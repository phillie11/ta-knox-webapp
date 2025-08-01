# projects/views.py
import logging
import requests
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from typing import List, Dict, Optional
from django.contrib import messages
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from .models import Project
from communications.models import EmailMonitorConfig
from .forms import ProjectForm

logger = logging.getLogger(__name__)

class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    context_object_name = 'projects'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().order_by('-created_at')

        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)

        return queryset

# Enhanced ProjectDetailView to include email monitoring config
class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    context_object_name = 'project'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_object()

        # Calculate invitation statistics
        invitation_count = project.invitations.count()
        accepted_count = project.invitations.filter(status='ACCEPTED').count()
        declined_count = project.invitations.filter(status='DECLINED').count()
        pending_count = project.invitations.filter(status='PENDING').count()

        # Get email monitoring configuration
        try:
            email_config = EmailMonitorConfig.objects.get(project=project)
        except EmailMonitorConfig.DoesNotExist:
            email_config = None

        # Add to context
        context.update({
            'invitation_count': invitation_count,
            'accepted_count': accepted_count,
            'declined_count': declined_count,
            'pending_count': pending_count,
            'email_monitor_config': email_config,
        })

        return context


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm

    def get_success_url(self):
        return reverse_lazy('projects:detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, "Project created successfully.")
        return super().form_valid(form)

class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm

    def get_success_url(self):
        return reverse_lazy('projects:detail', kwargs={'pk': self.object.pk})

    def get_initial(self):
        """Prepare initial data for the form, especially date fields"""
        initial = super().get_initial()

        if self.object:
            # Handle tender_deadline (datetime field)
            if self.object.tender_deadline:
                local_deadline = timezone.localtime(self.object.tender_deadline)
                initial['tender_deadline'] = local_deadline.strftime('%Y-%m-%dT%H:%M')

            # Handle all date fields
            date_fields = [
                'start_date', 'win_room_date', 'rfi_deadline',
                'site_visit_date', 'sc_deadline', 'mid_bid_review_date'
            ]

            for field_name in date_fields:
                value = getattr(self.object, field_name)
                if value:
                    # Format as YYYY-MM-DD for HTML date inputs
                    initial[field_name] = value.strftime('%Y-%m-%d')

        return initial

    def form_valid(self, form):
        # Get the tender deadline from the form
        tender_deadline = form.cleaned_data.get('tender_deadline')

        # If it's timezone naive, make it timezone aware using UTC
        if tender_deadline and timezone.is_naive(tender_deadline):
            form.instance.tender_deadline = timezone.make_aware(tender_deadline, timezone=timezone.utc)

        # Get the project's original status
        old_status = None
        if self.object:
            old_status = self.object.status

        # Get the new status
        new_status = form.cleaned_data.get('status')

        # Check if tender bid amount is provided for SUCCESSFUL or UNSUCCESSFUL
        if new_status in ['SUCCESSFUL', 'UNSUCCESSFUL']:
            tender_bid_amount = form.cleaned_data.get('tender_bid_amount')
            margin_percentage = form.cleaned_data.get('margin_percentage')

            if not tender_bid_amount:
                form.add_error('tender_bid_amount', 'Tender bid amount is required for successful/unsuccessful projects')
                return self.form_invalid(form)

            if not margin_percentage:
                form.add_error('margin_percentage', 'Margin percentage is required for successful/unsuccessful projects')
                return self.form_invalid(form)

        # Save the form
        response = super().form_valid(form)

        # Add a success message
        messages.success(self.request, "Project updated successfully.")

        # Additional logic based on status change
        if old_status != new_status:
            messages.info(self.request, f"Project status changed from {old_status} to {new_status}")

        return response

class ProjectDeleteView(LoginRequiredMixin, DeleteView):
    model = Project
    success_url = reverse_lazy('projects:list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Project deleted successfully.")
        return super().delete(request, *args, **kwargs)

# Add this to your projects/views.py to handle the SharePoint URL parsing

# Replace the existing parse_and_validate_sharepoint_url function in views.py
# and update the update_sharepoint_link function

@login_required
@require_POST
def update_sharepoint_link(request, pk):
    """Update SharePoint folder URL with flexible parsing and validation"""
    try:
        project = get_object_or_404(Project, pk=pk)

        sharepoint_url = request.POST.get('sharepoint_folder_url', '').strip()
        description = request.POST.get('sharepoint_link_description', 'ITT Documents').strip()

        if not sharepoint_url:
            messages.error(request, "SharePoint folder URL is required.")
            return redirect('projects:detail', pk=pk)

        # Parse and validate the SharePoint URL with flexible parser
        validation_result = parse_and_validate_sharepoint_url_flexible(sharepoint_url)

        if not validation_result['is_valid']:
            # Provide helpful error with debugging info
            error_msg = f"Invalid SharePoint URL: {validation_result['error']}"

            # Add helpful suggestions based on common issues
            if 'tenant' in validation_result['error'].lower():
                error_msg += "\n\nTip: Make sure you're copying the link from your TA Knox SharePoint account."
            elif 'shared documents' in validation_result['error'].lower():
                error_msg += "\n\nTip: The link should point to a folder within 'Shared Documents'."

            messages.error(request, error_msg)
            return redirect('projects:detail', pk=pk)

        # Update project with validated URL and parsed information
        project.sharepoint_folder_url = validation_result['clean_url']
        project.sharepoint_link_description = description or validation_result['suggested_description']

        project.save()

        logger.info(f"Updated SharePoint URL for project {project.id}")
        logger.info(f"Original URL: {sharepoint_url}")
        logger.info(f"Clean URL: {validation_result['clean_url']}")
        logger.info(f"Project detected: {validation_result['project_name']}")

        # Success message with parsed information
        success_msg = f"✅ SharePoint folder configured successfully!"

        if validation_result['project_name'] != "Unknown Project":
            success_msg += f"\nProject: {validation_result['project_name']}"

        if validation_result['folder_path']:
            success_msg += f"\nPath: {validation_result['path_display']}"

        success_msg += f"\nFormat detected: {validation_result['parsed_format']}"

        messages.success(request, success_msg)
        return redirect('projects:detail', pk=pk)

    except Exception as e:
        logger.exception(f"Error updating SharePoint link: {str(e)}")
        messages.error(request, f"Error updating SharePoint link: {str(e)}")
        return redirect('projects:detail', pk=pk)

@login_required
@require_POST
def remove_sharepoint_link(request, pk):
    """Remove SharePoint folder URL from project"""
    try:
        project = get_object_or_404(Project, pk=pk)

        # Clear SharePoint URL but keep description as empty string (not NULL)
        project.sharepoint_folder_url = None
        project.sharepoint_link_description = ""  # Empty string instead of None

        # Also clear the documents_link field if it exists
        if hasattr(project, 'sharepoint_documents_link'):
            project.sharepoint_documents_link = None

        project.save()

        messages.success(request, "SharePoint link removed successfully.")
        return JsonResponse({'success': True})

    except Exception as e:
        logger.exception(f"Error removing SharePoint link: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

def parse_and_validate_sharepoint_url_flexible(url):
    """
    More flexible SharePoint URL parser that handles various link formats
    INCLUDING SharePoint sharing links and Forms URLs with id parameters
    """
    try:
        from urllib.parse import urlparse, unquote, parse_qs
        import re

        print(f"🔍 FLEXIBLE PARSER CALLED with URL: {url}")

        # Parse the URL
        parsed = urlparse(url)

        print(f"DEBUG: Parsed netloc: {parsed.netloc}")
        print(f"DEBUG: Parsed path: {parsed.path}")
        print(f"DEBUG: Parsed query: {parsed.query}")

        # Basic validations
        if not parsed.scheme in ['http', 'https']:
            return {
                'is_valid': False,
                'error': 'URL must start with http:// or https://'
            }

        if 'sharepoint.com' not in parsed.netloc:
            return {
                'is_valid': False,
                'error': 'URL must be from sharepoint.com'
            }

        # More flexible tenant check
        tenant_patterns = ['taknox', 'ta-knox', 'taknoxltd']
        tenant_found = any(pattern in parsed.netloc.lower() for pattern in tenant_patterns)

        if not tenant_found:
            return {
                'is_valid': False,
                'error': f'URL must be from your SharePoint tenant. Found domain: {parsed.netloc}'
            }

        # Handle different SharePoint URL formats
        clean_url = None
        folder_path = ""
        site_name = "TAKNOXLTD"

        # NEW: Handle Forms/AllItems.aspx URLs with id parameter (YOUR FORMAT)
        if '/Forms/AllItems.aspx' in parsed.path and parsed.query:
            print("🎯 DEBUG: Detected Forms/AllItems.aspx URL with id parameter!")

            # Parse query parameters
            query_params = parse_qs(parsed.query)
            id_param = query_params.get('id', [None])[0]

            if id_param:
                print(f"DEBUG: Found id parameter: {id_param}")

                # Decode the id parameter
                decoded_path = unquote(id_param)
                print(f"DEBUG: Decoded path: {decoded_path}")

                # Extract folder path from the decoded id
                # Format: /sites/TAKNOXLTD/Shared Documents/Estimating/Live/Lidl Watford High Street/Estimating and Tender Information/ITT
                if '/Shared Documents/' in decoded_path:
                    shared_docs_index = decoded_path.find('/Shared Documents/')
                    folder_path = decoded_path[shared_docs_index + len('/Shared Documents/'):].strip('/')

                    # Build clean URL
                    clean_url = f"https://{parsed.netloc}/sites/{site_name}/Shared%20Documents"
                    if folder_path:
                        # Properly encode the folder path
                        encoded_path = folder_path.replace(' ', '%20').replace(',', '%2C')
                        clean_url += f"/{encoded_path}"

                    print(f"DEBUG: Extracted folder path: {folder_path}")
                    print(f"DEBUG: Built clean URL: {clean_url}")

        # Format 2: SharePoint sharing links /:f:/s/...
        elif parsed.path.startswith('/:f:/s/') or parsed.path.startswith('/:b:/s/'):
            print("🎯 DEBUG: Detected SharePoint sharing link format!")
            # Handle sharing links (your existing code)
            # ... existing sharing link code ...

        # Format 3: Direct Shared Documents URLs
        elif '/Shared Documents' in parsed.path or '/Shared%20Documents' in parsed.path:
            print("🎯 DEBUG: Detected direct Shared Documents URL!")
            # Handle direct URLs (your existing code)
            # ... existing direct URL code ...

        if not clean_url:
            print(f"❌ DEBUG: Could not build clean URL - no format matched")
            return {
                'is_valid': False,
                'error': f'Could not parse SharePoint URL format. Path: {parsed.path}, Query: {parsed.query}'
            }

        # Extract project information from folder path
        path_parts = [part for part in folder_path.split('/') if part] if folder_path else []

        if not path_parts and site_name:
            project_name = f"Project from {site_name}"
        else:
            project_name = path_parts[-1] if path_parts else "Unknown Project"

        is_estimating_live = len(path_parts) >= 2 and path_parts[0] == 'Estimating' and path_parts[1] == 'Live'
        suggested_description = f"ITT Documents"
        if project_name != "Unknown Project" and "Project from" not in project_name:
            suggested_description += f" - {project_name}"

        print(f"✅ SUCCESS: Final clean URL: {clean_url}")

        return {
            'is_valid': True,
            'clean_url': clean_url,
            'folder_path': folder_path,
            'project_name': project_name,
            'is_estimating_live': is_estimating_live,
            'folder_depth': len(path_parts),
            'suggested_description': suggested_description,
            'path_display': ' > '.join(path_parts) if path_parts else 'Root',
            'original_url': url,
            'parsed_format': 'forms_view' if '/Forms/AllItems.aspx' in parsed.path else 'sharing_link'
        }

    except Exception as e:
        print(f"❌ ERROR in URL parsing: {str(e)}")
        return {
            'is_valid': False,
            'error': f'Error parsing URL: {str(e)}'
        }

def test_debug():
    """Test the specific URL you're having trouble with"""
    test_url = "https://taknoxltd62.sharepoint.com/:f:/s/TAKNOXLTD/ErfL6606YTZEtCg4ESxnmCQBSkSJQCqRlvRvD4u58MOpoA?e=tdies3"

    print("=" * 50)
    print("TESTING YOUR URL:")
    print(test_url)
    print("=" * 50)

    result = parse_and_validate_sharepoint_url_flexible(test_url)

    print(f"Result: {result}")
    print("=" * 50)

# Test function specifically for your URL
def test_your_sharepoint_url():
    """Test function for the specific URL format you're using"""
    test_url = "https://taknoxltd62.sharepoint.com/:f:/s/TAKNOXLTD/ErfL6606YTZEtCg4ESxnmCQBSkSJQCqRlvRvD4u58MOpoA?e=tdies3"

    print("=== Testing Your SharePoint URL ===")
    print(f"URL: {test_url}")

    result = parse_and_validate_sharepoint_url_flexible(test_url)

    print(f"\nResult:")
    print(f"Valid: {result['is_valid']}")
    if result['is_valid']:
        print(f"Clean URL: {result['clean_url']}")
        print(f"Site Name: {result.get('site_name', 'N/A')}")
        print(f"Project: {result['project_name']}")
        print(f"Format: {result['parsed_format']}")
        print(f"Description: {result['suggested_description']}")
    else:
        print(f"Error: {result['error']}")

# Uncomment to test your specific URL:
# test_your_sharepoint_url()


# Optional: Add a test endpoint to validate URLs via AJAX
@login_required
def validate_sharepoint_url(request):
    """AJAX endpoint to validate SharePoint URLs in real-time"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    url = request.POST.get('url', '').strip()
    if not url:
        return JsonResponse({'error': 'URL required'}, status=400)

    result = parse_and_validate_sharepoint_url_flexible(url)
    return JsonResponse(result)


# Enhanced AI analysis trigger that uses the direct URL
@login_required
@require_POST
def trigger_ai_analysis_from_url(request, pk):
    """
    Trigger AI analysis directly from SharePoint URL without folder browsing
    """
    try:
        project = get_object_or_404(Project, pk=pk)

        if not project.sharepoint_folder_url:
            messages.error(request, "No SharePoint folder URL configured for this project.")
            return redirect('projects:detail', pk=pk)

        # Get analysis options
        recursive = request.POST.get('recursive', 'true').lower() == 'true'

        # Parse the SharePoint URL to get folder path
        validation_result = parse_and_validate_sharepoint_url_flexible(project.sharepoint_folder_url)

        if not validation_result['is_valid']:
            messages.error(request, f"Invalid SharePoint URL configuration: {validation_result['error']}")
            return redirect('projects:detail', pk=pk)

        # Initialize AI analyzer
        from tenders.services.ai_analysis import TenderAIAnalyzer
        analyzer = TenderAIAnalyzer()

        # Run analysis with direct URL approach
        logger.info(f"Starting AI analysis for project {project.name}")
        logger.info(f"SharePoint URL: {project.sharepoint_folder_url}")
        logger.info(f"Folder path: {validation_result['folder_path']}")
        logger.info(f"Recursive: {recursive}")

        if recursive:
            analysis = analyzer.analyze_project_sharepoint_folder_recursive(project, max_depth=4)
            scan_type = "all folders and subfolders (4 levels deep)"
        else:
            analysis = analyzer.analyze_project_sharepoint_folder(project)
            scan_type = "main folder only"

        # Count documents analyzed
        doc_count = len(analysis.documents_analyzed) if hasattr(analysis, 'documents_analyzed') else 0
        recommendation_count = analysis.recommendations.count() if hasattr(analysis, 'recommendations') else 0

        messages.success(
            request,
            f"🎉 AI analysis completed successfully!\n"
            f"Scanned: {scan_type}\n"
            f"Documents analyzed: {doc_count}\n"
            f"Recommendations generated: {recommendation_count}"
        )

        return redirect('tenders:analysis', project_id=project.id)

    except Exception as e:
        logger.exception(f"Error in AI analysis: {str(e)}")
        messages.error(request, f"Error during AI analysis: {str(e)}")
        return redirect('projects:detail', pk=pk)

@login_required
def debug_sharepoint_endpoint(request):
    """Simple test endpoint"""
    return JsonResponse({
        'success': True,
        'message': 'Endpoint is working!',
        'method': request.method,
        'path': request.path
    })

@login_required
def get_sharepoint_folders_minimal(request):
    """Minimal test with mock data"""
    try:
        test_folders = [
            {
                'id': 'test-1',
                'name': 'Arsenal Physio Room',
                'full_path': 'Arsenal Physio Room',
                'url': 'https://taknoxltd62.sharepoint.com/test1',
                'depth': 0
            },
            {
                'id': 'test-2',
                'name': 'Commercial Management',
                'full_path': 'Arsenal Physio Room > Commercial Management',
                'url': 'https://taknoxltd62.sharepoint.com/test2',
                'depth': 1
            },
            {
                'id': 'test-3',
                'name': 'Flat Iron, Bristol',
                'full_path': 'Flat Iron, Bristol',
                'url': 'https://taknoxltd62.sharepoint.com/test3',
                'depth': 0
            }
        ]

        return JsonResponse({
            'success': True,
            'folders': test_folders,
            'total_count': len(test_folders),
            'source': 'minimal_test'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


# Also add a test endpoint for debugging
@login_required
def test_sharepoint_connection(request):
    """Test SharePoint connection for debugging"""
    try:
        from .services import SharePointService

        sharepoint_service = SharePointService()
        test_result = sharepoint_service.test_connection()

        return JsonResponse({
            'success': test_result['success'],
            'result': test_result
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@require_POST
def get_sharepoint_folders(request, pk):
    """Update SharePoint folder for a project - FIXED to update both fields"""
    try:
        project = get_object_or_404(Project, pk=pk)

        folder_url = request.POST.get('folder_url')
        description = request.POST.get('description', 'ITT Documents')

        if not folder_url:
            return JsonResponse({
                'success': False,
                'error': 'Folder URL is required'
            })

        # FIXED: Update both field names to ensure compatibility
        # 1. sharepoint_documents_link - used by the template and forms
        project.sharepoint_documents_link = folder_url
        project.sharepoint_link_description = description

        # 2. sharepoint_folder_url - used by AI analysis
        # Check if this field exists on the model
        if hasattr(project, 'sharepoint_folder_url'):
            project.sharepoint_folder_url = folder_url
            save_fields = ['sharepoint_documents_link', 'sharepoint_link_description', 'sharepoint_folder_url']
        else:
            save_fields = ['sharepoint_documents_link', 'sharepoint_link_description']

        project.save(update_fields=save_fields)

        logger.info(f"Updated SharePoint folder for project {project.id}")
        logger.info(f"  URL: {folder_url}")
        logger.info(f"  Description: {description}")
        logger.info(f"  Updated fields: {save_fields}")

        return JsonResponse({
            'success': True,
            'message': 'SharePoint folder configured successfully',
            'url': folder_url,
            'description': description
        })

    except Exception as e:
        logger.exception(f"Error updating SharePoint folder: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def get_mail_folders(request):
    """Get mail folders for dropdown (existing functionality)"""
    try:
        logger.info("Getting mail folders")
        from communications.services import OutlookEmailService  # Adjust import as needed

        email_service = OutlookEmailService()
        folders = email_service.get_folders_for_dropdown()

        logger.info(f"Retrieved {len(folders)} mail folders")

        return JsonResponse({
            'success': True,
            'folders': folders
        })
    except Exception as e:
        logger.exception(f"Error fetching mail folders: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@require_POST
def update_email_folder(request, pk):
    """Update email monitoring folder for a project"""
    try:
        project = get_object_or_404(Project, pk=pk)

        folder_id = request.POST.get('folder_id')
        folder_name = request.POST.get('folder_name')
        is_active = request.POST.get('is_active') == 'true'

        if not folder_id or not folder_name:
            return JsonResponse({
                'success': False,
                'error': 'Folder ID and name are required'
            })

        # Get or create email monitor configuration
        config, created = EmailMonitorConfig.objects.get_or_create(
            project=project,
            defaults={
                'folder_name': folder_name,
                'folder_id': folder_id,
                'is_active': is_active
            }
        )

        if not created:
            # Update existing configuration
            config.folder_name = folder_name
            config.folder_id = folder_id
            config.is_active = is_active
            config.save()

        action = "created" if created else "updated"
        logger.info(f"Email monitoring {action} for project {project.id}: {folder_name}")

        return JsonResponse({
            'success': True,
            'message': f'Email monitoring {action} successfully for folder "{folder_name}"'
        })

    except Exception as e:
        logger.exception(f"Error updating email folder: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def update_sharepoint_folder(request, pk):
    """Update the SharePoint folder URL for a project"""
    project = get_object_or_404(Project, pk=pk)

    if request.method == 'POST':
        # FIXED: Use correct field name
        sharepoint_link = request.POST.get('sharepoint_folder_url', '').strip()
        link_description = request.POST.get('sharepoint_link_description', '').strip()

        # Basic validation
        if sharepoint_link:
            # Validate it's a proper SharePoint URL
            if not any(domain in sharepoint_link.lower() for domain in ['sharepoint.com', 'sharepoint.']):
                messages.error(request, "Please enter a valid SharePoint URL")
                return redirect('projects:detail', pk=pk)

        # Update the project with correct field name
        project.sharepoint_documents_link = sharepoint_link if sharepoint_link else None
        project.sharepoint_link_description = link_description if link_description else 'ITT Documents'
        project.save(update_fields=['sharepoint_documents_link', 'sharepoint_link_description'])

        if sharepoint_link:
            messages.success(request, "SharePoint documents folder updated successfully.")
        else:
            messages.success(request, "SharePoint documents folder link removed.")

    return redirect('projects:detail', pk=pk)
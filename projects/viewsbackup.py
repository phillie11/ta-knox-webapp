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

@login_required
def get_sharepoint_folders(request):
    """Get SharePoint folders - Optimized search for ITT folders"""
    try:
        logger.info("=== SHAREPOINT FOLDER FETCH - ITT FOCUSED ===")

        from .services import SharePointService
        sharepoint_service = SharePointService()

        if not sharepoint_service.access_token:
            return JsonResponse({
                'success': False,
                'error': 'SharePoint authentication failed'
            })

        # Test connection and get basic info
        test_result = sharepoint_service.test_connection()
        if not test_result.get('success'):
            return JsonResponse({
                'success': False,
                'error': f"Connection test failed: {test_result.get('error')}"
            })

        site_id = test_result.get('site_id')
        drive_id = test_result.get('drive_id')

        if not site_id or not drive_id:
            return JsonResponse({
                'success': False,
                'error': 'Could not get site_id or drive_id'
            })

        logger.info(f"✅ Connected - Site: {site_id}")

        # ITT-FOCUSED SEARCH STRATEGY
        all_folders = []
        itt_folders_found = []

        # Step 1: Get main project folders (limited for performance)
        main_projects = get_folders_at_path_limited(sharepoint_service, site_id, drive_id, "Estimating/Live", limit=15)
        logger.info(f"Found {len(main_projects)} main project folders")

        for i, project in enumerate(main_projects):
            # Add main project folder (Level 0)
            project_folder = {
                'id': project['id'],
                'name': project['name'],
                'full_path': project['name'],
                'url': project.get('webUrl', ''),
                'depth': 0
            }
            all_folders.append(project_folder)

            # Step 2: Look for key folders, prioritizing those containing "ITT"
            project_path = f"Estimating/Live/{project['name']}"
            level1_folders = get_folders_at_path_limited(sharepoint_service, site_id, drive_id, project_path, limit=10)

            # Separate ITT-related folders and other important folders
            itt_related = []
            other_important = []

            for level1 in level1_folders:
                folder_name = level1['name'].upper()

                if 'ITT' in folder_name:
                    itt_related.append(level1)
                elif folder_name in ['ESTIMATING AND TENDER INFORMATION', 'CONTRACT', 'DESIGN', 'COMMERCIAL MANAGEMENT']:
                    other_important.append(level1)

            # Process ITT folders first (with deeper search)
            for level1 in itt_related:
                level1_folder = {
                    'id': level1['id'],
                    'name': level1['name'],
                    'full_path': f"{project['name']} > {level1['name']} ⭐",  # Star for ITT folders
                    'url': level1.get('webUrl', ''),
                    'depth': 1
                }
                all_folders.append(level1_folder)
                itt_folders_found.append(level1_folder)

                # For ITT folders, go deeper to find specific ITT subfolders
                level1_path = f"Estimating/Live/{project['name']}/{level1['name']}"
                level2_folders = get_folders_at_path_limited(sharepoint_service, site_id, drive_id, level1_path, limit=8)

                for level2 in level2_folders:
                    level2_name = level2['name'].upper()
                    # Look for specific ITT-related subfolders
                    if any(keyword in level2_name for keyword in ['ITT', 'TENDER', 'BID', 'DOCUMENT', 'SUBMISSION']):
                        level2_folder = {
                            'id': level2['id'],
                            'name': level2['name'],
                            'full_path': f"{project['name']} > {level1['name']} > {level2['name']} ⭐⭐",
                            'url': level2.get('webUrl', ''),
                            'depth': 2
                        }
                        all_folders.append(level2_folder)
                        itt_folders_found.append(level2_folder)

                        # Go one level deeper for ITT folders
                        level2_path = f"Estimating/Live/{project['name']}/{level1['name']}/{level2['name']}"
                        level3_folders = get_folders_at_path_limited(sharepoint_service, site_id, drive_id, level2_path, limit=5)

                        for level3 in level3_folders:
                            level3_folder = {
                                'id': level3['id'],
                                'name': level3['name'],
                                'full_path': f"{project['name']} > {level1['name']} > {level2['name']} > {level3['name']}",
                                'url': level3.get('webUrl', ''),
                                'depth': 3
                            }
                            all_folders.append(level3_folder)

            # Process other important folders (limited depth)
            for level1 in other_important[:3]:  # Limit to first 3 important folders
                level1_folder = {
                    'id': level1['id'],
                    'name': level1['name'],
                    'full_path': f"{project['name']} > {level1['name']}",
                    'url': level1.get('webUrl', ''),
                    'depth': 1
                }
                all_folders.append(level1_folder)

                # For "Estimating and Tender Information", look for ITT subfolders
                if 'ESTIMATING' in level1['name'].upper() and 'TENDER' in level1['name'].upper():
                    level1_path = f"Estimating/Live/{project['name']}/{level1['name']}"
                    level2_folders = get_folders_at_path_limited(sharepoint_service, site_id, drive_id, level1_path, limit=5)

                    for level2 in level2_folders:
                        level2_name = level2['name'].upper()
                        if 'ITT' in level2_name or any(keyword in level2_name for keyword in ['TENDER', 'BID', 'SUBMISSION']):
                            level2_folder = {
                                'id': level2['id'],
                                'name': level2['name'],
                                'full_path': f"{project['name']} > {level1['name']} > {level2['name']} ⭐",
                                'url': level2.get('webUrl', ''),
                                'depth': 2
                            }
                            all_folders.append(level2_folder)
                            itt_folders_found.append(level2_folder)

            # Stop after first 10 projects to prevent timeout
            if i >= 9:
                logger.info("Limited to first 10 projects to prevent timeout")
                break

        # Sort folders - ITT folders first, then by project and depth
        all_folders.sort(key=lambda x: (
            0 if '⭐' in x['full_path'] else 1,  # ITT folders first
            x['full_path'].replace('⭐', ''),     # Then alphabetically
            x['depth']                           # Then by depth
        ))

        logger.info(f"Total folders collected: {len(all_folders)}")
        logger.info(f"ITT-specific folders found: {len(itt_folders_found)}")

        # Log ITT folders found for debugging
        for itt_folder in itt_folders_found[:5]:
            logger.info(f"⭐ ITT folder: {itt_folder['full_path']}")

        return JsonResponse({
            'success': True,
            'folders': all_folders,
            'total_count': len(all_folders),
            'source': 'itt_focused_search',
            'projects_found': len([f for f in all_folders if f['depth'] == 0]),
            'itt_folders_found': len(itt_folders_found),
            'note': 'ITT folders prioritized and marked with ⭐'
        })

    except Exception as e:
        logger.exception(f"Error getting SharePoint folders: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f"Error: {str(e)}"
        })


def get_folders_at_path_limited(sharepoint_service, site_id, drive_id, folder_path, limit=10):
    """Get folders at a specific path with a limit and timeout protection"""
    try:
        import requests

        if folder_path:
            encoded_path = requests.utils.quote(folder_path, safe='')
            url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root:/{encoded_path}:/children"
        else:
            url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root/children"

        headers = {
            'Authorization': f'Bearer {sharepoint_service.access_token}',
            'Accept': 'application/json'
        }

        params = {
            '$filter': "folder ne null",
            '$select': 'id,name,folder,webUrl',
            '$top': limit,  # Limit results to prevent timeout
            '$orderby': 'name asc'  # Order by name for consistency
        }

        logger.info(f"API call: {folder_path} (limit: {limit})")
        response = requests.get(url, headers=headers, params=params, timeout=8)  # 8 second timeout

        if response.status_code == 200:
            items = response.json().get('value', [])
            folders = []

            for item in items:
                if 'folder' in item:
                    folders.append({
                        'id': item.get('id', ''),
                        'name': item.get('name', ''),
                        'webUrl': item.get('webUrl', ''),
                        'url': item.get('webUrl', '')
                    })

            logger.info(f"Found {len(folders)} folders at '{folder_path}'")
            return folders

        elif response.status_code == 404:
            logger.info(f"Path '{folder_path}' not found (404)")
            return []
        else:
            logger.error(f"API error {response.status_code}: {response.text}")
            return []

    except requests.Timeout:
        logger.error(f"Timeout getting folders from '{folder_path}' - skipping")
        return []
    except Exception as e:
        logger.error(f"Error getting folders from '{folder_path}': {str(e)}")
        return []


# DIRECT ITT SEARCH FUNCTION
def search_for_itt_folders_direct(sharepoint_service, site_id, drive_id, project_name):
    """Direct search for ITT folders in a specific project"""
    try:
        common_itt_paths = [
            f"Estimating/Live/{project_name}/ITT",
            f"Estimating/Live/{project_name}/ITT Documents",
            f"Estimating/Live/{project_name}/Estimating and Tender Information/ITT",
            f"Estimating/Live/{project_name}/Contract/ITT",
            f"Estimating/Live/{project_name}/Design/ITT"
        ]

        itt_folders = []

        for path in common_itt_paths:
            try:
                folders = get_folders_at_path_limited(sharepoint_service, site_id, drive_id, path, limit=5)
                for folder in folders:
                    folder['search_path'] = path
                    itt_folders.append(folder)
            except:
                continue  # Skip if path doesn't exist

        return itt_folders

    except Exception as e:
        logger.error(f"Error in direct ITT search for {project_name}: {str(e)}")
        return []


# ULTRA-FAST VERSION - Just returns folders with ITT in the name
@login_required
def get_sharepoint_folders_simple_working(request):
    """Ultra-fast version - returns only folders containing 'ITT'"""
    try:
        from .services import SharePointService
        sharepoint_service = SharePointService()

        if not sharepoint_service.access_token:
            return JsonResponse({'success': False, 'error': 'No access token'})

        test_result = sharepoint_service.test_connection()
        if not test_result.get('success'):
            return JsonResponse({'success': False, 'error': 'Connection failed'})

        site_id = test_result.get('site_id')
        drive_id = test_result.get('drive_id')

        folders = []

        # Get main projects (limited)
        main_projects = get_folders_at_path_limited(sharepoint_service, site_id, drive_id, "Estimating/Live", limit=10)

        for project in main_projects:
            # Add main project
            folders.append({
                'id': project['id'],
                'name': project['name'],
                'full_path': project['name'],
                'url': project['webUrl'],
                'depth': 0
            })

            # Look specifically for ITT-related folders
            project_path = f"Estimating/Live/{project['name']}"
            subfolders = get_folders_at_path_limited(sharepoint_service, site_id, drive_id, project_path, limit=8)

            # Filter for ITT folders only
            for subfolder in subfolders:
                if 'ITT' in subfolder['name'].upper() or 'TENDER' in subfolder['name'].upper():
                    folders.append({
                        'id': subfolder['id'],
                        'name': f"{subfolder['name']} ⭐",
                        'full_path': f"{project['name']} > {subfolder['name']} ⭐",
                        'url': subfolder['webUrl'],
                        'depth': 1
                    })

        return JsonResponse({
            'success': True,
            'folders': folders,
            'total_count': len(folders),
            'source': 'itt_only_search',
            'note': 'Only ITT and Tender related folders shown'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ===== DEBUGGING FUNCTIONS =====

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
def update_sharepoint_folder(request, pk):
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
def update_sharepoint_link(request, pk):
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
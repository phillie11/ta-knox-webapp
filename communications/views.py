# communications/views.py
import logging
import json
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from projects.models import Project
from tenders.models import TenderInvitation
from subcontractors.models import Subcontractor
from .models import EmailMonitorConfig, EmailLog
from .services import OutlookEmailService
logger = logging.getLogger(__name__)

@login_required
def configure_email_monitoring(request, project_id):
    """Configure email monitoring for a project"""
    project = get_object_or_404(Project, id=project_id)

    if request.method == 'POST':
        folder_name = request.POST.get('folder')
        folder_id = request.POST.get('folder_id')
        is_active = request.POST.get('is_active') == 'on'

        if not folder_name:
            messages.error(request, "Folder name is required")
            return redirect('projects:detail', pk=project_id)

        # Get or create the config
        config, created = EmailMonitorConfig.objects.get_or_create(
            project=project,
            defaults={
                'folder_name': folder_name,
                'folder_id': folder_id,
                'is_active': is_active
            }
        )

        if not created:
            config.folder_name = folder_name
            config.folder_id = folder_id
            config.is_active = is_active
            config.save()

        messages.success(request, "Email monitoring configuration saved")

    return redirect('projects:detail', pk=project_id)

@login_required
def get_mail_folders(request):
    """Get mail folders for dropdown"""
    try:
        logger.info("Getting mail folders")
        email_service = OutlookEmailService()
        folders = email_service.get_folders_for_dropdown()

        logger.info(f"Retrieved {len(folders)} folders")

        return JsonResponse({
            'success': True,
            'folders': folders
        })
    except Exception as e:
        logger.exception(f"Error fetching mail folders: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def run_email_check_now(request, project_id):
    """Run the simplified email check for a project"""
    project = get_object_or_404(Project, id=project_id)

    try:
        # Get the email monitoring config
        config = EmailMonitorConfig.objects.filter(project=project).first()

        if not config:
            messages.error(request, "Email monitoring not configured for this project")
            return redirect('projects:detail', pk=project_id)

        if not config.folder_id:
            messages.error(request, "No folder selected for email monitoring")
            return redirect('projects:detail', pk=project_id)

        # Run the simplified email check
        email_service = OutlookEmailService()
        emails_processed, tenders_matched = email_service.check_project_folder_simple(config)

        # Show results
        if tenders_matched > 0:
            messages.success(
                request,
                f"✅ Email check complete: Found {tenders_matched} tender returns from {emails_processed} emails!"
            )
        elif emails_processed > 0:
            messages.info(
                request,
                f"Email check complete: Checked {emails_processed} emails, no new tender returns found"
            )
        else:
            messages.warning(request, "No emails found to check")

        # Redirect back to where they came from
        if request.GET.get('source') == 'tracking':
            return redirect(f"/tenders/project/{project_id}/tracking/?email_check=success")
        else:
            return redirect('projects:detail', pk=project_id)

    except Exception as e:
        logger.exception(f"Error running email check: {str(e)}")
        messages.error(request, f"Error checking emails: {str(e)}")

        # Redirect with error
        if request.GET.get('source') == 'tracking':
            return redirect(f"/tenders/project/{project_id}/tracking/?email_check=failure")
        else:
            return redirect('projects:detail', pk=project_id)

@login_required
@csrf_exempt
def manual_tender_return(request):
    """Manually record a tender return"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Only POST method is allowed'
        }, status=405)

    try:
        data = json.loads(request.body)
        project_id = data.get('project_id')
        subcontractor_id = data.get('subcontractor_id')
        sender_email = data.get('sender_email')
        notes = data.get('notes', '')

        if not project_id or not subcontractor_id:
            return JsonResponse({
                'success': False,
                'error': 'Missing required parameters'
            }, status=400)

        # Get project and subcontractor
        try:
            project = Project.objects.get(id=project_id)
            subcontractor = Subcontractor.objects.get(id=subcontractor_id)
        except (Project.DoesNotExist, Subcontractor.DoesNotExist) as e:
            return JsonResponse({
                'success': False,
                'error': f'Object not found: {str(e)}'
            }, status=404)

        # Get or create invitation
        invitation, created = TenderInvitation.objects.get_or_create(
            project=project,
            subcontractor=subcontractor,
            defaults={
                'status': 'ACCEPTED',
                'response_date': timezone.now()
            }
        )

        # Mark as returned
        invitation.tender_returned = True
        invitation.tender_returned_at = timezone.now()
        invitation.tender_attachments = {
            'sender': sender_email or subcontractor.email,
            'matched_by': 'manual_entry',
            'processed_at': timezone.now().isoformat(),
            'processed_by': request.user.username,
            'notes': notes
        }
        invitation.save()

        logger.info(f"Manually recorded tender return: {subcontractor.company} on {project.name}")

        return JsonResponse({
            'success': True,
            'message': f'Tender return recorded for {subcontractor.company}'
        })

    except Exception as e:
        logger.exception(f"Error in manual tender return: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
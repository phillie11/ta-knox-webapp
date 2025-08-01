import logging
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.urls import reverse
from django.core.signing import Signer
from django.conf import settings
from tenders.models import Project, TenderInvitation
from communications.models import EmailLog
from communications.services import OutlookEmailService

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Send automatic reminders for upcoming subcontractor deadlines'

    def handle(self, *args, **options):
        self.stdout.write("Starting to send deadline reminders...")

        # Get current time
        now = timezone.now()

        # Get projects with active tenders (deadline in the future)
        active_projects = Project.objects.filter(
            sc_deadline__gt=now
        )

        try:
            email_service = OutlookEmailService()

            for project in active_projects:
                self.stdout.write(f"Processing project: {project.name}")

                # Calculate days remaining to deadline
                days_to_deadline = (project.sc_deadline - now).days
                hours_to_deadline = int((project.sc_deadline - now).total_seconds() / 3600)

                # Get pending invitations for this project
                pending_invitations = TenderInvitation.objects.filter(
                    project=project,
                    status='PENDING'
                )

                # Get will tender invitations for this project
                will_tender_invitations = TenderInvitation.objects.filter(
                    project=project,
                    status='ACCEPTED',
                    tender_returned=False
                )

                # Combine both types
                all_invitations = list(pending_invitations) + list(will_tender_invitations)

                self.stdout.write(f"  Found {pending_invitations.count()} pending invitations")

                # Skip if no pending invitations
                if not pending_invitations.exists():
                    continue

                # Determine what reminder to send
                reminder_type = None
                if days_to_deadline == 3:
                    reminder_type = "3 days"
                elif days_to_deadline == 2:
                    reminder_type = "2 days"
                elif days_to_deadline == 1:
                    reminder_type = "1 day"
                elif days_to_deadline == 0 and hours_to_deadline <= 12:
                    reminder_type = "today"

                if not reminder_type:
                    self.stdout.write(f"  No reminder needed ({days_to_deadline} days to deadline)")
                    continue

                self.stdout.write(f"  Sending {reminder_type} reminders")

                # Get deadline information
                for invitation in all_invitations:
                    subcontractor = invitation.subcontractor

                    # Determine reminder type based on invitation status
                    if invitation.status == 'PENDING':
                        reminder_type_suffix = "response required"
                        email_subject_prefix = "REMINDER: Tender Response Required"
                    else:  # ACCEPTED (will tender)
                        reminder_type_suffix = "tender submission"
                        email_subject_prefix = "TENDER DEADLINE REMINDER"

                    # Skip if already sent this type of reminder today
                    already_sent = EmailLog.objects.filter(
                        project=project,
                        subcontractor=subcontractor,
                        email_type='REMINDER',
                        subject__contains=reminder_type,
                        sent_at__date=now.date()
                    ).exists()

                    if already_sent:
                        self.stdout.write(f"  Already sent {reminder_type} reminder to {subcontractor.company}")
                        continue

                    try:
                        # Generate tracking token
                        token = self._generate_tracking_token(invitation.id)

                        # Generate response URL
                        response_url = f"{settings.BASE_URL}{reverse('tenders:response', kwargs={'token': token})}"

                        # For tracking opened emails
                        tracking_url = f"{settings.BASE_URL}{reverse('tenders:track_email', kwargs={'token': token})}"

                        deadline_str = project.sc_deadline.strftime('%d/%m/%Y at %H:%M')

                        # Create reminder message based on invitation status
                        if invitation.status == 'PENDING':
                            if reminder_type == "today":
                                subject = f"URGENT: Tender for {project.name} is due TODAY"
                                message = f"""
                                <p>Dear {subcontractor.first_name or 'Sir/Madam'},</p>

                                <p><strong>This is an urgent reminder that the tender for {project.name} is due TODAY, {deadline_str}.</strong></p>

                                <p>If you plan to submit a tender, please ensure it is submitted by the deadline.</p>

                                <p>Please let us know if you will be submitting a tender by clicking one of the buttons below:</p>

                                <img src="{tracking_url}" width="1" height="1" style="display:none;" />
                                """
                            else:
                                subject = f"REMINDER: Tender for {project.name} is due in {reminder_type}"
                                message = f"""
                                <p>Dear {subcontractor.first_name or 'Sir/Madam'},</p>

                                <p>This is a reminder that the tender for {project.name} is due in {reminder_type}, on {deadline_str}.</p>

                                <p>If you plan to submit a tender, please ensure it is submitted by the deadline.</p>

                                <p>Please let us know if you will be submitting a tender by clicking one of the buttons below:</p>

                                <img src="{tracking_url}" width="1" height="1" style="display:none;" />
                                """
                        else:  # ACCEPTED (will tender)
                            if reminder_type == "today":
                                subject = f"URGENT: Tender submission for {project.name} is due TODAY"
                                message = f"""
                                <p>Dear {subcontractor.first_name or 'Sir/Madam'},</p>

                                <p>You have confirmed that you will tender for <strong>{project.name}</strong>.</p>

                                <p><strong>This is an urgent reminder that your tender submission is due TODAY, {deadline_str}.</strong></p>

                                <p>Please ensure your tender submission is returned by the deadline.</p>

                                <img src="{tracking_url}" width="1" height="1" style="display:none;" />
                                """
                            else:
                                subject = f"TENDER DEADLINE REMINDER: {project.name} - due in {reminder_type}"
                                message = f"""
                                <p>Dear {subcontractor.first_name or 'Sir/Madam'},</p>

                                <p>You have confirmed that you will tender for <strong>{project.name}</strong>.</p>

                                <p>This is a reminder that your tender submission is due in {reminder_type}, on {deadline_str}.</p>

                                <p>Please ensure your tender submission is returned by the deadline.</p>

                                <img src="{tracking_url}" width="1" height="1" style="display:none;" />
                                """

                        # Add response buttons only for PENDING invitations
                        if invitation.status == 'PENDING':
                            message += f"""
                            <div style="margin: 30px 0; text-align: center;">
                                <p>Please confirm your intention by clicking one of the buttons below:</p>
                                <div style="margin: 20px 0;">
                                    <a href="{response_url}?response=accept" style="display: inline-block; padding: 12px 24px; background-color: #28a745; color: white; text-decoration: none; border-radius: 5px; margin: 0 10px;">
                                        ✓ I Will Tender
                                    </a>
                                    <a href="{response_url}?response=decline" style="display: inline-block; padding: 12px 24px; background-color: #dc3545; color: white; text-decoration: none; border-radius: 5px; margin: 0 10px;">
                                        ✗ I Will Not Tender
                                    </a>
                                </div>
                            </div>
                            """

                        # Send the email
                        email_service.send_email(
                            to_email=subcontractor.email,
                            subject=subject,
                            body=message,
                            reply_url=response_url if invitation.status == 'PENDING' else None
                        )

                        # Log the email
                        EmailLog.objects.create(
                            project=project,
                            subcontractor=subcontractor,
                            email_type='REMINDER',
                            subject=subject,
                            body=message
                        )

                        self.stdout.write(f"  Sent {reminder_type} reminder to {subcontractor.company} (status: {invitation.status})")

                    except Exception as e:
                        logger.error(f"Failed to send reminder to {subcontractor.email}: {str(e)}")
                        self.stdout.write(self.style.ERROR(f"  Failed to send reminder to {subcontractor.company}: {str(e)}"))

    def _generate_tracking_token(self, invitation_id):
        signer = Signer()
        return signer.sign(str(invitation_id))
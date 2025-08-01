# communications/management/commands/check_tender_returns_enhanced.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from communications.services import OutlookEmailService
from communications.models import EmailMonitorConfig
from tenders.models import TenderInvitation
from subcontractors.models import Subcontractor
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Enhanced email monitoring for tender returns with detailed debugging'

    def add_arguments(self, parser):
        parser.add_argument(
            '--project-id',
            type=int,
            help='Check only a specific project by ID',
        )
        parser.add_argument(
            '--test-folder',
            action='store_true',
            help='Test folder access for all configured projects',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output',
        )
        parser.add_argument(
            '--days-back',
            type=int,
            default=7,
            help='Number of days back to check emails (default: 7)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without making changes',
        )

    def handle(self, *args, **options):
        verbosity = options.get('verbosity', 1)
        verbose = options.get('verbose', False) or verbosity > 1
        project_id = options.get('project_id')
        test_folder = options.get('test_folder', False)
        days_back = options.get('days_back', 7)
        dry_run = options.get('dry_run', False)

        if verbose:
            logging.getLogger('communications').setLevel(logging.DEBUG)

        self.stdout.write("🔍 Enhanced Email Monitoring for Tender Returns")
        self.stdout.write("=" * 50)

        # Initialize email service
        try:
            email_service = OutlookEmailService()
            self.stdout.write(self.style.SUCCESS("✅ Email service initialized successfully"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Failed to initialize email service: {str(e)}"))
            return

        # Get configurations to check
        if project_id:
            configs = EmailMonitorConfig.objects.filter(project_id=project_id, is_active=True)
            if not configs.exists():
                self.stdout.write(self.style.ERROR(f"❌ No active email monitoring found for project ID {project_id}"))
                return
        else:
            configs = EmailMonitorConfig.objects.filter(is_active=True)

        if not configs.exists():
            self.stdout.write(self.style.ERROR("❌ No active email monitoring configurations found"))
            return

        self.stdout.write(f"📁 Found {configs.count()} active email monitoring configuration(s)")

        # Test folder access if requested
        if test_folder:
            self.stdout.write("\n🧪 Testing folder access...")
            for config in configs:
                success, message = email_service.test_folder_access(config.folder_id)
                if success:
                    self.stdout.write(self.style.SUCCESS(f"✅ {config.project.name}: {message}"))
                else:
                    self.stdout.write(self.style.ERROR(f"❌ {config.project.name}: {message}"))
            return

        # Process each configuration
        total_processed = 0
        total_matched = 0

        for config in configs:
            self.stdout.write(f"\n📧 Processing project: {config.project.name}")
            self.stdout.write(f"   Folder: {config.folder_name} (ID: {config.folder_id})")
            
            if config.last_check_time:
                self.stdout.write(f"   Last checked: {config.last_check_time.strftime('%d/%m/%Y %H:%M')}")
            else:
                self.stdout.write(f"   Never checked before - will check last {days_back} days")

            try:
                if dry_run:
                    processed, matched = self._dry_run_process_folder(email_service, config, days_back, verbose)
                else:
                    processed, matched = email_service.process_project_folder(config)
                
                total_processed += processed
                total_matched += matched

                self.stdout.write(f"   📊 Results: {processed} emails processed, {matched} tenders matched")

                if matched > 0:
                    self.stdout.write(self.style.SUCCESS(f"   ✅ {matched} new tender return(s) detected!"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   ❌ Error: {str(e)}"))
                if verbose:
                    import traceback
                    self.stdout.write(traceback.format_exc())

        # Summary
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(f"📈 SUMMARY:")
        self.stdout.write(f"   Total emails processed: {total_processed}")
        self.stdout.write(f"   Total tenders matched: {total_matched}")

        if total_matched > 0:
            self.stdout.write(self.style.SUCCESS(f"🎉 {total_matched} tender return(s) successfully processed!"))
        else:
            self.stdout.write("ℹ️  No new tender returns found")

        # Show current invitation status
        if not dry_run:
            self._show_invitation_summary(configs)

    def _dry_run_process_folder(self, email_service, config, days_back, verbose):
        """Simulate processing a folder without making changes"""
        from tenders.models import TenderInvitation
        
        self.stdout.write(f"   🔍 DRY RUN - Simulating email check...")

        # Set time range
        current_time = timezone.now()
        if config.last_check_time:
            start_time = config.last_check_time
        else:
            start_time = current_time - timedelta(days=days_back)

        start_time_utc = start_time.astimezone(timezone.utc)
        filter_query = f"receivedDateTime ge {start_time_utc.strftime('%Y-%m-%dT%H:%M:%S.%fZ')}"

        try:
            headers = {
                'Authorization': f'Bearer {email_service.token}',
                'Content-Type': 'application/json'
            }

            endpoint = f'https://graph.microsoft.com/v1.0/users/{email_service.user_email}/mailFolders/{config.folder_id}/messages'
            
            params = {
                '$filter': filter_query,
                '$orderby': 'receivedDateTime desc',
                '$top': 50,
                '$select': 'id,subject,from,receivedDateTime,hasAttachments'
            }

            response = requests.get(endpoint, headers=headers, params=params)

            if response.status_code != 200:
                self.stdout.write(f"   ❌ API Error: {response.status_code} - {response.text}")
                return 0, 0

            messages_data = response.json().get('value', [])
            processed_emails = len(messages_data)
            potential_matches = 0

            self.stdout.write(f"   📬 Found {processed_emails} emails since {start_time_utc.strftime('%d/%m/%Y %H:%M')}")

            if verbose and processed_emails > 0:
                self.stdout.write(f"   📝 Email details:")

            for message in messages_data:
                subject = message.get('subject', 'No Subject')
                sender_info = message.get('from', {})
                from_address = ''
                
                if sender_info and sender_info.get('emailAddress'):
                    from_address = sender_info['emailAddress'].get('address', '')

                if verbose:
                    received_date = message.get('receivedDateTime', '')
                    has_attachments = message.get('hasAttachments', False)
                    self.stdout.write(f"     • From: {from_address}")
                    self.stdout.write(f"       Subject: {subject}")
                    self.stdout.write(f"       Date: {received_date}")
                    self.stdout.write(f"       Attachments: {'Yes' if has_attachments else 'No'}")

                if from_address:
                    # Try to find matching subcontractor
                    matched_subcontractor = email_service._find_matching_subcontractor(
                        from_address, subject, '', config.project
                    )

                    if matched_subcontractor:
                        # Check if there's an invitation
                        try:
                            invitation = TenderInvitation.objects.get(
                                project=config.project,
                                subcontractor=matched_subcontractor
                            )

                            if not invitation.tender_returned:
                                potential_matches += 1
                                if verbose:
                                    self.stdout.write(f"       🎯 WOULD MATCH: {matched_subcontractor.company}")
                            else:
                                if verbose:
                                    self.stdout.write(f"       ⏭️  Already returned: {matched_subcontractor.company}")
                        except TenderInvitation.DoesNotExist:
                            if verbose:
                                self.stdout.write(f"       ⚠️  No invitation found for: {matched_subcontractor.company}")
                    else:
                        if verbose:
                            self.stdout.write(f"       ❌ No subcontractor match found")

                if verbose:
                    self.stdout.write("")  # Empty line for readability

            return processed_emails, potential_matches

        except Exception as e:
            self.stdout.write(f"   ❌ Error in dry run: {str(e)}")
            return 0, 0

    def _show_invitation_summary(self, configs):
        """Show summary of invitation statuses for the monitored projects"""
        self.stdout.write("\n📊 CURRENT INVITATION STATUS:")
        self.stdout.write("-" * 40)

        for config in configs:
            invitations = TenderInvitation.objects.filter(project=config.project)
            
            total = invitations.count()
            returned = invitations.filter(tender_returned=True).count()
            pending = invitations.filter(status='PENDING').count()
            accepted = invitations.filter(status='ACCEPTED').count()
            declined = invitations.filter(status='DECLINED').count()

            self.stdout.write(f"📁 {config.project.name}:")
            self.stdout.write(f"   Total invitations: {total}")
            self.stdout.write(f"   Tenders returned: {returned}")
            self.stdout.write(f"   Status - Pending: {pending}, Accepted: {accepted}, Declined: {declined}")
            
            if total > 0:
                return_rate = (returned / total) * 100
                self.stdout.write(f"   Return rate: {return_rate:.1f}%")
            
            self.stdout.write("")
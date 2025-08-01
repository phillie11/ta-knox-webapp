# management/commands/check_tender_returns.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from communications.services import OutlookEmailService
from communications.models import EmailMonitorConfig
from tenders.models import TenderInvitation
from subcontractors.models import Subcontractor
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Check configured email folders for tender returns with enhanced debugging'

    def add_arguments(self, parser):
        parser.add_argument(
            '--project-id',
            type=int,
            help='Check only a specific project by ID',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--test-matching',
            action='store_true',
            help='Test email matching logic without processing folders',
        )

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write("Starting enhanced email monitoring for tender returns...")
        self.stdout.write("=" * 80)

        if options['test_matching']:
            self.test_email_matching()
            return

        try:
            # Create the service
            service = OutlookEmailService()
            
            # Get configurations to process
            if options['project_id']:
                configs = EmailMonitorConfig.objects.filter(
                    project_id=options['project_id'],
                    is_active=True
                )
                if not configs.exists():
                    self.stdout.write(
                        self.style.ERROR(f"No active email monitoring found for project ID {options['project_id']}")
                    )
                    return
            else:
                configs = EmailMonitorConfig.objects.filter(is_active=True)

            self.stdout.write(f"Found {configs.count()} active email monitoring configurations")

            total_processed = 0
            total_matched = 0

            for config in configs:
                self.stdout.write(f"\n📁 Processing project: {config.project.name}")
                self.stdout.write(f"   Folder: {config.folder_name}")
                self.stdout.write(f"   Last check: {config.last_check_time or 'Never'}")
                
                # Show project invitations for context
                invitations = TenderInvitation.objects.filter(project=config.project)
                self.stdout.write(f"   Project has {invitations.count()} invitations")
                
                if options['verbose']:
                    for inv in invitations:
                        status_icon = "✓" if inv.tender_returned else "○"
                        self.stdout.write(
                            f"   {status_icon} {inv.subcontractor.company} ({inv.subcontractor.email}) - "
                            f"Status: {inv.status}, Returned: {inv.tender_returned}"
                        )

                if options['dry_run']:
                    self.stdout.write("   [DRY RUN] Would process this folder...")
                    continue

                try:
                    processed, matched = service.process_project_folder(config)
                    total_processed += processed
                    total_matched += matched
                    
                    self.stdout.write(
                        f"   📧 Processed {processed} emails, matched {matched} tender returns"
                    )
                    
                    if matched > 0:
                        self.stdout.write(self.style.SUCCESS(f"   ✓ Found {matched} new tender returns!"))

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"   ❌ Error processing folder: {str(e)}")
                    )
                    logger.exception(f"Error processing folder for project {config.project.name}")

            self.stdout.write("\n" + "=" * 80)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Email monitoring completed successfully!\n"
                    f"Total emails processed: {total_processed}\n"
                    f"Total tender returns matched: {total_matched}"
                )
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Email monitoring failed: {str(e)}"))
            logger.exception("Email monitoring command failed")
            raise

    def test_email_matching(self):
        """Test the email matching logic with current data"""
        self.stdout.write("🧪 Testing email matching logic...")
        
        from communications.services import OutlookEmailService
        
        # Get all active projects with invitations
        configs = EmailMonitorConfig.objects.filter(is_active=True)
        
        for config in configs:
            self.stdout.write(f"\n📋 Project: {config.project.name}")
            
            invitations = TenderInvitation.objects.filter(project=config.project)
            
            # Create lookup tables like the service does
            email_to_invitation = {}
            domain_to_invitations = {}
            
            for invitation in invitations:
                subcontractor = invitation.subcontractor
                
                if subcontractor.email:
                    email_to_invitation[subcontractor.email.lower()] = invitation
                    
                    domain = subcontractor.email.split('@')[-1].lower()
                    if domain not in domain_to_invitations:
                        domain_to_invitations[domain] = []
                    domain_to_invitations[domain].append(invitation)

            self.stdout.write(f"   📧 {len(email_to_invitation)} direct email mappings")
            self.stdout.write(f"   🌐 {len(domain_to_invitations)} domain mappings")
            
            # Show the mappings
            if len(email_to_invitation) > 0:
                self.stdout.write("   Direct email mappings:")
                for email, inv in email_to_invitation.items():
                    self.stdout.write(f"     {email} -> {inv.subcontractor.company}")
            
            if len(domain_to_invitations) > 0:
                self.stdout.write("   Domain mappings:")
                for domain, invs in domain_to_invitations.items():
                    companies = [inv.subcontractor.company for inv in invs]
                    self.stdout.write(f"     @{domain} -> {', '.join(companies)}")
            
            # Test some example emails
            test_emails = [
                f"info@{list(domain_to_invitations.keys())[0]}" if domain_to_invitations else "test@example.com",
                f"quotes@{list(domain_to_invitations.keys())[0]}" if domain_to_invitations else "quotes@example.com",
            ]
            
            self.stdout.write("   🧪 Testing example emails:")
            service = OutlookEmailService()
            for test_email in test_emails:
                matched = service._find_matching_invitation(
                    test_email.lower(),
                    email_to_invitation,
                    domain_to_invitations,
                    config.project
                )
                
                if matched:
                    self.stdout.write(f"     ✓ {test_email} -> {matched.subcontractor.company}")
                else:
                    self.stdout.write(f"     ❌ {test_email} -> No match found")

        self.stdout.write("\n✅ Email matching test completed!")
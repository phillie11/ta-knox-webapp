# communications/management/commands/check_emails_simple.py
from django.core.management.base import BaseCommand
from communications.services import OutlookEmailService
from communications.models import EmailMonitorConfig

class Command(BaseCommand):
    help = 'Simple email check for tender returns - domain matching only'

    def add_arguments(self, parser):
        parser.add_argument(
            '--project-id',
            type=int,
            help='Check emails for a specific project only'
        )

    def handle(self, *args, **options):
        self.stdout.write("🔍 Starting simplified email check...")

        try:
            # Get email service
            service = OutlookEmailService()
            
            # Get configurations to check
            configs = EmailMonitorConfig.objects.filter(is_active=True)
            
            if options['project_id']:
                configs = configs.filter(project_id=options['project_id'])
            
            if not configs.exists():
                self.stdout.write(self.style.WARNING("No active email monitoring configurations found"))
                return

            total_emails = 0
            total_matched = 0

            for config in configs:
                self.stdout.write(f"\n📧 Checking project: {config.project.name}")
                self.stdout.write(f"   Folder: {config.folder_name}")
                
                try:
                    emails_processed, tenders_matched = service.check_project_folder_simple(config)
                    
                    total_emails += emails_processed
                    total_matched += tenders_matched
                    
                    self.stdout.write(f"   ✅ Processed {emails_processed} emails")
                    if tenders_matched > 0:
                        self.stdout.write(
                            self.style.SUCCESS(f"   🎯 Found {tenders_matched} tender returns!")
                        )
                    else:
                        self.stdout.write("   📭 No new tender returns found")
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"   ❌ Error checking {config.project.name}: {str(e)}")
                    )

            self.stdout.write(f"\n📊 Summary:")
            self.stdout.write(f"   Total emails processed: {total_emails}")
            self.stdout.write(f"   Total tender returns found: {total_matched}")
            
            if total_matched > 0:
                self.stdout.write(self.style.SUCCESS("✅ Email check completed successfully!"))
            else:
                self.stdout.write(self.style.WARNING("📭 No new tender returns found"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error during email check: {str(e)}"))
            raise
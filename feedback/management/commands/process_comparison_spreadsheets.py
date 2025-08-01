# feedback/management/commands/process_comparison_spreadsheets.py
import os
import logging
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from feedback.services import FeedbackService

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Process comparison spreadsheets for subcontractor feedback'
    
    def add_arguments(self, parser):
        parser.add_argument('project_id', type=int, help='ID of the project')
        parser.add_argument('spreadsheet_path', help='Path to the comparison spreadsheet')
        parser.add_argument('--send', action='store_true', help='Send emails immediately after processing')
    
    def handle(self, *args, **options):
        try:
            project_id = options['project_id']
            spreadsheet_path = options['spreadsheet_path']
            send_emails = options['send']
            
            # Validate spreadsheet path
            if not os.path.exists(spreadsheet_path):
                raise CommandError(f"Spreadsheet not found at: {spreadsheet_path}")
            
            # Initialize the service
            service = FeedbackService()
            
            # Process the spreadsheet
            self.stdout.write(self.style.SUCCESS(f"Processing spreadsheet: {spreadsheet_path}"))
            results = service.process_spreadsheet(project_id, spreadsheet_path)
            
            # Display results
            self.stdout.write(self.style.SUCCESS(
                f"Processed {results['processed_subcontractors']} subcontractors in {results['total_trades']} trades"
            ))
            
            # Show errors if any
            if results['errors']:
                self.stdout.write(self.style.WARNING(f"Encountered {len(results['errors'])} errors:"))
                for error in results['errors']:
                    error_msg = f"- Error in {error.get('trade', 'unknown')}"
                    if 'subcontractor' in error:
                        error_msg += f" for {error['subcontractor']}"
                    error_msg += f": {error.get('error', 'unknown error')}"
                    
                    self.stdout.write(self.style.WARNING(error_msg))
            
            # Send emails if requested
            if send_emails:
                self.stdout.write(self.style.SUCCESS(f"Sending feedback emails..."))
                send_results = service.send_feedback_emails(project_id)
                
                self.stdout.write(self.style.SUCCESS(
                    f"Sent {send_results['sent']} feedback emails" +
                    (f" ({send_results['failed']} failed)" if send_results['failed'] > 0 else "")
                ))
            
        except Exception as e:
            logger.exception(f"Error processing spreadsheet: {str(e)}")
            raise CommandError(f"Error processing spreadsheet: {str(e)}")
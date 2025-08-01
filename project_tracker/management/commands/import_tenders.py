# In project_tracker/management/commands/import_tenders.py
import pandas as pd
from django.core.management.base import BaseCommand
from projects.models import Project

class Command(BaseCommand):
    help = 'Import tender data from CSV/Excel file'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to CSV or Excel file')

    def handle(self, *args, **options):
        file_path = options['file_path']
        self.stdout.write(f"Importing tender data from {file_path}")

        # Detect file type and read accordingly
        if file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        else:
            df = pd.read_csv(file_path)

        # Track statistics
        stats = {
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0
        }

        # Process each row
        for _, row in df.iterrows():
            try:
                # Required fields check
                if pd.isna(row.get('project_name')) or pd.isna(row.get('status')):
                    stats['skipped'] += 1
                    continue

                # Create or update the project
                project, created = Project.objects.update_or_create(
                    name=row.get('project_name'),
                    defaults={
                        'reference': row.get('reference', ''),
                        'location': row.get('location', ''),
                        'status': row.get('status'),
                        'estimator': row.get('estimator', ''),
                        'tender_bid_amount': row.get('bid_amount'),
                        'margin_percentage': row.get('margin'),
                        # Add other fields as needed
                    }
                )

                if created:
                    stats['created'] += 1
                else:
                    stats['updated'] += 1

            except Exception as e:
                self.stderr.write(f"Error processing {row.get('project_name')}: {str(e)}")
                stats['errors'] += 1

        # Report results
        self.stdout.write(self.style.SUCCESS(f"Import complete:"))
        self.stdout.write(f"  Created: {stats['created']}")
        self.stdout.write(f"  Updated: {stats['updated']}")
        self.stdout.write(f"  Skipped: {stats['skipped']}")
        self.stdout.write(f"  Errors: {stats['errors']}")
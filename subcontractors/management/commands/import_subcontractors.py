# In subcontractors/management/commands/import_subcontractors.py
import pandas as pd
from datetime import datetime
from django.core.management.base import BaseCommand
from subcontractors.models import Subcontractor, Trade, Region

class Command(BaseCommand):
    help = 'Import subcontractors from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to CSV file')

    def handle(self, *args, **options):
        file_path = options['file_path']
        self.stdout.write(f"Importing subcontractors from {file_path}")
        
        # Read the CSV file
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            self.stderr.write(f"Error reading file: {str(e)}")
            return
        
        # Get all existing trades to reduce DB queries
        existing_trades = {t.name: t for t in Trade.objects.all()}
        existing_regions = {r.name: r for r in Region.objects.all()}
        
        # Track statistics
        stats = {
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0
        }
        
        # Process each row
        for _, row in df.iterrows():
            # Skip rows without company or email
            if pd.isna(row.get('Company')) or pd.isna(row.get('Email')):
                stats['skipped'] += 1
                continue
            
            try:
                # Get or create trade
                trade_name = row.get('Trade')
                if pd.isna(trade_name):
                    trade = None
                else:
                    if trade_name not in existing_trades:
                        trade = Trade.objects.create(name=trade_name)
                        existing_trades[trade_name] = trade
                    else:
                        trade = existing_trades[trade_name]
                
                # Process regions
                regions_text = row.get('Regions they opperate')
                region_objs = []
                if not pd.isna(regions_text):
                    region_names = [r.strip() for r in str(regions_text).split(',')]
                    for region_name in region_names:
                        if region_name not in existing_regions:
                            region = Region.objects.create(name=region_name)
                            existing_regions[region_name] = region
                        else:
                            region = existing_regions[region_name]
                        region_objs.append(region)
                
                # Map PQQ status
                pqq_value = row.get('PQQ ')
                if pd.isna(pqq_value):
                    pqq_status = 'NONE'
                elif 'complete' in str(pqq_value).lower():
                    pqq_status = 'COMPLETED'
                elif 'sent' in str(pqq_value).lower():
                    pqq_status = 'SENT'
                else:
                    pqq_status = 'NONE'
                
                # Parse dates (handle DD/MM/YYYY format)
                insurance_expiry = None
                if not pd.isna(row.get('Insurance Exp')):
                    try:
                        # Try to parse the date in various formats
                        date_str = str(row.get('Insurance Exp')).strip()
                        try:
                            # Try DD/MM/YYYY format
                            insurance_expiry = datetime.strptime(date_str, '%d/%m/%Y').date()
                        except ValueError:
                            # Try other common formats
                            try:
                                insurance_expiry = datetime.strptime(date_str, '%Y-%m-%d').date()
                            except ValueError:
                                # If all parsing fails, leave as None
                                self.stdout.write(f"  Warning: Could not parse date '{date_str}' for {row.get('Company')}")
                    except Exception as e:
                        self.stdout.write(f"  Warning: Date parsing error for {row.get('Company')}: {str(e)}")
                
                # Create or update subcontractor
                try:
                    # First try to find by email (most unique)
                    existing = Subcontractor.objects.filter(email=row.get('Email')).first()
                    
                    if not existing:
                        # If not found by email, try company+head_office
                        existing = Subcontractor.objects.filter(
                            company=row.get('Company'),
                            head_office=row.get('Head Office ') if not pd.isna(row.get('Head Office ')) else ''
                        ).first()
                    
                    if existing:
                        # Update existing record
                        existing.trade = trade
                        existing.head_office = row.get('Head Office ') if not pd.isna(row.get('Head Office ')) else ''
                        existing.pqq_status = pqq_status
                        existing.first_name = row.get('First Name') if not pd.isna(row.get('First Name')) else ''
                        existing.surname = row.get('Surname') if not pd.isna(row.get('Surname')) else ''
                        existing.mobile = row.get('Mobile') if not pd.isna(row.get('Mobile')) else ''
                        existing.landline = row.get('__EMPTY') if not pd.isna(row.get('__EMPTY')) else ''
                        existing.website = row.get('Website') if not pd.isna(row.get('Website')) else ''
                        existing.insurance_expiry = insurance_expiry
                        existing.save()
                        
                        # Update regions (many-to-many)
                        existing.regions.set(region_objs)
                        
                        stats['updated'] += 1
                        
                    else:
                        # Create new record
                        subcontractor = Subcontractor.objects.create(
                            trade=trade,
                            company=row.get('Company'),
                            head_office=row.get('Head Office ') if not pd.isna(row.get('Head Office ')) else '',
                            pqq_status=pqq_status,
                            first_name=row.get('First Name') if not pd.isna(row.get('First Name')) else '',
                            surname=row.get('Surname') if not pd.isna(row.get('Surname')) else '',
                            email=row.get('Email'),
                            mobile=row.get('Mobile') if not pd.isna(row.get('Mobile')) else '',
                            landline=row.get('__EMPTY') if not pd.isna(row.get('__EMPTY')) else '',
                            website=row.get('Website') if not pd.isna(row.get('Website')) else '',
                            insurance_expiry=insurance_expiry,
                        )
                        
                        # Add regions (many-to-many)
                        subcontractor.regions.set(region_objs)
                        
                        stats['created'] += 1
                
                except Exception as e:
                    self.stderr.write(f"Error processing {row.get('Company')}: {str(e)}")
                    stats['errors'] += 1
                    
            except Exception as e:
                self.stderr.write(f"Error processing {row.get('Company')}: {str(e)}")
                stats['errors'] += 1
        
        # Report results
        self.stdout.write(self.style.SUCCESS(f"Import complete:"))
        self.stdout.write(f"  Created: {stats['created']}")
        self.stdout.write(f"  Updated: {stats['updated']}")
        self.stdout.write(f"  Skipped: {stats['skipped']}")
        self.stdout.write(f"  Errors: {stats['errors']}")
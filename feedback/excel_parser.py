# feedback/excel_parser.py
# Using xlrd instead of openpyxl to avoid numpy conflicts

import logging
import xlrd
from datetime import datetime
import csv
import io

logger = logging.getLogger(__name__)

class ExcelParser:
    """Excel parser using xlrd (no numpy dependency)"""
    
    def __init__(self, file_path=None, file_content=None):
        self.file_path = file_path
        self.file_content = file_content
        self.workbook = None
        self.worksheet = None
        self.headers = []
        self.data = []
    
    def load_file(self):
        """Load Excel file using xlrd"""
        try:
            if self.file_content:
                # Load from file content (uploaded file)
                if hasattr(self.file_content, 'read'):
                    content = self.file_content.read()
                else:
                    content = self.file_content
                self.workbook = xlrd.open_workbook(file_contents=content)
            elif self.file_path:
                # Load from file path
                self.workbook = xlrd.open_workbook(self.file_path)
            else:
                raise ValueError("Either file_path or file_content must be provided")
            
            # Get the first worksheet
            self.worksheet = self.workbook.sheet_by_index(0)
            self._parse_data()
            return True
        except Exception as e:
            logger.error(f"Error loading Excel file: {str(e)}")
            return False
    
    def _parse_data(self):
        """Parse worksheet data into headers and rows"""
        if not self.worksheet:
            return
        
        if self.worksheet.nrows == 0:
            return
        
        # Get headers from first row
        self.headers = []
        for col in range(self.worksheet.ncols):
            cell_value = self.worksheet.cell_value(0, col)
            if cell_value:
                self.headers.append(str(cell_value).strip())
            else:
                self.headers.append(f'Column_{col}')
        
        # Get data rows (skip header row)
        self.data = []
        for row in range(1, self.worksheet.nrows):
            row_dict = {}
            has_data = False
            
            for col in range(min(self.worksheet.ncols, len(self.headers))):
                cell_value = self.worksheet.cell_value(row, col)
                header = self.headers[col]
                
                # Convert Excel date numbers to readable dates
                if self.worksheet.cell_type(row, col) == xlrd.XL_CELL_DATE:
                    try:
                        date_tuple = xlrd.xldate_as_tuple(cell_value, self.workbook.datemode)
                        cell_value = datetime(*date_tuple).strftime('%Y-%m-%d')
                    except:
                        pass
                
                # Clean up string values
                if isinstance(cell_value, str):
                    cell_value = cell_value.strip()
                
                row_dict[header] = cell_value if cell_value != '' else None
                
                if cell_value:
                    has_data = True
            
            if has_data:  # Only add rows with actual data
                self.data.append(row_dict)
    
    def get_data_as_list(self):
        """Get data as list of dictionaries"""
        return self.data.copy()
    
    def get_headers(self):
        """Get column headers"""
        return self.headers.copy()
    
    def get_column_values(self, column_name):
        """Get all values from a specific column"""
        return [row.get(column_name) for row in self.data if column_name in row and row[column_name] is not None]
    
    def filter_data(self, column_name, value):
        """Filter data by column value"""
        return [row for row in self.data if row.get(column_name) == value]
    
    def get_unique_values(self, column_name):
        """Get unique values from a column"""
        values = self.get_column_values(column_name)
        return list(set(str(v) for v in values if v is not None))
    
    def count_by_column(self, column_name):
        """Count occurrences of each value in a column"""
        values = self.get_column_values(column_name)
        counts = {}
        for value in values:
            if value is not None:
                str_value = str(value)
                counts[str_value] = counts.get(str_value, 0) + 1
        return counts
    
    def get_numeric_column_stats(self, column_name):
        """Get basic statistics for a numeric column"""
        values = []
        for row in self.data:
            if column_name in row and row[column_name] is not None:
                try:
                    # Try to convert to float
                    if isinstance(row[column_name], (int, float)):
                        values.append(float(row[column_name]))
                    elif isinstance(row[column_name], str):
                        # Try to parse string numbers
                        cleaned = str(row[column_name]).replace(',', '').strip()
                        if cleaned:
                            values.append(float(cleaned))
                except (ValueError, TypeError):
                    continue
        
        if not values:
            return {'count': 0, 'sum': 0, 'mean': 0, 'min': 0, 'max': 0}
        
        return {
            'count': len(values),
            'sum': sum(values),
            'mean': sum(values) / len(values),
            'min': min(values),
            'max': max(values)
        }
    
    def search_data(self, search_term, columns=None):
        """Search for a term across specified columns or all columns"""
        if columns is None:
            columns = self.headers
        
        results = []
        search_term = str(search_term).lower()
        
        for row in self.data:
            for column in columns:
                if column in row and row[column] is not None:
                    if search_term in str(row[column]).lower():
                        results.append(row)
                        break  # Found in this row, move to next row
        
        return results
    
    def export_to_csv(self, output_path):
        """Export data to CSV file"""
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                if not self.data:
                    return False
                
                writer = csv.DictWriter(csvfile, fieldnames=self.headers)
                writer.writeheader()
                for row in self.data:
                    writer.writerow(row)
            return True
        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
            return False

class CSVParser:
    """Simple CSV parser as fallback"""
    
    def __init__(self, file_path=None, file_content=None):
        self.file_path = file_path
        self.file_content = file_content
        self.headers = []
        self.data = []
    
    def load_file(self):
        """Load CSV file"""
        try:
            if self.file_content:
                if hasattr(self.file_content, 'read'):
                    content = self.file_content.read()
                    if isinstance(content, bytes):
                        content = content.decode('utf-8')
                else:
                    content = str(self.file_content)
                
                # Use StringIO to read from string
                csv_file = io.StringIO(content)
                reader = csv.DictReader(csv_file)
                self.headers = reader.fieldnames or []
                self.data = [row for row in reader]
                
            elif self.file_path:
                with open(self.file_path, 'r', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    self.headers = reader.fieldnames or []
                    self.data = [row for row in reader]
            
            return True
        except Exception as e:
            logger.error(f"Error loading CSV file: {str(e)}")
            return False
    
    def get_data_as_list(self):
        """Get data as list of dictionaries"""
        return self.data.copy()
    
    def get_headers(self):
        """Get column headers"""
        return self.headers.copy()

# Utility functions
def parse_excel_file(file_path):
    """Parse Excel file and return data"""
    parser = ExcelParser(file_path=file_path)
    if parser.load_file():
        return parser.get_data_as_list()
    return []

def parse_uploaded_file(file_content, filename=''):
    """Parse uploaded file (Excel or CSV)"""
    # Try Excel first
    if filename.lower().endswith(('.xlsx', '.xls')):
        parser = ExcelParser(file_content=file_content)
        if parser.load_file():
            return parser.get_data_as_list()
    
    # Try CSV as fallback
    parser = CSVParser(file_content=file_content)
    if parser.load_file():
        return parser.get_data_as_list()
    
    return []

def analyze_feedback_file(file_path_or_content, filename=''):
    """Analyze feedback data from file"""
    if isinstance(file_path_or_content, str):
        data = parse_excel_file(file_path_or_content)
    else:
        data = parse_uploaded_file(file_path_or_content, filename)
    
    if not data:
        return None
    
    # Basic analysis
    total_responses = len(data)
    headers = list(data[0].keys()) if data else []
    
    # Look for rating columns
    rating_columns = [h for h in headers if any(word in h.lower() for word in ['rating', 'score', 'satisfaction', 'stars'])]
    
    analysis = {
        'total_responses': total_responses,
        'headers': headers,
        'rating_columns': rating_columns,
        'sample_data': data[:3] if data else []
    }
    
    return analysis
# feedback/services.py
# Pure Python implementation - no external dependencies except xlrd

import csv
import json
import logging
from collections import Counter, defaultdict
from datetime import datetime, date

logger = logging.getLogger(__name__)

class FeedbackAnalysisService:
    """Service for analyzing feedback data - pure Python implementation"""
    
    @staticmethod
    def process_feedback_data(data_list):
        """Process raw feedback data and return analysis"""
        if not data_list:
            return {
                'total_responses': 0,
                'summary': 'No data to analyze',
                'analysis': {}
            }
        
        analysis = {
            'total_responses': len(data_list),
            'rating_analysis': FeedbackAnalysisService._analyze_ratings(data_list),
            'category_analysis': FeedbackAnalysisService._analyze_categories(data_list),
            'sentiment_analysis': FeedbackAnalysisService._analyze_sentiment(data_list),
            'response_trends': FeedbackAnalysisService._analyze_trends(data_list)
        }
        
        return analysis
    
    @staticmethod
    def _analyze_ratings(data_list):
        """Analyze rating data"""
        ratings = []
        rating_fields = ['rating', 'score', 'satisfaction', 'stars', 'overall_rating']
        
        for item in data_list:
            for field in rating_fields:
                if field in item and item[field] is not None:
                    try:
                        rating_str = str(item[field]).strip()
                        rating = float(rating_str)
                        if 0 <= rating <= 10:  # Assume 0-10 scale
                            ratings.append(rating)
                            break
                    except (ValueError, TypeError):
                        continue
        
        if not ratings:
            return {'count': 0, 'average': 0, 'distribution': {}}
        
        # Calculate distribution (group by whole numbers)
        distribution = Counter()
        for rating in ratings:
            rounded = int(round(rating))
            distribution[rounded] += 1
        
        return {
            'count': len(ratings),
            'average': round(sum(ratings) / len(ratings), 2),
            'min': min(ratings),
            'max': max(ratings),
            'distribution': dict(distribution)
        }
    
    @staticmethod
    def _analyze_categories(data_list):
        """Analyze feedback by categories"""
        categories = defaultdict(list)
        category_fields = ['category', 'type', 'department', 'topic', 'subject']
        
        for item in data_list:
            category = 'uncategorized'
            for field in category_fields:
                if field in item and item[field]:
                    category = str(item[field]).lower().strip()
                    break
            
            categories[category].append(item)
        
        # Calculate statistics for each category
        analysis = {}
        total_items = len(data_list)
        for category, items in categories.items():
            analysis[category] = {
                'count': len(items),
                'percentage': round((len(items) / total_items) * 100, 1) if total_items > 0 else 0
            }
        
        return analysis
    
    @staticmethod
    def _analyze_sentiment(data_list):
        """Basic sentiment analysis based on keywords"""
        positive_words = [
            'good', 'great', 'excellent', 'amazing', 'love', 'perfect', 'fantastic', 
            'wonderful', 'awesome', 'brilliant', 'outstanding', 'superb', 'satisfied',
            'happy', 'pleased', 'impressed', 'recommend'
        ]
        negative_words = [
            'bad', 'terrible', 'awful', 'hate', 'horrible', 'disappointing', 'poor', 
            'worst', 'dissatisfied', 'angry', 'frustrated', 'annoyed', 'upset',
            'complaint', 'problem', 'issue', 'wrong'
        ]
        
        sentiment_scores = {'positive': 0, 'negative': 0, 'neutral': 0}
        
        comment_fields = ['comment', 'feedback', 'review', 'text', 'message', 'notes', 'description']
        
        for item in data_list:
            comment = ''
            for field in comment_fields:
                if field in item and item[field]:
                    comment = str(item[field]).lower()
                    break
            
            if not comment:
                sentiment_scores['neutral'] += 1
                continue
            
            positive_count = sum(1 for word in positive_words if word in comment)
            negative_count = sum(1 for word in negative_words if word in comment)
            
            if positive_count > negative_count:
                sentiment_scores['positive'] += 1
            elif negative_count > positive_count:
                sentiment_scores['negative'] += 1
            else:
                sentiment_scores['neutral'] += 1
        
        # Convert to percentages
        total = sum(sentiment_scores.values())
        if total > 0:
            for key in sentiment_scores:
                sentiment_scores[key] = round((sentiment_scores[key] / total) * 100, 1)
        
        return sentiment_scores
    
    @staticmethod
    def _analyze_trends(data_list):
        """Analyze trends over time if date fields are available"""
        date_fields = ['date', 'created_at', 'timestamp', 'submitted_on', 'date_submitted']
        dated_items = []
        
        for item in data_list:
            item_date = None
            for field in date_fields:
                if field in item and item[field]:
                    try:
                        if isinstance(item[field], (datetime, date)):
                            item_date = item[field] if isinstance(item[field], date) else item[field].date()
                        elif isinstance(item[field], str):
                            # Try to parse common date formats
                            date_str = str(item[field]).strip()
                            for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S', '%d-%m-%Y']:
                                try:
                                    item_date = datetime.strptime(date_str, fmt).date()
                                    break
                                except ValueError:
                                    continue
                        break
                    except (ValueError, TypeError):
                        continue
            
            if item_date:
                dated_items.append((item_date, item))
        
        if not dated_items:
            return {'has_date_data': False, 'message': 'No date information found'}
        
        # Sort by date
        dated_items.sort(key=lambda x: x[0])
        
        # Group by month
        monthly_counts = defaultdict(int)
        for item_date, item in dated_items:
            month_key = f"{item_date.year}-{item_date.month:02d}"
            monthly_counts[month_key] += 1
        
        return {
            'has_date_data': True,
            'date_range': {
                'start': dated_items[0][0].isoformat(),
                'end': dated_items[-1][0].isoformat()
            },
            'monthly_distribution': dict(monthly_counts),
            'total_with_dates': len(dated_items)
        }
    
    @staticmethod
    def export_analysis_to_csv(analysis_data, output_path):
        """Export analysis results to CSV"""
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write summary
                writer.writerow(['Feedback Analysis Summary'])
                writer.writerow(['Generated on', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
                writer.writerow(['Total Responses', analysis_data.get('total_responses', 0)])
                writer.writerow([])
                
                # Write rating analysis
                if 'rating_analysis' in analysis_data and analysis_data['rating_analysis']['count'] > 0:
                    rating = analysis_data['rating_analysis']
                    writer.writerow(['Rating Analysis'])
                    writer.writerow(['Average Rating', rating.get('average', 0)])
                    writer.writerow(['Total Ratings', rating.get('count', 0)])
                    writer.writerow(['Min Rating', rating.get('min', 0)])
                    writer.writerow(['Max Rating', rating.get('max', 0)])
                    writer.writerow([])
                    
                    # Rating distribution
                    if rating.get('distribution'):
                        writer.writerow(['Rating Distribution'])
                        writer.writerow(['Rating', 'Count'])
                        for rating_val, count in sorted(rating['distribution'].items()):
                            writer.writerow([rating_val, count])
                        writer.writerow([])
                
                # Write category analysis
                if 'category_analysis' in analysis_data:
                    writer.writerow(['Category Analysis'])
                    writer.writerow(['Category', 'Count', 'Percentage'])
                    for category, data in analysis_data['category_analysis'].items():
                        writer.writerow([category, data['count'], f"{data['percentage']}%"])
                    writer.writerow([])
                
                # Write sentiment analysis
                if 'sentiment_analysis' in analysis_data:
                    writer.writerow(['Sentiment Analysis'])
                    writer.writerow(['Sentiment', 'Percentage'])
                    for sentiment, percentage in analysis_data['sentiment_analysis'].items():
                        writer.writerow([sentiment.title(), f"{percentage}%"])
            
            return True
        except Exception as e:
            logger.error(f"Error exporting analysis to CSV: {str(e)}")
            return False
    
    @staticmethod
    def process_file_feedback(file_path_or_content, filename=''):
        """Process feedback from any supported file format"""
        try:
            # Import here to avoid circular imports
            from .excel_parser import parse_uploaded_file, parse_excel_file
            
            if isinstance(file_path_or_content, str):
                data = parse_excel_file(file_path_or_content)
            else:
                data = parse_uploaded_file(file_path_or_content, filename)
            
            if not data:
                return {
                    'error': 'Could not parse file or file is empty',
                    'total_responses': 0
                }
            
            analysis = FeedbackAnalysisService.process_feedback_data(data)
            
            # Add file-specific metadata
            analysis['file_info'] = {
                'filename': filename,
                'headers': list(data[0].keys()) if data else [],
                'total_rows': len(data),
                'sample_data': data[:2] if data else []  # First 2 rows as sample
            }
            
            return analysis
        
        except Exception as e:
            logger.error(f"Error processing file feedback: {str(e)}")
            return {
                'error': f'Error processing file: {str(e)}',
                'total_responses': 0
            }

class FeedbackReportGenerator:
    """Generate reports from feedback analysis"""
    
    @staticmethod
    def generate_summary_report(analysis_data):
        """Generate a text summary report"""
        if not analysis_data or analysis_data.get('total_responses', 0) == 0:
            return "No feedback data available for report generation."
        
        report = []
        report.append("FEEDBACK ANALYSIS REPORT")
        report.append("=" * 50)
        report.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Responses: {analysis_data.get('total_responses', 0)}")
        report.append("")
        
        # Rating summary
        if 'rating_analysis' in analysis_data and analysis_data['rating_analysis']['count'] > 0:
            rating = analysis_data['rating_analysis']
            report.append("RATING SUMMARY:")
            report.append(f"  Average Rating: {rating['average']}/10")
            report.append(f"  Total Ratings: {rating['count']}")
            report.append(f"  Range: {rating['min']} - {rating['max']}")
            
            if rating.get('distribution'):
                report.append("  Rating Distribution:")
                for rating_val, count in sorted(rating['distribution'].items()):
                    report.append(f"    {rating_val} stars: {count} responses")
            report.append("")
        
        # Category summary
        if 'category_analysis' in analysis_data:
            report.append("CATEGORY BREAKDOWN:")
            categories = analysis_data['category_analysis']
            sorted_categories = sorted(categories.items(), key=lambda x: x[1]['count'], reverse=True)
            for category, data in sorted_categories:
                report.append(f"  {category.title()}: {data['count']} ({data['percentage']}%)")
            report.append("")
        
        # Sentiment summary
        if 'sentiment_analysis' in analysis_data:
            sentiment = analysis_data['sentiment_analysis']
            report.append("SENTIMENT ANALYSIS:")
            report.append(f"  Positive: {sentiment.get('positive', 0)}%")
            report.append(f"  Negative: {sentiment.get('negative', 0)}%")
            report.append(f"  Neutral: {sentiment.get('neutral', 0)}%")
            report.append("")
        
        # Trends summary
        if 'response_trends' in analysis_data and analysis_data['response_trends'].get('has_date_data'):
            trends = analysis_data['response_trends']
            report.append("RESPONSE TRENDS:")
            report.append(f"  Date Range: {trends['date_range']['start']} to {trends['date_range']['end']}")
            report.append(f"  Responses with Dates: {trends['total_with_dates']}")
            report.append("")
        
        return "\n".join(report)
    
    @staticmethod
    def generate_json_report(analysis_data):
        """Generate JSON format report"""
        return json.dumps(analysis_data, indent=2, default=str)

# Utility functions for easy use
def quick_feedback_analysis(file_path):
    """Quick analysis of feedback file"""
    service = FeedbackAnalysisService()
    return service.process_file_feedback(file_path)

def generate_feedback_report(analysis_data, format_type='text'):
    """Generate feedback report in specified format"""
    generator = FeedbackReportGenerator()
    if format_type == 'json':
        return generator.generate_json_report(analysis_data)
    else:
        return generator.generate_summary_report(analysis_data)
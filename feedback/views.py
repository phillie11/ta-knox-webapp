# feedback/views.py
# Fixed imports to match the new service class names

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import json
import logging
import tempfile
import os

# FIXED: Import the correct class names
from .services import FeedbackAnalysisService, FeedbackReportGenerator
from .excel_parser import parse_uploaded_file, analyze_feedback_file

logger = logging.getLogger(__name__)

@login_required
def feedback_dashboard(request):
    """Main feedback dashboard"""
    return render(request, 'feedback/dashboard.html')

@login_required
def upload_feedback_file(request):
    """Handle feedback file upload and analysis"""
    if request.method == 'POST':
        if 'feedback_file' not in request.FILES:
            messages.error(request, 'No file was uploaded.')
            return redirect('feedback:dashboard')
        
        file = request.FILES['feedback_file']
        
        # Validate file type
        allowed_extensions = ['.xlsx', '.xls', '.csv']
        file_extension = os.path.splitext(file.name)[1].lower()
        
        if file_extension not in allowed_extensions:
            messages.error(request, 'Please upload an Excel (.xlsx, .xls) or CSV file.')
            return redirect('feedback:dashboard')
        
        try:
            # Process the file using our updated service
            analysis = FeedbackAnalysisService.process_file_feedback(file, file.name)
            
            if analysis and analysis.get('total_responses', 0) > 0:
                # Store analysis in session for display
                request.session['feedback_analysis'] = analysis
                messages.success(request, f'Successfully analyzed {analysis["total_responses"]} feedback responses.')
                return redirect('feedback:results')
            else:
                error_msg = analysis.get('error', 'No data found in file or file format not supported.')
                messages.error(request, f'Could not process file: {error_msg}')
                return redirect('feedback:dashboard')
                
        except Exception as e:
            logger.error(f"Error processing feedback file: {str(e)}")
            messages.error(request, f'Error processing file: {str(e)}')
            return redirect('feedback:dashboard')
    
    return render(request, 'feedback/upload.html')

@login_required
def feedback_results(request):
    """Display feedback analysis results"""
    analysis = request.session.get('feedback_analysis')
    
    if not analysis:
        messages.warning(request, 'No analysis data found. Please upload a file first.')
        return redirect('feedback:dashboard')
    
    # Generate text report
    try:
        text_report = FeedbackReportGenerator.generate_summary_report(analysis)
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        text_report = "Error generating report."
    
    context = {
        'analysis': analysis,
        'text_report': text_report,
        'has_ratings': analysis.get('rating_analysis', {}).get('count', 0) > 0,
        'has_categories': len(analysis.get('category_analysis', {})) > 0,
        'has_sentiment': any(analysis.get('sentiment_analysis', {}).values()),
    }
    
    return render(request, 'feedback/results.html', context)

@login_required
def export_analysis(request):
    """Export analysis results to CSV"""
    analysis = request.session.get('feedback_analysis')
    
    if not analysis:
        messages.error(request, 'No analysis data to export.')
        return redirect('feedback:dashboard')
    
    try:
        # Create temporary file for export
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
            success = FeedbackAnalysisService.export_analysis_to_csv(analysis, temp_file.name)
            
            if success:
                # Read the file and return as download
                with open(temp_file.name, 'r', encoding='utf-8') as f:
                    response = HttpResponse(f.read(), content_type='text/csv')
                    response['Content-Disposition'] = 'attachment; filename="feedback_analysis.csv"'
                
                # Clean up temp file
                os.unlink(temp_file.name)
                return response
            else:
                messages.error(request, 'Error exporting analysis.')
                
    except Exception as e:
        logger.error(f"Error exporting analysis: {str(e)}")
        messages.error(request, f'Error exporting data: {str(e)}')
    
    return redirect('feedback:results')

@login_required
def download_report(request, format_type='text'):
    """Download analysis report in specified format"""
    analysis = request.session.get('feedback_analysis')
    
    if not analysis:
        messages.error(request, 'No analysis data to download.')
        return redirect('feedback:dashboard')
    
    try:
        if format_type == 'json':
            report_content = FeedbackReportGenerator.generate_json_report(analysis)
            content_type = 'application/json'
            filename = 'feedback_report.json'
        else:
            report_content = FeedbackReportGenerator.generate_summary_report(analysis)
            content_type = 'text/plain'
            filename = 'feedback_report.txt'
        
        response = HttpResponse(report_content, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
        
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        messages.error(request, f'Error generating report: {str(e)}')
        return redirect('feedback:results')

@login_required
@csrf_exempt
def ajax_analyze_sample(request):
    """AJAX endpoint to analyze sample data"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method allowed'}, status=405)
    
    try:
        # Sample data for testing
        sample_data = [
            {'rating': 8, 'category': 'service', 'comment': 'Great service, very helpful staff'},
            {'rating': 6, 'category': 'product', 'comment': 'Product was okay, could be better'},
            {'rating': 9, 'category': 'service', 'comment': 'Excellent experience, highly recommend'},
            {'rating': 4, 'category': 'delivery', 'comment': 'Delivery was slow and disappointing'},
            {'rating': 7, 'category': 'product', 'comment': 'Good quality, satisfied with purchase'},
        ]
        
        analysis = FeedbackAnalysisService.process_feedback_data(sample_data)
        
        return JsonResponse({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        logger.error(f"Error in AJAX analysis: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def clear_analysis(request):
    """Clear stored analysis data"""
    if 'feedback_analysis' in request.session:
        del request.session['feedback_analysis']
    messages.info(request, 'Analysis data cleared.')
    return redirect('feedback:dashboard')

# Utility view for testing
@login_required
def test_feedback_analysis(request):
    """Test view to verify feedback analysis is working"""
    try:
        # Test with sample data
        test_data = [
            {'rating': 5, 'category': 'test', 'comment': 'This is a test comment'},
            {'rating': 8, 'category': 'test', 'comment': 'Another test with positive feedback'},
        ]
        
        analysis = FeedbackAnalysisService.process_feedback_data(test_data)
        report = FeedbackReportGenerator.generate_summary_report(analysis)
        
        return HttpResponse(f"<pre>{report}</pre>", content_type='text/html')
        
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)
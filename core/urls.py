# In core/urls.py
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.http import HttpResponse
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from project_tracker.views import ProjectAnalyticsView  # Import the analytics view
import traceback
import logging
import sys  # Import sys for sys.exc_info()

logger = logging.getLogger(__name__)

def debug_view(request):
    """Simple test view"""
    return HttpResponse("Debug view is working correctly!")

def error_test_view(request):
    """View that deliberately raises an exception"""
    logger.error("Testing error logging")
    raise Exception("This is a deliberate test exception")

def handler500(request, exception=None):
    """Custom 500 error handler that prints exception info"""
    type_, value, tb = sys.exc_info()
    error_text = f"Type: {type_}\nValue: {value}\nTraceback:\n{''.join(traceback.format_tb(tb))}"

    # Log the error to a file
    with open('/home/TAKnox/crm_system/custom_error.log', 'a') as f:
        f.write(f"\n\n--- New Error ---\n")
        f.write(error_text)

    # Only show detailed error in debug mode
    if settings.DEBUG:
        return HttpResponse(f"<pre>{error_text}</pre>", content_type="text/plain")
    else:
        return HttpResponse("Internal Server Error", content_type="text/plain", status=500)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('subcontractors/', include('subcontractors.urls')),
    path('projects/', include('projects.urls', namespace='projects')),
    path('tenders/', include('tenders.urls')),  # Remove the namespace parameter
    path('communications/', include('communications.urls')),
    path('project-tracker/', include('project_tracker.urls')),
    # Make the analytics view the homepage
    path('', ProjectAnalyticsView.as_view(), name='home'),
    path('debug/', debug_view, name='debug'),
    path('error-test/', error_test_view, name='error_test'),
    path('feedback/', include('feedback.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
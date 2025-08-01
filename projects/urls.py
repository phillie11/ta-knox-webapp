# projects/urls.py - Add these URL patterns

from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.ProjectListView.as_view(), name='list'),
    path('create/', views.ProjectCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ProjectDetailView.as_view(), name='detail'),
    path('<int:pk>/update/', views.ProjectUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.ProjectDeleteView.as_view(), name='delete'),
    path('<int:pk>/update-sharepoint-link/', views.update_sharepoint_link, name='update_sharepoint_link'),
    path('<int:pk>/remove-sharepoint-link/', views.remove_sharepoint_link, name='remove_sharepoint_link'),

    # NEW: Real SharePoint integration endpoints
    path('api/sharepoint-folders/', views.get_sharepoint_folders, name='get_sharepoint_folders'),
    path('api/test-sharepoint/', views.test_sharepoint_connection, name='test_sharepoint_connection'),
    path('api/debug-endpoint/', views.debug_sharepoint_endpoint, name='debug_sharepoint_endpoint'),
    path('api/test-minimal/', views.get_sharepoint_folders_minimal, name='test_minimal'),
    path('<int:pk>/update-sharepoint-folder/', views.update_sharepoint_folder, name='update_sharepoint_folder'),
    path('<int:pk>/update-email-folder/', views.update_email_folder, name='update_email_folder'),
]
# In project_tracker/urls.py
from django.urls import path
from . import views

app_name = 'project_tracker'

urlpatterns = [
    path('', views.ProjectTrackerListView.as_view(), name='list'),
    path('<int:pk>/', views.ProjectTrackerDetailView.as_view(), name='detail'),
    # Remove the analytics URL pattern since ProjectAnalyticsView is missing
    path('analytics/', views.ProjectAnalyticsView.as_view(), name='analytics'),
]
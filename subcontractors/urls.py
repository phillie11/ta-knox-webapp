# subcontractors/urls.py - Updated to include Trade management URLs
from django.urls import path
from . import views

app_name = 'subcontractors'

urlpatterns = [
    # Subcontractor URLs
    path('', views.SubcontractorListView.as_view(), name='list'),
    path('create/', views.SubcontractorCreateView.as_view(), name='create'),
    path('<int:pk>/', views.SubcontractorDetailView.as_view(), name='detail'),
    path('<int:pk>/update/', views.SubcontractorUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.SubcontractorDeleteView.as_view(), name='delete'),
    
    # Trade management URLs
    path('trades/', views.TradeListView.as_view(), name='trade_list'),
    path('trades/create/', views.TradeCreateView.as_view(), name='trade_create'),
    path('trades/<int:pk>/update/', views.TradeUpdateView.as_view(), name='trade_update'),
    path('trades/<int:pk>/delete/', views.TradeDeleteView.as_view(), name='trade_delete'),
    path('trades/ajax-create/', views.trade_create_ajax, name='trade_create_ajax'),
]
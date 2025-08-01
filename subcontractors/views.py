# subcontractors/views.py - Updated to include Trade management views
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from datetime import timedelta
from django.db import models
from .models import Subcontractor, Trade, Region
from .forms import SubcontractorForm, TradeForm

class SubcontractorListView(LoginRequiredMixin, ListView):
    model = Subcontractor
    context_object_name = 'subcontractors'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by trade if specified
        trade_id = self.request.GET.get('trade')
        if trade_id:
            queryset = queryset.filter(trade_id=trade_id)
        
        # Filter by region if specified
        region_id = self.request.GET.get('region')
        if region_id:
            queryset = queryset.filter(regions__id=region_id)
        
        # Search by name or company
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(company__icontains=search) | 
                models.Q(first_name__icontains=search) | 
                models.Q(surname__icontains=search) |
                models.Q(email__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['trades'] = Trade.objects.all()
        context['regions'] = Region.objects.all()
        return context

class SubcontractorDetailView(LoginRequiredMixin, DetailView):
    model = Subcontractor
    context_object_name = 'subcontractor'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['thirty_days_from_now'] = timezone.now().date() + timedelta(days=30)
        return context

class SubcontractorCreateView(LoginRequiredMixin, CreateView):
    model = Subcontractor
    form_class = SubcontractorForm
    success_url = reverse_lazy('subcontractors:list')
    
    def form_valid(self, form):
        messages.success(self.request, "Subcontractor created successfully.")
        return super().form_valid(form)

class SubcontractorUpdateView(LoginRequiredMixin, UpdateView):
    model = Subcontractor
    form_class = SubcontractorForm
    
    def get_success_url(self):
        return reverse_lazy('subcontractors:detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, "Subcontractor updated successfully.")
        return super().form_valid(form)

class SubcontractorDeleteView(LoginRequiredMixin, DeleteView):
    model = Subcontractor
    success_url = reverse_lazy('subcontractors:list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, "Subcontractor deleted successfully.")
        return super().delete(request, *args, **kwargs)

# NEW TRADE MANAGEMENT VIEWS

class TradeListView(LoginRequiredMixin, ListView):
    """List all trade categories"""
    model = Trade
    template_name = 'subcontractors/trade_list.html'
    context_object_name = 'trades'
    paginate_by = 20
    
    def get_queryset(self):
        return Trade.objects.annotate(
            subcontractor_count=models.Count('subcontractors')
        ).order_by('name')

class TradeCreateView(LoginRequiredMixin, CreateView):
    """Create a new trade category"""
    model = Trade
    form_class = TradeForm  
    template_name = 'subcontractors/trade_form.html'
    success_url = reverse_lazy('subcontractors:trade_list')
    
    def form_valid(self, form):
        messages.success(self.request, f"Trade category '{form.cleaned_data['name']}' created successfully.")
        return super().form_valid(form)

class TradeUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing trade category"""
    model = Trade
    form_class = TradeForm
    template_name = 'subcontractors/trade_form.html'
    success_url = reverse_lazy('subcontractors:trade_list')
    
    def form_valid(self, form):
        messages.success(self.request, f"Trade category '{form.cleaned_data['name']}' updated successfully.")
        return super().form_valid(form)

class TradeDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a trade category"""
    model = Trade
    template_name = 'subcontractors/trade_confirm_delete.html'
    success_url = reverse_lazy('subcontractors:trade_list')
    
    def delete(self, request, *args, **kwargs):
        trade_name = self.get_object().name
        messages.success(request, f"Trade category '{trade_name}' deleted successfully.")
        return super().delete(request, *args, **kwargs)

def trade_create_ajax(request):
    """AJAX endpoint for creating a new trade from a modal"""
    if request.method == 'POST':
        form = TradeForm(request.POST)
        if form.is_valid():
            trade = form.save()
            return JsonResponse({
                'success': True,
                'trade_id': trade.id,
                'trade_name': trade.name,
                'message': f"Trade '{trade.name}' created successfully."
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    return JsonResponse({'success': False, 'error': 'Invalid request method'})
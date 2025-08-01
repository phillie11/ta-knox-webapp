from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.utils import timezone  # Add this line
from projects.models import Project
import json
from decimal import Decimal
from django.db.models import Avg, Count, Q, F, Sum, Case, When, Value, IntegerField
from django.utils import timezone

class ProjectTrackerListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'project_tracker/list.html'
    context_object_name = 'projects'

    def get_queryset(self):
        status_filter = self.request.GET.get('status', 'LIVE')
        queryset = Project.objects.all()

        # No need to exclude completed tenders anymore - we'll filter by status
        # We want to see all projects organized by their status

        if status_filter and status_filter != 'ALL':
            queryset = queryset.filter(status=status_filter)

        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(reference__icontains=search_query) |
                Q(name__icontains=search_query) |
                Q(location__icontains=search_query)
            )

        return queryset.order_by('tender_deadline')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['statuses'] = [choice[0] for choice in Project.STATUS_CHOICES]
        context['current_status'] = self.request.GET.get('status', 'LIVE')

        # Initialize gantt_data as an empty list BEFORE the if statement
        gantt_data = []

        # Get gantt chart data for live projects
        if context['current_status'] == 'LIVE':
            for project in context['projects']:
                if project.start_date and project.tender_deadline:
                    deadline = project.tender_deadline

                    # Format with explicit timezone handling - adjust hours if needed
                    # Option 1: Add one hour to compensate
                    end_date_formatted = (deadline).strftime('%d/%m/%Y %H:%M')

                    # For other dates without time, regular formatting is fine
                    start_date_formatted = project.start_date.strftime('%d/%m/%Y')

                    item = {
                        'id': project.id,
                        'name': project.name,
                        'start': start_date_formatted,  # Use the formatted strings
                        'end': end_date_formatted,     # Use the formatted strings with time
                        'milestones': []
                    }

                    # Add milestones
                    if project.win_room_date:
                        item['milestones'].append({
                            'date': project.win_room_date.strftime('%d/%m/%Y'),  # Match format
                            'name': 'Win Room',
                            'type': 'win-room'
                        })
                    if project.site_visit_date:
                        item['milestones'].append({
                            'date': project.site_visit_date.strftime('%d/%m/%Y'),  # Match format
                            'name': 'Site Visit',
                            'type': 'site-visit'
                        })
                    if project.rfi_deadline:
                        item['milestones'].append({
                            'date': project.rfi_deadline.strftime('%d/%m/%Y'),  # Match format
                            'name': 'RFI Deadline',
                            'type': 'rfi'
                        })
                    if project.sc_deadline:
                        item['milestones'].append({
                            'date': project.sc_deadline.strftime('%d/%m/%Y'),  # Match format
                            'name': 'SC Deadline',
                            'type': 'sc-deadline'
                        })
                    if project.mid_bid_review_date:
                        item['milestones'].append({
                            'date': project.mid_bid_review_date.strftime('%d/%m/%Y'),  # Match format
                            'name': 'Mid Bid Review',
                            'type': 'mid-review'
                        })

                    gantt_data.append(item)

        # Add gantt_data to context AFTER the if statement
        context['gantt_data'] = json.dumps(gantt_data)

        return context

class ProjectTrackerDetailView(LoginRequiredMixin, DetailView):
    model = Project  # Use Project model here
    template_name = 'project_tracker/detail.html'
    context_object_name = 'project'

class ProjectAnalyticsView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'project_tracker/analytics.html'
    context_object_name = 'projects'

    def get_queryset(self):
        # Include completed tenders - those with bid amount and expired deadline
        now = timezone.now()
        queryset = Project.objects.filter(
            tender_bid_amount__isnull=False,
            tender_deadline__lt=now
        )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Prepare data for analytics
        completed_projects = self.get_queryset()

        # Success rate data
        successful = completed_projects.filter(status='SUCCESSFUL').count()
        unsuccessful = completed_projects.filter(status='UNSUCCESSFUL').count()
        total = successful + unsuccessful

        if total > 0:
            success_rate = (successful / total) * 100
        else:
            success_rate = 0

        context['success_rate'] = round(success_rate, 1)
        context['total_bids'] = total
        context['successful_bids'] = successful
        context['unsuccessful_bids'] = unsuccessful

        # Average margin data
        avg_margin_successful = completed_projects.filter(
            status='SUCCESSFUL',
            margin_percentage__isnull=False
        ).values_list('margin_percentage', flat=True)

        if avg_margin_successful:
            context['avg_margin_successful'] = sum(avg_margin_successful) / len(avg_margin_successful)
        else:
            context['avg_margin_successful'] = 0

        # Prepare chart data with location information
        margin_data = []
        for project in completed_projects:
            if project.margin_percentage and project.tender_bid_amount:
                margin_data.append({
                    'name': project.name,
                    'location': project.location,

                    'margin': float(project.margin_percentage),
                    'amount': float(project.tender_bid_amount),
                    'successful': project.status == 'SUCCESSFUL'
                })

        context['margin_chart_data'] = json.dumps(margin_data)

        # Enhanced location analytics data
        location_summary = {}
        for project in completed_projects:
            location = project.location or 'Unknown'

            if location not in location_summary:
                location_summary[location] = {
                    'total': 0,
                    'successful': 0,
                    'unsuccessful': 0,
                    'total_value': 0,
                    'avg_margin': 0,
                    'margins_sum': 0,
                    'projects_with_margin': 0
                }

            location_summary[location]['total'] += 1

            if project.status == 'SUCCESSFUL':
                location_summary[location]['successful'] += 1
            elif project.status == 'UNSUCCESSFUL':
                location_summary[location]['unsuccessful'] += 1

            if project.tender_bid_amount:
                location_summary[location]['total_value'] += float(project.tender_bid_amount)

            if project.margin_percentage:
                location_summary[location]['margins_sum'] += float(project.margin_percentage)
                location_summary[location]['projects_with_margin'] += 1

        # Calculate averages for location data
        for location in location_summary:
            if location_summary[location]['projects_with_margin'] > 0:
                location_summary[location]['avg_margin'] = (
                    location_summary[location]['margins_sum'] /
                    location_summary[location]['projects_with_margin']
                )

        context['location_summary'] = json.dumps(location_summary)

        return context
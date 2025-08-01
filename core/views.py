import traceback
import sys
from django.http import HttpResponse
from django.views.generic import TemplateView


# core/views.py
class HelpView(TemplateView):
    template_name = 'help.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        help_topic = self.kwargs.get('topic', 'general')

        # Map topics to template sections
        context['help_content'] = self.get_help_content(help_topic)
        context['available_topics'] = [
            'general', 'projects', 'tenders', 'subcontractors',
            'emails', 'analytics', 'settings'
        ]
        return context

    def get_help_content(self, topic):
        # Return help content based on topic
        help_content = {
            'general': {
                'title': 'General Help',
                'content': 'General instructions for using the CRM system...'
            },
            'projects': {
                'title': 'Managing Projects',
                'content': 'How to create, edit, and track projects...'
            },
            # Other topics...
        }
        return help_content.get(topic, help_content['general'])

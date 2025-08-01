from django.shortcuts import redirect
from django.contrib import messages
from django.urls import resolve

class EmailConfirmationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Skip check for certain paths
        path = request.path_info
        
        # List of paths to exclude from authentication checks
        excluded_paths = [
            '/',                    # Home page
            '/admin/',              # Admin pages
            '/accounts/login/',     # Login page
            '/accounts/logout/',    # Logout page
            '/accounts/signup/',    # Signup page
            '/accounts/activate/',  # Account activation
            '/login/',              # Alternative login page
            '/logout/',             # Alternative logout page
            '/debug/',              # Debug page
            '/static/',             # Static files
            '/media/',              # Media files
        ]
        
        # Check if the current path matches any excluded path
        for excluded_path in excluded_paths:
            if path == excluded_path or path.startswith(excluded_path):
                return None
        
        # Check if user is authenticated but email not confirmed
        if request.user.is_authenticated and not request.user.profile.email_confirmed:
            messages.warning(request, 'Please confirm your email address to access all features.')
            return redirect('home')
        
        # Check if user is not authenticated - redirect to login
        if not request.user.is_authenticated:
            messages.warning(request, 'Please log in to access this page.')
            return redirect('accounts:login')
        
        return None
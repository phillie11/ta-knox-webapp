// static/js/email_confirmation.js

/**
 * Email form confirmation dialog and validation
 * Adds a confirmation dialog before submitting email forms
 * and shows a loading spinner during submission
 */
document.addEventListener('DOMContentLoaded', function() {
  // Only run on email forms (invitation or addendum)
  const form = document.querySelector('.email-send-form');
  if (!form) return;

  form.addEventListener('submit', function(e) {
    // Count selected subcontractors
    const selectedCount = document.querySelectorAll('input[name="subcontractors"]:checked').length;

    // Prevent submission if no subcontractors selected
    if (selectedCount === 0) {
      e.preventDefault();
      alert('Please select at least one subcontractor before sending.');
      return;
    }

    // Prevent the form from submitting immediately
    e.preventDefault();

    // Create confirmation message based on the form type
    let confirmMessage = '';
    if (window.location.href.includes('send-invitation')) {
      confirmMessage = `Are you sure you want to send this invitation to ${selectedCount} selected subcontractor(s)?`;
    } else if (window.location.href.includes('send-addendum')) {
      confirmMessage = `Are you sure you want to send this addendum to ${selectedCount} selected subcontractor(s)?`;
    } else {
      confirmMessage = `Are you sure you want to send this email to ${selectedCount} selected subcontractor(s)?`;
    }

    // Display confirmation dialog
    const confirmDialog = confirm(confirmMessage);

    // Submit the form if confirmed
    if (confirmDialog) {
      // Create a loading overlay
      const loadingOverlay = document.createElement('div');
      loadingOverlay.style.position = 'fixed';
      loadingOverlay.style.top = '0';
      loadingOverlay.style.left = '0';
      loadingOverlay.style.width = '100%';
      loadingOverlay.style.height = '100%';
      loadingOverlay.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
      loadingOverlay.style.display = 'flex';
      loadingOverlay.style.justifyContent = 'center';
      loadingOverlay.style.alignItems = 'center';
      loadingOverlay.style.zIndex = '9999';

      const spinner = document.createElement('div');
      spinner.className = 'spinner-border text-light';
      spinner.setAttribute('role', 'status');
      spinner.style.width = '3rem';
      spinner.style.height = '3rem';

      const spinnerText = document.createElement('span');
      spinnerText.className = 'ms-3 text-light';
      spinnerText.textContent = 'Sending emails...';

      const spinnerContainer = document.createElement('div');
      spinnerContainer.appendChild(spinner);
      spinnerContainer.appendChild(spinnerText);

      loadingOverlay.appendChild(spinnerContainer);
      document.body.appendChild(loadingOverlay);

      // Submit the form after a short delay to allow the overlay to render
      setTimeout(() => {
        form.submit();
      }, 100);
    }
  });
});
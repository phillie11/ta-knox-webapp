// Combined email form confirmation and document upload functionality
document.addEventListener('DOMContentLoaded', function() {
  //
  // PART 1: QUILL EDITOR INITIALIZATION
  //
  if (document.getElementById('editor-container')) {
    var quill = new Quill('#editor-container', {
      modules: {
        toolbar: [
          ['bold', 'italic', 'underline', 'strike'],
          ['blockquote', 'code-block'],
          [{ 'header': 1 }, { 'header': 2 }],
          [{ 'list': 'ordered'}, { 'list': 'bullet' }],
          [{ 'color': [] }, { 'background': [] }],
          [{ 'align': [] }],
          ['clean']
        ]
      },
      placeholder: 'Compose your message...',
      theme: 'snow'
    });
    
    // Set initial content
    if (document.getElementById('id_message')) {
      quill.root.innerHTML = document.getElementById('id_message').value;
    
      // Update hidden form field before submit
      var form = document.querySelector('form');
      if (form) {
        form.addEventListener('submit', function() {
          document.getElementById('id_message').value = quill.root.innerHTML;
        });
      }
    }
  }

  //
  // PART 2: PROJECT ID DETECTION
  //
  function getProjectId() {
    // Strategy 1: Look for a hidden input named project_id
    let projectIdInput = document.querySelector('input[name="project_id"]');
    if (projectIdInput) {
      return projectIdInput.value;
    }

    // Strategy 2: Try to extract from the page URL
    const urlMatch = window.location.pathname.match(/\/project\/(\d+)\//);
    if (urlMatch && urlMatch[1]) {
      return urlMatch[1];
    }

    // Strategy 3: Look for project ID in page context
    if (window.projectId) {
      return window.projectId;
    }

    // Strategy 4: Check form's action URL
    const form = document.querySelector('form');
    if (form && form.action) {
      const formUrlMatch = form.action.match(/\/project\/(\d+)\//);
      if (formUrlMatch && formUrlMatch[1]) {
        return formUrlMatch[1];
      }
    }

    // Fallback
    console.error('Could not detect project ID through any method');
    return null;
  }

  //
  // PART 3: HELPER FUNCTIONS
  //
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  function showAlert(type, message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
      ${message}
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Find a good place to show the alert
    const container = document.querySelector('.container-fluid') || document.querySelector('.container');
    if (container) {
      container.insertBefore(alertDiv, container.firstChild);
      
      // Auto-dismiss after 5 seconds
      setTimeout(() => {
        alertDiv.remove();
      }, 5000);
    }
  }

  function getDocumentTypeLabel(type) {
    const types = {
      'MAIN': 'Main Tender Document',
      'SPEC': 'Specification',
      'DRAWING': 'Drawing',
      'ADDENDUM': 'Addendum',
      'OTHER': 'Other'
    };
    return types[type] || type;
  }

  //
  // PART 4: ATTACHMENT HANDLING
  //
  const saveAttachmentBtn = document.getElementById('saveAttachment');
  const attachmentList = document.getElementById('attachmentList');

  if (saveAttachmentBtn && attachmentList) {
    saveAttachmentBtn.addEventListener('click', function() {
      // Get form elements
      const documentType = document.getElementById('documentType').value;
      const documentTitle = document.getElementById('documentTitle').value;
      const documentFile = document.getElementById('documentFile').files[0];
      const sharePointLink = document.getElementById('sharePointLink')?.value || '';
      const documentDescription = document.getElementById('documentDescription')?.value || '';
      const projectId = document.querySelector('input[name="project_id"]')?.value || getProjectId();

      // Log details for debugging
      console.log('Attachment details:', {
        documentType,
        documentTitle,
        filePresent: !!documentFile,
        sharePointLink,
        projectId
      });

      // Validate inputs
      if (!documentType || !documentTitle) {
        alert('Please fill in all required fields');
        return;
      }

      if (!documentFile && !sharePointLink) {
        alert('Please provide either a file or a SharePoint link');
        return;
      }

      if (!projectId) {
        console.error('Project ID not found in the form');
        alert('Error: Project ID not found. Please refresh the page and try again.');
        return;
      }

      // Create FormData for file upload
      const formData = new FormData();
      formData.append('document_type', documentType);
      formData.append('title', documentTitle);
      formData.append('project_id', projectId);
      
      if (documentDescription) {
        formData.append('description', documentDescription);
      }
      
      if (documentFile) {
        formData.append('file', documentFile);
      }
      
      if (sharePointLink) {
        formData.append('sharepoint_link', sharePointLink);
      }

      // Get CSRF token from cookie
      const csrfToken = getCookie('csrftoken');
      
      if (!csrfToken) {
        console.error('CSRF token not found');
        alert('CSRF token not found. Please refresh the page.');
        return;
      }

      // Show loading indicator
      saveAttachmentBtn.disabled = true;
      saveAttachmentBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Uploading...';

      // AJAX request to upload document
      fetch("/tenders/upload-document/", {
        method: 'POST',
        body: formData,
        headers: {
          'X-CSRFToken': csrfToken
        }
      })
      .then(response => {
        if (!response.ok) {
          return response.json().then(data => {
            throw new Error(data.error || `Server error: ${response.status}`);
          });
        }
        return response.json();
      })
      .then(data => {
        if (data.success) {
          console.log('Document upload successful:', data);
          
          // Add document to the list
          const attachmentItem = document.createElement('div');
          attachmentItem.classList.add('attachment-item');
          attachmentItem.innerHTML = `
            <span>${documentTitle} (${data.document_type || getDocumentTypeLabel(documentType)})</span>
            <button type="button" class="btn btn-sm btn-danger remove-attachment" data-document-id="${data.document_id}">
              <i class="bi bi-trash"></i>
            </button>
          `;
          
          attachmentList.appendChild(attachmentItem);
          
          // Close modal
          const modal = bootstrap.Modal.getInstance(document.getElementById('attachmentModal'));
          modal.hide();
          
          // Reset form
          document.getElementById('documentType').value = '';
          document.getElementById('documentTitle').value = '';
          document.getElementById('documentFile').value = '';
          if (document.getElementById('documentDescription')) {
            document.getElementById('documentDescription').value = '';
          }
          document.getElementById('sharePointLink').value = '';
          
          // Show success message
          showAlert('success', `Document "${documentTitle}" uploaded successfully`);
        } else {
          console.error('Upload failed:', data.error);
          showAlert('danger', `Upload failed: ${data.error}`);
        }
      })
      .catch(error => {
        console.error('Error:', error);
        showAlert('danger', `An error occurred while uploading the document: ${error.message}`);
      })
      .finally(() => {
        // Reset button state
        saveAttachmentBtn.disabled = false;
        saveAttachmentBtn.innerHTML = 'Add Attachment';
      });
    });
  }

  // Remove attachment functionality
  if (attachmentList) {
    attachmentList.addEventListener('click', function(event) {
      const removeBtn = event.target.closest('.remove-attachment');
      if (removeBtn) {
        const documentId = removeBtn.getAttribute('data-document-id');
        
        // Simple confirmation dialog
        if (confirm(`Are you sure you want to remove this document?`)) {
          // Show feedback that removal is in progress
          removeBtn.disabled = true;
          removeBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>';
          
          // Get CSRF token
          const csrfToken = getCookie('csrftoken');
          
          // AJAX request to remove document
          fetch(`/tenders/document/${documentId}/remove/`, {
            method: 'POST',
            headers: {
              'X-CSRFToken': csrfToken,
              'Content-Type': 'application/json'
            }
          })
          .then(response => {
            if (!response.ok) {
              throw new Error(`Server error: ${response.status}`);
            }
            return response.json();
          })
          .then(data => {
            if (data.success) {
              // Simply remove the item from the DOM without additional alerts
              removeBtn.closest('.attachment-item').remove();
              showAlert('success', 'Document removed successfully');
            } else {
              // Only show alert for errors
              showAlert('danger', `Failed to remove document: ${data.error || 'Unknown error'}`);
              // Reset button state
              removeBtn.disabled = false;
              removeBtn.innerHTML = '<i class="bi bi-trash"></i>';
            }
          })
          .catch(error => {
            console.error('Error:', error);
            showAlert('danger', `An error occurred while removing the document: ${error.message}`);
            // Reset button state on error
            removeBtn.disabled = false;
            removeBtn.innerHTML = '<i class="bi bi-trash"></i>';
          });
        }
      }
    });
  }

  //
  // PART 5: SUBCONTRACTOR FILTERING
  //
  function setupSubcontractorFiltering() {
    // Only run if we have the necessary elements
    const tradeFilter = document.getElementById('tradeFilter');
    const searchInput = document.getElementById('searchInput');
    const clearFiltersBtn = document.getElementById('clearFiltersBtn');
    const selectAllBtn = document.getElementById('selectAllBtn');
    const countDisplay = document.getElementById('countDisplay');
    
    if (!tradeFilter || !searchInput) return;
    
    // Get all subcontractor items
    const subcontractorItems = document.querySelectorAll('.form-check');
    if (subcontractorItems.length === 0) return;
    
    // Get all display checkboxes
    const displayCheckboxes = document.querySelectorAll('input[name="display_subcontractors"]');
    
    // Get all form checkboxes (original ones that will be submitted)
    const formCheckboxes = document.querySelectorAll('input[name="subcontractors"]');
    
    // Sync the display checkboxes to the form checkboxes
    function syncCheckboxesToForm() {
      displayCheckboxes.forEach(displayCheckbox => {
        const value = displayCheckbox.value;
        const formCheckbox = document.querySelector(`input[name="subcontractors"][value="${value}"]`);
        
        if (formCheckbox) {
          formCheckbox.checked = displayCheckbox.checked;
        }
      });
    }
    
    // Add event listeners to display checkboxes
    displayCheckboxes.forEach(checkbox => {
      checkbox.addEventListener('change', syncCheckboxesToForm);
    });
    
    // Function to filter the list
    function filterList() {
      const selectedTrade = tradeFilter.value.toLowerCase();
      const searchText = searchInput.value.toLowerCase();
      
      let visibleCount = 0;
      const totalCount = subcontractorItems.length;
      
      subcontractorItems.forEach(item => {
        const trade = item.getAttribute('data-trade') || '';
        const company = item.getAttribute('data-company') || '';
        const headOffice = item.getAttribute('data-head-office') || '';
        
        // Check if it passes all filters
        const matchesTrade = !selectedTrade || trade.includes(selectedTrade);
        const matchesSearch = !searchText || 
                            company.includes(searchText) || 
                            trade.includes(searchText) || 
                            headOffice.includes(searchText);
        
        // Show or hide based on filter results
        if (matchesTrade && matchesSearch) {
          item.style.display = '';
          visibleCount++;
        } else {
          item.style.display = 'none';
        }
      });
      
      // Update count display
      if (countDisplay) {
        countDisplay.textContent = `Showing ${visibleCount} of ${totalCount} subcontractors`;
      }
    }
    
    // Initialize count display
    if (countDisplay) {
      countDisplay.textContent = `Showing ${subcontractorItems.length} of ${subcontractorItems.length} subcontractors`;
    }
    
    // Add event listeners for filters
    if (tradeFilter) {
      tradeFilter.addEventListener('change', filterList);
    }
    
    if (searchInput) {
      searchInput.addEventListener('input', filterList);
    }
    
    // Clear filters button
    if (clearFiltersBtn) {
      clearFiltersBtn.addEventListener('click', function(e) {
        e.preventDefault();
        tradeFilter.value = '';
        searchInput.value = '';
        filterList();
      });
    }
    
    // Select all visible button
    if (selectAllBtn) {
      selectAllBtn.addEventListener('click', function() {
        const visibleCheckboxes = document.querySelectorAll('.form-check:not([style*="display: none"]) input[type="checkbox"]');
        visibleCheckboxes.forEach(checkbox => {
          checkbox.checked = true;
        });
        
        // Sync to form checkboxes
        syncCheckboxesToForm();
      });
    }
  }

  // Initialize subcontractor filtering
  setupSubcontractorFiltering();

  //
  // PART 6: EMAIL FORM CONFIRMATION - TEMPORARILY DISABLED FOR TESTING
  //
  /*
  // Only run on email forms (invitation or addendum)
  const emailForm = document.querySelector('.email-send-form');
  if (emailForm) {
    
    function handleFormSubmission(e) {
      // Prevent the default submission
      e.preventDefault();
      e.stopImmediatePropagation();

      console.log('Form submission intercepted for confirmation');

      // Count selected subcontractors using BOTH display and form checkboxes
      const displayCheckboxes = document.querySelectorAll('input[name="display_subcontractors"]');
      const formCheckboxes = document.querySelectorAll('input[name="subcontractors"]');

      // Count checked display checkboxes
      const selectedDisplayCount = Array.from(displayCheckboxes)
        .filter(checkbox => checkbox.checked).length;

      // Count checked form checkboxes
      const selectedFormCount = Array.from(formCheckboxes)
        .filter(checkbox => checkbox.checked).length;

      // Prevent the form from submitting if no subcontractors are selected
      const totalSelectedCount = Math.max(selectedDisplayCount, selectedFormCount);
      
      if (totalSelectedCount === 0) {
        alert('Please select at least one subcontractor before sending.');
        return false;
      }

      // Synchronize display and form checkboxes
      displayCheckboxes.forEach(displayCheckbox => {
        const correspondingFormCheckbox = document.querySelector(
          `input[name="subcontractors"][value="${displayCheckbox.value}"]`
        );
        
        if (correspondingFormCheckbox) {
          correspondingFormCheckbox.checked = displayCheckbox.checked;
        }
      });

      // Ensure Quill editor content is saved to the hidden form field
      if (window.quill && document.getElementById('id_message')) {
        document.getElementById('id_message').value = quill.root.innerHTML;
      }

      // Create confirmation message based on form type
      let confirmMessage = '';
      if (window.location.href.includes('send-invitation')) {
        confirmMessage = `Are you sure you want to send this invitation to ${totalSelectedCount} selected subcontractor(s)?`;
      } else if (window.location.href.includes('send-addendum')) {
        confirmMessage = `Are you sure you want to send this addendum to ${totalSelectedCount} selected subcontractor(s)?`;
      } else {
        confirmMessage = `Are you sure you want to send this email to ${totalSelectedCount} selected subcontractor(s)?`;
      }

      // Display confirmation dialog
      const confirmDialog = confirm(confirmMessage);

      // If confirmed, proceed with submission
      if (confirmDialog) {
        console.log('User confirmed, removing event listener and submitting form');
        
        // CRITICAL: Remove ALL event listeners from the form
        emailForm.removeEventListener('submit', handleFormSubmission, true);
        emailForm.removeEventListener('submit', handleFormSubmission, false);
        
        // Disable the submit button to prevent multiple clicks
        const submitButton = emailForm.querySelector('button[type="submit"]');
        if (submitButton) {
          submitButton.disabled = true;
          submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Sending...';
        }

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
        loadingOverlay.id = 'emailLoadingOverlay';

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

        // Use requestSubmit() for modern browsers or submit() as fallback
        setTimeout(() => {
          console.log('Submitting form after removing event listeners');
          
          // Try the modern approach first
          if (emailForm.requestSubmit) {
            emailForm.requestSubmit();
          } else {
            // Fallback for older browsers
            emailForm.submit();
          }
        }, 100);
      } else {
        console.log('User cancelled confirmation');
      }
      
      return false;
    }
    
    // Add the event listener with capture to ensure we catch it first
    emailForm.addEventListener('submit', handleFormSubmission, true);
  }
  */
  
  // SIMPLE TEST: Just sync checkboxes and ensure Quill content is saved
  const emailForm = document.querySelector('.email-send-form');
  if (emailForm) {
    emailForm.addEventListener('submit', function(e) {
      console.log('Simple form submission - no confirmation dialog');
      
      // Synchronize display and form checkboxes
      const displayCheckboxes = document.querySelectorAll('input[name="display_subcontractors"]');
      displayCheckboxes.forEach(displayCheckbox => {
        const correspondingFormCheckbox = document.querySelector(
          `input[name="subcontractors"][value="${displayCheckbox.value}"]`
        );
        if (correspondingFormCheckbox) {
          correspondingFormCheckbox.checked = displayCheckbox.checked;
        }
      });

      // Ensure Quill editor content is saved
      if (window.quill && document.getElementById('id_message')) {
        document.getElementById('id_message').value = quill.root.innerHTML;
      }
      
      // Let the form submit naturally - no preventDefault, no confirmation
    });
  }
});
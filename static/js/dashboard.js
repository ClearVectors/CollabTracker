document.addEventListener('DOMContentLoaded', function() {
    // Handle collaboration form submission
    const collaborationForm = document.getElementById('collaborationForm');
    if (collaborationForm) {
        collaborationForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(collaborationForm);
            
            try {
                const response = await fetch('/collaboration/new', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                
                if (data.success) {
                    window.location.reload();
                } else {
                    alert('Error creating collaboration: ' + data.error);
                }
            } catch (error) {
                console.error('Error:', error);
            }
        });
    }

    // Initialize KPI charts
    const progressBars = document.querySelectorAll('.progress-bar');
    progressBars.forEach(bar => {
        bar.style.width = bar.getAttribute('aria-valuenow') + '%';
    });
});

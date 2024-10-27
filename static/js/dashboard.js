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

    // Handle export data click
    const exportButton = document.querySelector('a[href="/export/data"]');
    if (exportButton) {
        exportButton.addEventListener('click', async (e) => {
            e.preventDefault();
            try {
                const response = await fetch('/export/data');
                
                if (response.ok) {
                    const contentType = response.headers.get('content-type');
                    if (contentType && contentType.includes('spreadsheetml')) {
                        // If the response is successful and it's an Excel file, download it
                        const blob = await response.blob();
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `collaboration_data_${new Date().toISOString().split('T')[0]}.xlsx`;
                        document.body.appendChild(a);
                        a.click();
                        window.URL.revokeObjectURL(url);
                        a.remove();
                    } else {
                        const data = await response.json();
                        alert('Export failed: Invalid file format received');
                    }
                } else {
                    const data = await response.json();
                    alert('Export failed: ' + (data.error || 'Unknown error occurred'));
                }
            } catch (error) {
                console.error('Export error:', error);
                alert('Failed to export data. Please try again later.');
            }
        });
    }

    // Initialize KPI charts
    const progressBars = document.querySelectorAll('.progress-bar');
    progressBars.forEach(bar => {
        bar.style.width = bar.getAttribute('aria-valuenow') + '%';
    });
});

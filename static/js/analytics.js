document.addEventListener('DOMContentLoaded', async function() {
    // Chart.js default configuration for dark theme
    Chart.defaults.color = '#fff';
    Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';

    try {
        // Show loading state
        const chartContainers = document.querySelectorAll('.card-body');
        chartContainers.forEach(container => {
            container.innerHTML = '<div class="text-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        });

        // Fetch analytics data
        const [revenueData, satisfactionData, pipelineData, predictionsData] = await Promise.all([
            fetch('/api/analytics/revenue').then(r => r.json()),
            fetch('/api/analytics/satisfaction').then(r => r.json()),
            fetch('/api/analytics/pipeline').then(r => r.json()),
            fetch('/api/analytics/predictions').then(r => r.json())
        ]);

        // Clear loading state and restore canvas elements
        document.getElementById('pipelineRevenueChart').parentElement.innerHTML = '<canvas id="pipelineRevenueChart"></canvas>';
        document.getElementById('collaborationRevenueChart').parentElement.innerHTML = '<canvas id="collaborationRevenueChart"></canvas>';
        document.getElementById('satisfactionChart').parentElement.innerHTML = '<canvas id="satisfactionChart"></canvas>';
        document.getElementById('pipelineDistributionChart').parentElement.innerHTML = '<canvas id="pipelineDistributionChart"></canvas>';
        document.getElementById('predictiveAnalyticsChart').parentElement.innerHTML = '<canvas id="predictiveAnalyticsChart"></canvas>';

        // Pipeline Revenue Chart
        new Chart(document.getElementById('pipelineRevenueChart'), {
            type: 'bar',
            data: {
                labels: revenueData.stage_revenue.map(d => d.stage),
                datasets: [{
                    label: 'Weighted Revenue ($)',
                    data: revenueData.stage_revenue.map(d => d.weighted_revenue),
                    backgroundColor: 'rgba(54, 162, 235, 0.7)'
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Weighted Pipeline Revenue by Stage'
                    }
                }
            }
        });

        // Collaboration Revenue Chart
        new Chart(document.getElementById('collaborationRevenueChart'), {
            type: 'doughnut',
            data: {
                labels: revenueData.collab_revenue.map(d => d.status),
                datasets: [{
                    data: revenueData.collab_revenue.map(d => d.total_revenue),
                    backgroundColor: [
                        'rgba(75, 192, 192, 0.7)',
                        'rgba(153, 102, 255, 0.7)',
                        'rgba(255, 159, 64, 0.7)'
                    ]
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Collaboration Revenue by Status'
                    }
                }
            }
        });

        // Satisfaction Chart
        new Chart(document.getElementById('satisfactionChart'), {
            type: 'radar',
            data: {
                labels: satisfactionData.map(d => d.company),
                datasets: [{
                    label: 'Partner Satisfaction',
                    data: satisfactionData.map(d => d.satisfaction),
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    r: {
                        min: 0,
                        max: 10,
                        ticks: {
                            stepSize: 2
                        }
                    }
                }
            }
        });

        // Pipeline Distribution Chart
        new Chart(document.getElementById('pipelineDistributionChart'), {
            type: 'bar',
            data: {
                labels: pipelineData.map(d => d.stage),
                datasets: [{
                    label: 'Number of Opportunities',
                    data: pipelineData.map(d => d.count),
                    backgroundColor: 'rgba(255, 206, 86, 0.7)',
                    yAxisID: 'y'
                }, {
                    label: 'Total Value ($)',
                    data: pipelineData.map(d => d.total_value),
                    backgroundColor: 'rgba(75, 192, 192, 0.7)',
                    yAxisID: 'y1'
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Pipeline Distribution'
                    }
                },
                scales: {
                    y: {
                        type: 'linear',
                        position: 'left',
                    },
                    y1: {
                        type: 'linear',
                        position: 'right',
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                }
            }
        });

        // Predictive Analytics Chart
        new Chart(document.getElementById('predictiveAnalyticsChart'), {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'Opportunities',
                    data: predictionsData.map(p => ({
                        x: p.expected_revenue,
                        y: p.success_rate,
                        label: p.title
                    })),
                    backgroundColor: 'rgba(54, 162, 235, 0.7)'
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Success Rate vs Expected Revenue'
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const point = context.raw;
                                return `${point.label}: ${point.y}% success rate, $${point.x.toLocaleString()} revenue`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'linear',
                        position: 'bottom',
                        title: {
                            display: true,
                            text: 'Expected Revenue ($)'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Predicted Success Rate (%)'
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error loading analytics:', error);
        const chartContainers = document.querySelectorAll('.card-body');
        chartContainers.forEach(container => {
            container.innerHTML = '<div class="alert alert-danger">Error loading chart data. Please try again later.</div>';
        });
    }
});

// Export report functionality
async function exportReport() {
    const exportButton = document.querySelector('button[onclick="exportReport()"]');
    const originalText = exportButton.textContent;
    
    try {
        // Show loading state
        exportButton.disabled = true;
        exportButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Exporting...';
        
        const response = await fetch('/export-report', {
            method: 'GET',
            headers: {
                'Accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Export failed');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = 'collaboration_analytics_report.xlsx';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        
        // Show success message
        const toast = new bootstrap.Toast(createToast('Success', 'Report exported successfully!', 'success'));
        toast.show();
    } catch (error) {
        console.error('Export error:', error);
        // Show error message
        const toast = new bootstrap.Toast(createToast('Error', error.message || 'Failed to export report. Please try again.', 'danger'));
        toast.show();
    } finally {
        // Restore button state
        exportButton.disabled = false;
        exportButton.textContent = originalText;
    }
}

// Export executive report functionality
async function exportExecutiveReport() {
    const format = window.confirm('Click OK for PDF format, or Cancel for Excel format') ? 'pdf' : 'excel';
    const exportButton = document.querySelector('button[onclick="exportExecutiveReport()"]');
    const originalText = exportButton.textContent;
    
    try {
        // Show loading state
        exportButton.disabled = true;
        exportButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Exporting...';
        
        const response = await fetch(`/export-executive-report?format=${format}`, {
            method: 'GET',
            headers: {
                'Accept': format === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Export failed');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `executive_report.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        
        // Show success message
        const toast = new bootstrap.Toast(createToast('Success', 'Executive report exported successfully!', 'success'));
        toast.show();
    } catch (error) {
        console.error('Export error:', error);
        // Show error message
        const toast = new bootstrap.Toast(createToast('Error', error.message || 'Failed to export executive report. Please try again.', 'danger'));
        toast.show();
    } finally {
        // Restore button state
        exportButton.disabled = false;
        exportButton.textContent = originalText;
    }
}

// Helper function to create toast notifications
function createToast(title, message, type = 'success') {
    const toastContainer = document.getElementById('toastContainer') || createToastContainer();
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <strong>${title}</strong><br>
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    return toast;
}

// Helper function to create toast container
function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    document.body.appendChild(container);
    return container;
}

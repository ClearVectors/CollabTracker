document.addEventListener('DOMContentLoaded', async function() {
    // Chart.js default configuration for dark theme
    Chart.defaults.color = '#fff';
    Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';

    // Show loading state for all charts
    const chartContainers = [
        'pipelineRevenueChart',
        'collaborationRevenueChart',
        'satisfactionChart',
        'pipelineDistributionChart'
    ].map(id => document.getElementById(id));

    chartContainers.forEach(container => {
        container.style.opacity = '0.5';
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'text-center position-absolute top-50 start-50 translate-middle';
        loadingDiv.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';
        container.parentElement.style.position = 'relative';
        container.parentElement.appendChild(loadingDiv);
    });

    try {
        // Fetch analytics data with timeout and error handling
        const fetchWithTimeout = async (url, timeout = 5000) => {
            const controller = new AbortController();
            const id = setTimeout(() => controller.abort(), timeout);
            try {
                const response = await fetch(url, { signal: controller.signal });
                clearTimeout(id);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();
                return data;
            } catch (error) {
                clearTimeout(id);
                throw error;
            }
        };

        const [revenueData, satisfactionData, pipelineData] = await Promise.all([
            fetchWithTimeout('/api/analytics/revenue'),
            fetchWithTimeout('/api/analytics/satisfaction'),
            fetchWithTimeout('/api/analytics/pipeline')
        ]);

        // Validate data before rendering
        const validateData = (data, type) => {
            switch(type) {
                case 'revenue':
                    return data && data.stage_revenue && Array.isArray(data.stage_revenue) &&
                           data.collab_revenue && Array.isArray(data.collab_revenue);
                case 'satisfaction':
                    return Array.isArray(data) && data.length > 0;
                case 'pipeline':
                    return Array.isArray(data) && data.every(d => 
                        typeof d.stage === 'string' && 
                        typeof d.count === 'number' &&
                        typeof d.total_value === 'number'
                    );
                default:
                    return false;
            }
        };

        if (!validateData(revenueData, 'revenue')) {
            throw new Error('Invalid revenue data structure');
        }

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
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                return `Revenue: $${context.raw.toLocaleString()}`;
                            }
                        }
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
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                return `Revenue: $${context.raw.toLocaleString()}`;
                            }
                        }
                    }
                }
            }
        });

        if (!validateData(satisfactionData, 'satisfaction')) {
            throw new Error('Invalid satisfaction data structure');
        }

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

        if (!validateData(pipelineData, 'pipeline')) {
            throw new Error('Invalid pipeline data structure');
        }

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
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const dataset = context.dataset;
                                const value = context.raw;
                                if (dataset.label === 'Total Value ($)') {
                                    return `${dataset.label}: $${value.toLocaleString()}`;
                                }
                                return `${dataset.label}: ${value}`;
                            }
                        }
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

        // Remove loading states
        chartContainers.forEach(container => {
            container.style.opacity = '1';
            const loadingDiv = container.parentElement.querySelector('.spinner-border').parentElement;
            loadingDiv.remove();
        });

    } catch (error) {
        console.error('Error loading analytics:', error);
        
        // Show error message for each chart
        chartContainers.forEach(container => {
            container.style.opacity = '0.3';
            const loadingDiv = container.parentElement.querySelector('.spinner-border')?.parentElement;
            if (loadingDiv) loadingDiv.remove();
            
            const errorDiv = document.createElement('div');
            errorDiv.className = 'text-center position-absolute top-50 start-50 translate-middle text-danger';
            errorDiv.innerHTML = '<i class="bi bi-exclamation-triangle"></i> Failed to load chart data';
            container.parentElement.appendChild(errorDiv);
        });

        // Show error toast
        const toastContainer = document.createElement('div');
        toastContainer.className = 'position-fixed bottom-0 end-0 p-3';
        toastContainer.innerHTML = `
            <div class="toast align-items-center text-bg-danger border-0" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">
                        Failed to load analytics data. Please try refreshing the page.
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;
        document.body.appendChild(toastContainer);
        const toast = new bootstrap.Toast(toastContainer.querySelector('.toast'));
        toast.show();
    }
});

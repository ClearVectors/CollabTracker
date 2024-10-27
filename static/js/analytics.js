document.addEventListener('DOMContentLoaded', async function() {
    // Chart.js default configuration for dark theme
    Chart.defaults.color = '#fff';
    Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';

    // Fetch analytics data
    const [revenueData, satisfactionData, pipelineData] = await Promise.all([
        fetch('/api/analytics/revenue').then(r => r.json()),
        fetch('/api/analytics/satisfaction').then(r => r.json()),
        fetch('/api/analytics/pipeline').then(r => r.json())
    ]);

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
});

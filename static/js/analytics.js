document.addEventListener('DOMContentLoaded', async function() {
    // Chart.js default configuration for dark theme
    Chart.defaults.color = '#fff';
    Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';

    // Fetch analytics data
    const [revenueData, satisfactionData, pipelineData, predictionsData] = await Promise.all([
        fetch('/api/analytics/revenue').then(r => r.json()),
        fetch('/api/analytics/satisfaction').then(r => r.json()),
        fetch('/api/analytics/pipeline').then(r => r.json()),
        fetch('/api/analytics/predictions').then(r => r.json())
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
});

// Export report functionality
async function exportReport() {
    try {
        const response = await fetch('/export-report', {
            method: 'GET',
            headers: {
                'Accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
        });
        
        if (!response.ok) throw new Error('Export failed');
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = 'collaboration_analytics_report.xlsx';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
    } catch (error) {
        console.error('Export error:', error);
        alert('Failed to export report. Please try again.');
    }
}

// Export executive report functionality
async function exportExecutiveReport() {
    try {
        const format = window.confirm('Click OK for PDF format, or Cancel for Excel format') ? 'pdf' : 'excel';
        const response = await fetch(`/export-executive-report?format=${format}`, {
            method: 'GET',
            headers: {
                'Accept': format === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
        });
        
        if (!response.ok) throw new Error('Export failed');
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `executive_report.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
    } catch (error) {
        console.error('Export error:', error);
        alert('Failed to export executive report. Please try again.');
    }
}

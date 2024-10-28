document.addEventListener('DOMContentLoaded', async function() {
    // Chart.js default configuration for dark theme
    Chart.defaults.color = '#fff';
    Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';
    
    // Enhanced tooltip configuration
    const tooltipConfig = {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#fff',
        bodyColor: '#fff',
        padding: 12,
        boxPadding: 6
    };

    // Custom animation configuration
    const animationConfig = {
        duration: 1000,
        easing: 'easeInOutQuart'
    };

    // Connect to WebSocket for real-time updates
    const socket = io();
    
    // Fetch initial analytics data
    const [revenueData, satisfactionData, pipelineData] = await Promise.all([
        fetch('/api/analytics/revenue').then(r => r.json()),
        fetch('/api/analytics/satisfaction').then(r => r.json()),
        fetch('/api/analytics/pipeline').then(r => r.json())
    ]);

    // Initialize charts with interactive features
    const pipelineRevenueChart = new Chart(document.getElementById('pipelineRevenueChart'), {
        type: 'bar',
        data: {
            labels: revenueData.stage_revenue.map(d => d.stage),
            datasets: [{
                label: 'Weighted Revenue ($)',
                data: revenueData.stage_revenue.map(d => d.weighted_revenue),
                backgroundColor: 'rgba(54, 162, 235, 0.7)',
                borderWidth: 2,
                borderColor: 'rgba(54, 162, 235, 1)'
            }]
        },
        options: {
            responsive: true,
            animation: animationConfig,
            plugins: {
                title: {
                    display: true,
                    text: 'Weighted Pipeline Revenue by Stage'
                },
                tooltip: {
                    ...tooltipConfig,
                    callbacks: {
                        label: function(context) {
                            return `Revenue: $${new Intl.NumberFormat().format(context.raw)}`;
                        }
                    }
                },
                legend: {
                    position: 'bottom'
                }
            },
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    const stage = revenueData.stage_revenue[elements[0].index].stage;
                    filterChartsByStage(stage);
                }
            }
        }
    });

    const collaborationRevenueChart = new Chart(document.getElementById('collaborationRevenueChart'), {
        type: 'doughnut',
        data: {
            labels: revenueData.collab_revenue.map(d => d.status),
            datasets: [{
                data: revenueData.collab_revenue.map(d => d.total_revenue),
                backgroundColor: [
                    'rgba(75, 192, 192, 0.7)',
                    'rgba(153, 102, 255, 0.7)',
                    'rgba(255, 159, 64, 0.7)'
                ],
                borderWidth: 2,
                borderColor: [
                    'rgba(75, 192, 192, 1)',
                    'rgba(153, 102, 255, 1)',
                    'rgba(255, 159, 64, 1)'
                ]
            }]
        },
        options: {
            responsive: true,
            animation: animationConfig,
            plugins: {
                title: {
                    display: true,
                    text: 'Collaboration Revenue by Status'
                },
                tooltip: {
                    ...tooltipConfig,
                    callbacks: {
                        label: function(context) {
                            return `${context.label}: $${new Intl.NumberFormat().format(context.raw)}`;
                        }
                    }
                },
                legend: {
                    position: 'bottom',
                    onClick: (event, legendItem) => {
                        filterChartsByStatus(legendItem.text);
                    }
                }
            }
        }
    });

    const satisfactionChart = new Chart(document.getElementById('satisfactionChart'), {
        type: 'radar',
        data: {
            labels: satisfactionData.map(d => d.company),
            datasets: [{
                label: 'Partner Satisfaction',
                data: satisfactionData.map(d => d.satisfaction),
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                borderColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 2,
                pointBackgroundColor: 'rgba(255, 99, 132, 1)',
                pointHoverRadius: 8
            }]
        },
        options: {
            responsive: true,
            animation: animationConfig,
            scales: {
                r: {
                    min: 0,
                    max: 10,
                    ticks: {
                        stepSize: 2
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    pointLabels: {
                        font: {
                            size: 12
                        }
                    }
                }
            },
            plugins: {
                tooltip: {
                    ...tooltipConfig,
                    callbacks: {
                        label: function(context) {
                            return `Satisfaction Score: ${context.raw}/10`;
                        }
                    }
                },
                legend: {
                    position: 'bottom'
                }
            }
        }
    });

    const pipelineDistributionChart = new Chart(document.getElementById('pipelineDistributionChart'), {
        type: 'bar',
        data: {
            labels: pipelineData.map(d => d.stage),
            datasets: [{
                label: 'Number of Opportunities',
                data: pipelineData.map(d => d.count),
                backgroundColor: 'rgba(255, 206, 86, 0.7)',
                borderColor: 'rgba(255, 206, 86, 1)',
                borderWidth: 2,
                yAxisID: 'y'
            }, {
                label: 'Total Value ($)',
                data: pipelineData.map(d => d.total_value),
                backgroundColor: 'rgba(75, 192, 192, 0.7)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 2,
                yAxisID: 'y1'
            }]
        },
        options: {
            responsive: true,
            animation: animationConfig,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Pipeline Distribution'
                },
                tooltip: {
                    ...tooltipConfig,
                    callbacks: {
                        label: function(context) {
                            if (context.datasetIndex === 0) {
                                return `Opportunities: ${context.raw}`;
                            }
                            return `Value: $${new Intl.NumberFormat().format(context.raw)}`;
                        }
                    }
                },
                legend: {
                    position: 'bottom'
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    position: 'left',
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
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

    // Handle real-time updates via WebSocket
    socket.on('analytics_update', (data) => {
        if (data.type === 'revenue') {
            updateRevenueCharts(data);
        } else if (data.type === 'satisfaction') {
            updateSatisfactionChart(data);
        } else if (data.type === 'pipeline') {
            updatePipelineChart(data);
        }
    });

    // Cross-chart filtering functions
    function filterChartsByStage(stage) {
        // Highlight selected stage across charts
        const charts = [pipelineRevenueChart, pipelineDistributionChart];
        charts.forEach(chart => {
            chart.data.datasets.forEach(dataset => {
                dataset.backgroundColor = dataset.data.map((_, index) => 
                    chart.data.labels[index] === stage ? 
                    dataset.borderColor : 
                    dataset.backgroundColor
                );
            });
            chart.update();
        });
    }

    function filterChartsByStatus(status) {
        collaborationRevenueChart.data.datasets[0].backgroundColor = 
            collaborationRevenueChart.data.labels.map(label => 
                label === status ? 
                collaborationRevenueChart.data.datasets[0].borderColor[
                    collaborationRevenueChart.data.labels.indexOf(label)
                ] : 
                'rgba(75, 75, 75, 0.7)'
            );
        collaborationRevenueChart.update();
    }

    // Chart update functions for WebSocket events
    function updateRevenueCharts(data) {
        if (data.stage_revenue) {
            pipelineRevenueChart.data.labels = data.stage_revenue.map(d => d.stage);
            pipelineRevenueChart.data.datasets[0].data = data.stage_revenue.map(d => d.weighted_revenue);
            pipelineRevenueChart.update();
        }
        if (data.collab_revenue) {
            collaborationRevenueChart.data.labels = data.collab_revenue.map(d => d.status);
            collaborationRevenueChart.data.datasets[0].data = data.collab_revenue.map(d => d.total_revenue);
            collaborationRevenueChart.update();
        }
    }

    function updateSatisfactionChart(data) {
        satisfactionChart.data.labels = data.map(d => d.company);
        satisfactionChart.data.datasets[0].data = data.map(d => d.satisfaction);
        satisfactionChart.update();
    }

    function updatePipelineChart(data) {
        pipelineDistributionChart.data.labels = data.map(d => d.stage);
        pipelineDistributionChart.data.datasets[0].data = data.map(d => d.count);
        pipelineDistributionChart.data.datasets[1].data = data.map(d => d.total_value);
        pipelineDistributionChart.update();
    }
});

document.addEventListener('DOMContentLoaded', function() {
    // Connect to WebSocket server
    const socket = io();

    socket.on('connect', () => {
        console.log('Connected to WebSocket server');
    });

    socket.on('collaboration_updated', (data) => {
        if (data.action === 'new') {
            // Update collaborations grid if we're on the dashboard
            const collaborationsGrid = document.getElementById('collaborationsGrid');
            if (collaborationsGrid) {
                const newCard = createCollaborationCard(data.collaboration);
                collaborationsGrid.insertAdjacentHTML('afterbegin', newCard);
            }
        }
    });

    socket.on('opportunity_updated', (data) => {
        if (data.action === 'new') {
            // Update opportunities view if we're on the pipeline page
            const stageContainer = document.querySelector(`[data-stage="${data.opportunity.stage}"]`);
            if (stageContainer) {
                const newCard = createOpportunityCard(data.opportunity);
                stageContainer.insertAdjacentHTML('afterbegin', newCard);
            }
        } else if (data.action === 'update') {
            // Update existing opportunity card
            const card = document.querySelector(`[data-id="${data.opportunity.id}"]`);
            if (card) {
                updateOpportunityCard(card, data.opportunity);
            }
        }
    });

    socket.on('document_added', (data) => {
        // Update documents list if we're on the documents page
        const documentsList = document.querySelector('.list-group');
        if (documentsList) {
            const newDoc = createDocumentListItem(data.document);
            documentsList.insertAdjacentHTML('afterbegin', newDoc);
        }
    });

    // Helper functions to create HTML elements
    function createCollaborationCard(collaboration) {
        return `
            <div class="col-md-6 mb-3">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">${collaboration.title}</h5>
                        <h6 class="card-subtitle mb-2 text-muted">${collaboration.company_name}</h6>
                        <div class="progress mb-2">
                            <div class="progress-bar" role="progressbar" style="width: ${collaboration.kpi_satisfaction * 10}%">
                                Satisfaction: ${collaboration.kpi_satisfaction}/10
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    function createOpportunityCard(opportunity) {
        return `
            <div class="card mb-2 opportunity-card" data-id="${opportunity.id}">
                <div class="card-body">
                    <h6 class="card-title">${opportunity.title}</h6>
                    <p class="card-text">${opportunity.company_name}</p>
                    <div class="d-flex justify-content-between align-items-center">
                        <span class="badge bg-success">$${new Intl.NumberFormat().format(opportunity.expected_revenue)}</span>
                        <span class="badge bg-info">${opportunity.probability}%</span>
                    </div>
                </div>
            </div>
        `;
    }

    function updateOpportunityCard(card, opportunity) {
        const probabilityBadge = card.querySelector('.badge.bg-info');
        if (probabilityBadge) {
            probabilityBadge.textContent = `${opportunity.probability}%`;
        }
        
        // Move card to new stage container if stage changed
        const currentStage = card.closest('.pipeline-stage');
        const newStage = document.querySelector(`[data-stage="${opportunity.stage}"]`);
        if (currentStage && newStage && currentStage !== newStage) {
            newStage.appendChild(card);
        }
    }

    function createDocumentListItem(document) {
        return `
            <div class="list-group-item">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="mb-1">${document.title}</h6>
                        <small class="text-muted d-block">Type: ${document.file_type}</small>
                        <small class="text-muted d-block">Version: ${document.version}</small>
                        <small class="text-muted">Uploaded: ${document.upload_date}</small>
                    </div>
                    <a href="/document/${document.id}/download" class="btn btn-sm btn-secondary">
                        <i class="bi bi-download"></i> Download
                    </a>
                </div>
            </div>
        `;
    }
});

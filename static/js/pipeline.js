document.addEventListener('DOMContentLoaded', function() {
    // Handle opportunity form submission
    const opportunityForm = document.getElementById('opportunityForm');
    if (opportunityForm) {
        opportunityForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(opportunityForm);
            
            try {
                const response = await fetch('/opportunity/new', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                
                if (data.success) {
                    window.location.reload();
                } else {
                    alert('Error creating opportunity: ' + data.error);
                }
            } catch (error) {
                console.error('Error:', error);
            }
        });
    }

    // Drag and Drop functionality
    const cards = document.querySelectorAll('.opportunity-card');
    const stages = document.querySelectorAll('.pipeline-stage');

    // Add drag event listeners to cards
    cards.forEach(card => {
        card.setAttribute('draggable', true);
        
        card.addEventListener('dragstart', (e) => {
            e.dataTransfer.setData('text/plain', card.dataset.id);
            card.classList.add('dragging');
        });

        card.addEventListener('dragend', () => {
            card.classList.remove('dragging');
        });
    });

    // Add drop event listeners to stages
    stages.forEach(stage => {
        stage.addEventListener('dragover', (e) => {
            e.preventDefault();
            stage.classList.add('drag-over');
        });

        stage.addEventListener('dragleave', () => {
            stage.classList.remove('drag-over');
        });

        stage.addEventListener('drop', async (e) => {
            e.preventDefault();
            stage.classList.remove('drag-over');
            
            const oppId = e.dataTransfer.getData('text/plain');
            const newStage = stage.dataset.stage;
            const card = document.querySelector(`[data-id="${oppId}"]`);

            if (card) {
                try {
                    const response = await fetch(`/opportunity/${oppId}/update`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                        },
                        body: new URLSearchParams({
                            'stage': newStage,
                            'probability': getProbabilityForStage(newStage),
                            'next_meeting_date': card.querySelector('[data-next-meeting]')?.dataset.nextMeeting || '',
                            'notes': card.querySelector('[data-notes]')?.dataset.notes || ''
                        })
                    });

                    const data = await response.json();
                    if (data.success) {
                        stage.appendChild(card);
                        updateCardProbability(card, newStage);
                    } else {
                        alert('Error updating opportunity stage: ' + data.error);
                    }
                } catch (error) {
                    console.error('Error:', error);
                }
            }
        });
    });

    // Helper function to get probability based on stage
    function getProbabilityForStage(stage) {
        const probabilities = {
            'Lead': 20,
            'Meeting': 40,
            'Proposal': 60,
            'Negotiation': 80,
            'Closed': 100
        };
        return probabilities[stage] || 0;
    }

    // Update card probability badge
    function updateCardProbability(card, stage) {
        const probability = getProbabilityForStage(stage);
        const badge = card.querySelector('.badge.bg-info');
        if (badge) {
            badge.textContent = `${probability}%`;
        }
    }
});

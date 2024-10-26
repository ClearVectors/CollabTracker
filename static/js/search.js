document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    let timeoutId;

    searchInput.addEventListener('input', function(e) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => performSearch(e.target.value), 300);
    });

    async function performSearch(query) {
        if (query.length < 2) return;
        
        try {
            const response = await fetch(`/search?q=${encodeURIComponent(query)}`);
            const results = await response.json();
            
            const companiesList = document.querySelector('.list-group');
            if (companiesList) {
                companiesList.innerHTML = results.map(company => `
                    <a href="/company/${company.id}" class="list-group-item list-group-item-action">
                        ${company.name}
                        <span class="badge bg-secondary float-end">${company.industry}</span>
                    </a>
                `).join('');
            }
        } catch (error) {
            console.error('Search error:', error);
        }
    }
});

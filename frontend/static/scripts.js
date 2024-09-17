document.addEventListener('DOMContentLoaded', () => {
    const searchForm = document.getElementById('search-form');
    const collectionSearchForm = document.getElementById('collection-search-form');

    // Function to display results
    const displayResults = (data, resultsDiv) => {
        if (data.results && data.results.length > 0) {
            resultsDiv.innerHTML = data.results.map(item => `
                <div class="result">
                    <h3>${item.character_name}</h3>
                    <p>Anime: ${item.anime_name}</p>
                    <p>Rarity: ${item.rarity}</p>
                    <img src="${item.image_url}" alt="${item.character_name}">
                </div>
            `).join('');
        } else {
            resultsDiv.innerHTML = 'No results found.';
        }
    };

    // Handle search form submission
    searchForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const query = document.getElementById('search-query').value;
        const resultsDiv = document.getElementById('search-results');
        resultsDiv.innerHTML = 'Loading...';

        try {
            const response = await fetch(`/waifus/search?query=${encodeURIComponent(query)}`);
            const data = await response.json();
            displayResults(data, resultsDiv);
        } catch (error) {
            resultsDiv.innerHTML = 'Error fetching results.';
            console.error('Error:', error);
        }
    });

    // Handle collection search form submission
    collectionSearchForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const query = document.getElementById('collection-query').value;
        const resultsDiv = document.getElementById('collection-results');
        resultsDiv.innerHTML = 'Loading...';

        try {
            const response = await fetch(`/waifus/search?query=${encodeURIComponent(query)}`);
            const data = await response.json();
            displayResults(data, resultsDiv);
        } catch (error) {
            resultsDiv.innerHTML = 'Error fetching results.';
            console.error('Error:', error);
        }
    });
});

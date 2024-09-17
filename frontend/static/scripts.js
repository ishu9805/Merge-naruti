document.addEventListener('DOMContentLoaded', () => {
    const searchForm = document.getElementById('search-form');
    const collectionSearchForm = document.getElementById('collection-search-form');

    // Handle search form submission
    searchForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const query = document.getElementById('search-query').value;
        const resultsDiv = document.getElementById('search-results');
        resultsDiv.innerHTML = 'Loading...';

        try {
            const response = await fetch(`https:weblearningnaruto-8d06c84d5de0.herokuapp.com/api/search?query=${encodeURIComponent(query)}`);
            const data = await response.json();
            resultsDiv.innerHTML = data.results.map(item => `<p>${item.name} - ${item.anime}</p>`).join('');
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
            const response = await fetch(`https://weblearningnaruto-8d06c84d5de0.herokuapp.com/api/collection?query=${encodeURIComponent(query)}`);
            const data = await response.json();
            resultsDiv.innerHTML = data.results.map(item => `<p>${item.name} - ${item.anime} - ${item.rarity}</p>`).join('');
        } catch (error) {
            resultsDiv.innerHTML = 'Error fetching results.';
            console.error('Error:', error);
        }
    });
});

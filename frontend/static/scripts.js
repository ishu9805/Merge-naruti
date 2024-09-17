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
            const response = await fetch(`https://weblearningnaruto-8d06c84d5de0.herokuapp.com/waifus/${encodeURIComponent(query)}`);
            const data = await response.json();
            
            if (data.error) {
                resultsDiv.innerHTML = 'No results found.';
            } else {
                resultsDiv.innerHTML = `
                    <p>Character Name: ${data.character_name}</p>
                    <p>Anime Name: ${data.anime_name}</p>
                    <p><img src="${data.image_url}" alt="${data.character_name}" style="max-width: 200px;"></p>
                `;
            }
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
            const response = await fetch(`https://weblearningnaruto-8d06c84d5de0.herokuapp.com/waifus/search?query=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            if (data.error) {
                resultsDiv.innerHTML = 'No results found.';
            } else {
                resultsDiv.innerHTML = data.map(item => `
                    <p>Character Name: ${item.character_name} - Anime Name: ${item.anime_name} - Rarity: ${item.rarity}</p>
                    <p><img src="${item.image_url}" alt="${item.character_name}" style="max-width: 200px;"></p>
                `).join('');
            }
        } catch (error) {
            resultsDiv.innerHTML = 'Error fetching results.';
            console.error('Error:', error);
        }
    });
});

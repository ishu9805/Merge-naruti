document.addEventListener('DOMContentLoaded', () => {
    const searchForm = document.getElementById('search-form');
    const collectionResultsDiv = document.getElementById('collection-results');
    const prevPageButton = document.getElementById('prev-page');
    const nextPageButton = document.getElementById('next-page');
    let currentPage = 1;
    const pageSize = 15;

    const updatePaginationButtons = (hasNextPage) => {
        prevPageButton.disabled = currentPage === 1;
        nextPageButton.disabled = !hasNextPage;
    };

    const loadCharacters = async (page) => {
        collectionResultsDiv.innerHTML = 'Loading...';
        try {
            const response = await fetch(`/waifus?page=${page}&size=${pageSize}`);
            const data = await response.json();
            if (data.results && data.results.length > 0) {
                collectionResultsDiv.innerHTML = data.results.map(item => `
                    <div class="character-item">
                        <img src="${item.image_url}" alt="${item.character_name}">
                        <h3>${item.character_name}</h3>
                        <p>Anime: ${item.anime_name}</p>
                        <p>Rarity: ${item.rarity}</p>
                        <p>ID: ${item.id}</p>
                    </div>
                `).join('');
                updatePaginationButtons(data.hasNextPage);
            } else {
                collectionResultsDiv.innerHTML = 'No characters found.';
                updatePaginationButtons(false);
            }
        } catch (error) {
            collectionResultsDiv.innerHTML = 'Error fetching results.';
            console.error('Error:', error);
        }
    };

    prevPageButton.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            loadCharacters(currentPage);
        }
    });

    nextPageButton.addEventListener('click', () => {
        currentPage++;
        loadCharacters(currentPage);
    });

    // Initial load
    loadCharacters(currentPage);

    // Handle search form submission
    searchForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const query = document.getElementById('search-query').value;
        const resultsDiv = document.getElementById('search-results');
        resultsDiv.innerHTML = 'Loading...';

        try {
            const response = await fetch(`/waifus/search?query=${encodeURIComponent(query)}`);
            const data = await response.json();

            if (data.results && data.results.length > 0) {
                resultsDiv.innerHTML = data.results.map(item => `
                    <div class="character-item">
                        <img src="${item.image_url}" alt="${item.character_name}">
                        <h3>${item.character_name}</h3>
                        <p>Anime: ${item.anime_name}</p>
                        <p>Rarity: ${item.rarity}</p>
                        <p>ID: ${item.id}</p>
                    </div>
                `).join('');
            } else {
                resultsDiv.innerHTML = 'No results found.';
            }
        } catch (error) {
            resultsDiv.innerHTML = 'Error fetching results.';
            console.error('Error:', error);
        }
    });
});

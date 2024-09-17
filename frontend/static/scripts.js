document.addEventListener('DOMContentLoaded', () => {
    const searchForm = document.getElementById('search-form');
    const searchResultsDiv = document.getElementById('search-results');
    const prevPageButton = document.getElementById('prev-page');
    const nextPageButton = document.getElementById('next-page');
    let currentPage = 1;
    const pageSize = 15;

    // Array of background images
    const backgroundImages = [
        'https://files.catbox.moe/9jbemn.jpg',
        'https://files.catbox.moe/l5g4xp.jpg',
        'https://files.catbox.moe/7tdou5.jpg',
        'https://files.catbox.moe/4sgb37.jpg',
        'https://files.catbox.moe/qggqe3.jpg'
    ];

    // Set a random background image
    document.body.style.backgroundImage = `url('${backgroundImages[Math.floor(Math.random() * backgroundImages.length)]}')`;

    const updatePaginationButtons = (hasNextPage) => {
        prevPageButton.disabled = currentPage === 1;
        nextPageButton.disabled = !hasNextPage;
    };

    const loadCharacters = async (page) => {
        searchResultsDiv.innerHTML = 'Loading...';
        try {
            const response = await fetch(`/waifus?page=${page}&size=${pageSize}`);
            const data = await response.json();
            if (data.results && data.results.length > 0) {
                searchResultsDiv.innerHTML = data.results.map(item => `
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
                searchResultsDiv.innerHTML = 'No characters found.';
                updatePaginationButtons(false);
            }
        } catch (error) {
            searchResultsDiv.innerHTML = 'Error fetching results.';
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
        searchResultsDiv.innerHTML = 'Loading...';

        try {
            const response = await fetch(`/waifus/search?query=${encodeURIComponent(query)}`);
            const data = await response.json();

            if (data.results && data.results.length > 0) {
                searchResultsDiv.innerHTML = data.results.map(item => `
                    <div class="character-item">
                        <img src="${item.image_url}" alt="${item.character_name}">
                        <h3>${item.character_name}</h3>
                        <p>Anime: ${item.anime_name}</p>
                        <p>Rarity: ${item.rarity}</p>
                        <p>ID: ${item.id}</p>
                    </div>
                `).join('');
            } else {
                searchResultsDiv.innerHTML = 'No results found.';
            }
        } catch (error) {
            searchResultsDiv.innerHTML = 'Error fetching results.';
            console.error('Error:', error);
        }
    });
});

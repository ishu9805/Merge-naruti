document.addEventListener('DOMContentLoaded', () => {
    const searchForm = document.getElementById('multi-search-form');
    const searchResultsDiv = document.getElementById('search-results');
    const prevPageButton = document.getElementById('prev-page');
    const nextPageButton = document.getElementById('next-page');
    const appliedFiltersDiv = document.getElementById('applied-filters');
    const modal = document.getElementById('image-popup');
    const modalImg = document.getElementById('popup-image');
    const closeBtn = document.querySelector('.modal .close');
    let currentPage = 1;
    let currentFilters = {};

    // Set background image
    document.body.style.backgroundImage = "url('https://files.catbox.moe/9jbemn.jpg')";

    const updatePaginationButtons = (hasNextPage) => {
        prevPageButton.disabled = currentPage === 1;
        nextPageButton.disabled = !hasNextPage;
    };

    const updateFilters = () => {
        const filters = {};
        const nameQuery = document.getElementById('name-query').value.trim();
        const animeQuery = document.getElementById('anime-query').value.trim();
        const rarityQuery = document.getElementById('rarity-query').value.trim();
        const idQuery = document.getElementById('id-query').value.trim();

        if (nameQuery) filters.name = nameQuery;
        if (animeQuery) filters.anime = animeQuery;
        if (rarityQuery) filters.rarity = rarityQuery;
        if (idQuery) filters.id = idQuery;

        currentFilters = filters;

        appliedFiltersDiv.innerHTML = Object.entries(filters).map(([key, value]) => `
            <span>${key.charAt(0).toUpperCase() + key.slice(1)}: ${value} 
            <button class="remove-filter" data-filter="${key}">x</button></span>
        `).join(' ');
    };

    const loadCharacters = async (page) => {
        searchResultsDiv.innerHTML = 'Loading...';
        const params = new URLSearchParams(currentFilters);
        params.append('page', page);

        try {
            const response = await fetch(`/waifus/search?${params.toString()}`);
            const data = await response.json();

            if (data.results && data.results.length > 0) {
                // Sort by ID
                data.results.sort((a, b) => b.id - a.id);
                searchResultsDiv.innerHTML = data.results.map(item => `
                    <div class="character-item">
                        <img src="${item.image_url}" alt="${item.character_name}" loading="lazy">
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
            searchResultsDiv.innerHTML = 'Error fetching results. Please try again.';
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

    searchForm.addEventListener('submit', (event) => {
        event.preventDefault();
        currentPage = 1; // Reset to first page on search
        updateFilters();
        loadCharacters(currentPage);
    });

    document.addEventListener('click', (event) => {
        if (event.target.classList.contains('remove-filter')) {
            const filterKey = event.target.getAttribute('data-filter');
            document.getElementById(`${filterKey}-query`).value = '';
            updateFilters();
            loadCharacters(currentPage);
        } else if (event.target.tagName === 'IMG' && event.target.closest('.character-item')) {
            // Open modal with image
            modal.style.display = 'block';
            modalImg.src = event.target.src;
        }
    });

    closeBtn.addEventListener('click', () => {
        modal.style.display = 'none';
    });

    window.addEventListener('click', (event) => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });

    // Initial load
    loadCharacters(currentPage);
});

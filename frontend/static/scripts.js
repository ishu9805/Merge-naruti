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
    const pageSize = 15; // This is declared but not used in this script. Consider removing it if not needed.

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

    const updateFilters = () => {
        const filters = [];
        const nameQuery = document.getElementById('name-query').value.trim();
        const animeQuery = document.getElementById('anime-query').value.trim();
        const rarityQuery = document.getElementById('rarity-query').value.trim();
        const idQuery = document.getElementById('id-query').value.trim();

        if (nameQuery) filters.push(`Name: ${nameQuery}`);
        if (animeQuery) filters.push(`Anime: ${animeQuery}`);
        if (rarityQuery) filters.push(`Rarity: ${rarityQuery}`);
        if (idQuery) filters.push(`ID: ${idQuery}`);

        appliedFiltersDiv.innerHTML = filters.map(filter => `
            <span>${filter} <button class="remove-filter" data-filter="${filter}">x</button></span>
        `).join(' ');
    };

    const loadCharacters = async (page) => {
        searchResultsDiv.innerHTML = 'Loading...';
        const nameQuery = document.getElementById('name-query').value.trim();
        const animeQuery = document.getElementById('anime-query').value.trim();
        const rarityQuery = document.getElementById('rarity-query').value.trim();
        const idQuery = document.getElementById('id-query').value.trim();

        try {
            const response = await fetch(`/waifus/search?name=${encodeURIComponent(nameQuery)}&anime=${encodeURIComponent(animeQuery)}&rarity=${encodeURIComponent(rarityQuery)}&id=${encodeURIComponent(idQuery)}`);
            const data = await response.json();

            if (data.results && data.results.length > 0) {
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

    searchForm.addEventListener('submit', (event) => {
        event.preventDefault();
        updateFilters();
        loadCharacters(currentPage);
    });

    document.addEventListener('click', (event) => {
        if (event.target.classList.contains('remove-filter')) {
            const filter = event.target.getAttribute('data-filter');
            const [key, value] = filter.split(': ');
            document.getElementById(`${key.toLowerCase()}-query`).value = '';
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

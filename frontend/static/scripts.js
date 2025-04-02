document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const searchForm = document.getElementById('multi-search-form');
    const searchResults = document.getElementById('search-results');
    const prevPageBtn = document.getElementById('prev-page');
    const nextPageBtn = document.getElementById('next-page');
    const currentPageSpan = document.getElementById('current-page');
    const loadingSpinner = document.getElementById('loading-spinner');
    const noResultsDiv = document.getElementById('no-results');
    const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
    const mainNav = document.querySelector('.main-nav');

    // State
    let currentPage = 1;
    let currentFilters = {};

    // Initialize
    noResultsDiv.style.display = 'flex';
    searchResults.style.display = 'none';

    // Event Listeners
    searchForm.addEventListener('submit', handleSearch);
    prevPageBtn.addEventListener('click', goToPrevPage);
    nextPageBtn.addEventListener('click', goToNextPage);
    mobileMenuBtn.addEventListener('click', toggleMobileMenu);

    // Functions
    async function handleSearch(e) {
        e.preventDefault();
        currentPage = 1;
        updateFilters();
        await loadCharacters();
    }

    function updateFilters() {
        currentFilters = {
            name: document.getElementById('name-query').value.trim(),
            anime: document.getElementById('anime-query').value.trim(),
            rarity: document.getElementById('rarity-query').value.trim(),
            id: document.getElementById('id-query').value.trim()
        };
    }

    async function loadCharacters() {
        loadingSpinner.style.display = 'flex';
        noResultsDiv.style.display = 'none';
        searchResults.style.display = 'none';

        try {
            const params = new URLSearchParams();
            if (currentFilters.name) params.append('name', currentFilters.name);
            if (currentFilters.anime) params.append('anime', currentFilters.anime);
            if (currentFilters.rarity) params.append('rarity', currentFilters.rarity);
            if (currentFilters.id) params.append('id', currentFilters.id);

            const response = await fetch(`/waifus/search?${params.toString()}`);
            const data = await response.json();

            if (data.results?.length) {
                displayResults(data.results);
            } else {
                showNoResults();
            }
        } catch (error) {
            console.error('Error:', error);
            showNoResults('Error loading characters');
        } finally {
            loadingSpinner.style.display = 'none';
        }
    }

                                                 
    // Update your displayResults function to use the new HTML structure
    function displayResults(characters) {
        searchResults.innerHTML = '';
        characters.sort((a, b) => b.id - a.id).forEach(character => {
            const card = document.createElement('div');
            card.className = 'character-card';
            card.innerHTML = `
                <div class="character-image-container">
                     <img src="${character.image_url}" 
                         alt="${character.character_name}" 
                         class="character-image" 
                         loading="lazy">
                </div>
                <div class="character-info">
                    <h3 class="character-name">${character.character_name}</h3>
                    <div>
                        v<p class="character-detail"><i class="fas fa-film"></i> ${character.anime_name}</p>
                        <p class="character-detail"><i class="fas fa-star"></i> ${character.rarity}</p>
                    </div>
                </div>
            `;
            searchResults.appendChild(card);
            });
    searchResults.style.display = 'grid';
    }
    
    function showNoResults(message = 'No characters found') {
        noResultsDiv.innerHTML = `
            <i class="fas fa-search"></i>
            <p>${message}</p>
        `;
        noResultsDiv.style.display = 'flex';
    }

    function goToPrevPage() {
        if (currentPage > 1) {
            currentPage--;
            loadCharacters();
        }
    }

    function goToNextPage() {
        currentPage++;
        loadCharacters();
    }

    function toggleMobileMenu() {
        mainNav.classList.toggle('active');
    }
});

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const searchForm = document.getElementById('multi-search-form');
    const searchResultsDiv = document.getElementById('search-results');
    const prevPageButton = document.getElementById('prev-page');
    const nextPageButton = document.getElementById('next-page');
    const currentPageSpan = document.getElementById('current-page');
    const appliedFiltersDiv = document.getElementById('applied-filters');
    const loadingSpinner = document.getElementById('loading-spinner');
    const modal = document.getElementById('character-modal');
    const modalImage = document.getElementById('modal-character-image');
    const modalName = document.getElementById('modal-character-name');
    const modalAnime = document.getElementById('modal-anime-name');
    const modalRarity = document.getElementById('modal-rarity');
    const modalId = document.getElementById('modal-character-id');
    const closeModal = document.querySelector('.close-modal');
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const mainNav = document.querySelector('.main-nav');
    
    // State variables
    let currentPage = 1;
    let currentFilters = {};
    const backgroundImages = [
        'https://files.catbox.moe/9jbemn.jpg',
        'https://files.catbox.moe/l5g4xp.jpg',
        'https://files.catbox.moe/7tdou5.jpg',
        'https://files.catbox.moe/4sgb37.jpg',
        'https://files.catbox.moe/qggqe3.jpg'
    ];
    
    // Initialize the page
    initPage();
    
    function initPage() {
        // Set random background
        setRandomBackground();
        
        // Load initial characters
        loadCharacters(currentPage);
        
        // Set up event listeners
        setupEventListeners();
    }
    
    function setRandomBackground() {
        const randomImage = backgroundImages[Math.floor(Math.random() * backgroundImages.length)];
        document.body.style.backgroundImage = `url('${randomImage}')`;
    }
    
    function setupEventListeners() {
        // Form submission
        searchForm.addEventListener('submit', (e) => {
            e.preventDefault();
            currentPage = 1;
            updateCurrentFilters();
            updateFiltersDisplay();
            loadCharacters(currentPage);
        });
        
        // Pagination buttons
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
        
        // Filter removal
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('remove-filter')) {
                const filterType = e.target.dataset.filterType;
                clearFilter(filterType);
            }
        });
        
        // Modal interactions
        closeModal.addEventListener('click', () => {
            modal.style.display = 'none';
        });
        
        window.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        });
        
        // Mobile menu toggle
        mobileMenuToggle.addEventListener('click', () => {
            mainNav.classList.toggle('active');
        });
    }
    
    function updateCurrentFilters() {
        currentFilters = {
            name: document.getElementById('name-query').value.trim(),
            anime: document.getElementById('anime-query').value.trim(),
            rarity: document.getElementById('rarity-query').value.trim(),
            id: document.getElementById('id-query').value.trim()
        };
    }
    
    function updateFiltersDisplay() {
        const activeFilters = Object.entries(currentFilters)
            .filter(([_, value]) => value !== '')
            .map(([key, value]) => ({ type: key, value }));
        
        if (activeFilters.length === 0) {
            appliedFiltersDiv.innerHTML = '';
            return;
        }
        
        appliedFiltersDiv.innerHTML = activeFilters.map(filter => `
            <div class="filter-tag">
                ${filter.type}: ${filter.value}
                <button class="remove-filter" data-filter-type="${filter.type}">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `).join('');
    }
    
    function clearFilter(filterType) {
        document.getElementById(`${filterType}-query`).value = '';
        currentFilters[filterType] = '';
        updateFiltersDisplay();
        currentPage = 1;
        loadCharacters(currentPage);
    }
    
    async function loadCharacters(page) {
        // Show loading spinner
        loadingSpinner.style.display = 'flex';
        searchResultsDiv.innerHTML = '';
        
        // Update current page display
        currentPageSpan.textContent = page;
        
        try {
            // Build query parameters
            const params = new URLSearchParams();
            if (currentFilters.name) params.append('name', currentFilters.name);
            if (currentFilters.anime) params.append('anime', currentFilters.anime);
            if (currentFilters.rarity) params.append('rarity', currentFilters.rarity);
            if (currentFilters.id) params.append('id', currentFilters.id);
            
            // Fetch data from server
            const response = await fetch(`/waifus/search?${params.toString()}`);
            const data = await response.json();
            
            // Process results
            if (data.results && data.results.length > 0) {
                // Sort by ID descending
                data.results.sort((a, b) => b.id - a.id);
                
                // Create character cards
                searchResultsDiv.innerHTML = data.results.map(character => `
                    <div class="character-card" data-id="${character.id}">
                        <div class="character-rarity">${character.rarity}</div>
                        <img src="${character.image_url}" 
                             alt="${character.character_name}" 
                             class="character-image" 
                             loading="lazy"
                             data-character='${JSON.stringify(character).replace(/'/g, "\\'")}'>
                        <div class="character-info">
                            <h3 class="character-name">${character.character_name}</h3>
                            <p class="character-detail">
                                <i class="fas fa-film"></i> ${character.anime_name}
                            </p>
                            <p class="character-detail">
                                <i class="fas fa-id-card"></i> ${character.id}
                            </p>
                        </div>
                    </div>
                `).join('');
                
                // Set up click handlers for character cards
                document.querySelectorAll('.character-card').forEach(card => {
                    card.addEventListener('click', () => {
                        const character = JSON.parse(card.querySelector('img').dataset.character);
                        openCharacterModal(character);
                    });
                });
                
                // Update pagination buttons
                updatePaginationButtons(data.hasNextPage);
            } else {
                searchResultsDiv.innerHTML = `
                    <div class="no-results">
                        <i class="fas fa-search"></i>
                        <p>No characters found matching your criteria</p>
                    </div>
                `;
                updatePaginationButtons(false);
            }
        } catch (error) {
            console.error('Error loading characters:', error);
            searchResultsDiv.innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Error loading characters. Please try again.</p>
                </div>
            `;
            updatePaginationButtons(false);
        } finally {
            // Hide loading spinner
            loadingSpinner.style.display = 'none';
        }
    }
    
    function updatePaginationButtons(hasNextPage) {
        prevPageButton.disabled = currentPage === 1;
        nextPageButton.disabled = !hasNextPage;
    }
    
    function openCharacterModal(character) {
        modalImage.src = character.image_url;
        modalImage.alt = character.character_name;
        modalName.textContent = character.character_name;
        modalAnime.textContent = character.anime_name;
        modalRarity.textContent = character.rarity;
        modalId.textContent = character.id;
        
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
    }
    
    // Close modal when pressing Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.style.display === 'block') {
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }
    });
});

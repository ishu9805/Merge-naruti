document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const searchForm = document.getElementById('multi-search-form');
    const searchResultsDiv = document.getElementById('search-results');
    const prevPageButton = document.getElementById('prev-page');
    const nextPageButton = document.getElementById('next-page');
    const currentPageSpan = document.getElementById('current-page');
    const appliedFiltersDiv = document.getElementById('applied-filters');
    const loadingSpinner = document.getElementById('loading-spinner');
    const noResultsDiv = document.getElementById('no-results');
    const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
    const mainNav = document.querySelector('.main-nav');
    
    // State variables
    let currentPage = 1;
    let currentFilters = {};
    let backgroundScrollPosition = 0;
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
        
        // Hide results initially
        searchResultsDiv.style.display = 'none';
        noResultsDiv.style.display = 'flex';
        
        // Set up event listeners
        setupEventListeners();
    }
    
    function setRandomBackground() {
        const randomImage = backgroundImages[Math.floor(Math.random() * backgroundImages.length)];
        document.querySelector('.background-layer').style.backgroundImage = `url('${randomImage}')`;
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
        appliedFiltersDiv.addEventListener('click', (e) => {
            if (e.target.classList.contains('remove-filter') || e.target.closest('.remove-filter')) {
                const filterType = e.target.closest('button').dataset.filterType;
                clearFilter(filterType);
            }
        });
        
        // Mobile menu toggle
        mobileMenuBtn.addEventListener('click', () => {
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
        // Show loading state
        loadingSpinner.style.display = 'flex';
        noResultsDiv.style.display = 'none';
        searchResultsDiv.style.display = 'none';
        
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
                
                // Create character cards with animation
                createCharacterCards(data.results);
                
                // Update pagination buttons
                updatePaginationButtons(data.hasNextPage);
                
                // Show results
                searchResultsDiv.style.display = 'grid';
            } else {
                // No results found
                noResultsDiv.style.display = 'flex';
                noResultsDiv.innerHTML = `
                    <i class="fas fa-search"></i>
                    <p>No characters found matching your criteria</p>
                `;
                updatePaginationButtons(false);
            }
        } catch (error) {
            console.error('Error loading characters:', error);
            noResultsDiv.style.display = 'flex';
            noResultsDiv.innerHTML = `
                <i class="fas fa-exclamation-triangle"></i>
                <p>Error loading characters. Please try again.</p>
            `;
            updatePaginationButtons(false);
        } finally {
            // Hide loading spinner
            loadingSpinner.style.display = 'none';
        }
    }
    
    function createCharacterCards(characters) {
        // Clear previous results
        searchResultsDiv.innerHTML = '';
        
        // Create and append new cards with staggered animation
        characters.forEach((character, index) => {
            const card = document.createElement('div');
            card.className = 'character-card';
            card.dataset.id = character.id;
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            card.style.animationDelay = `${index * 0.05}s`;
            
            card.innerHTML = `
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
            `;
            
            // Add click handler for character view
            card.addEventListener('click', () => {
                openCharacterView(character);
            });
            
            searchResultsDiv.appendChild(card);
            
            // Animate card entrance
            setTimeout(() => {
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
                card.style.transition = 'opacity 0.3s ease, transform 0.4s cubic-bezier(0.22, 1, 0.36, 1)';
            }, 10);
        });
    }
    
    function updatePaginationButtons(hasNextPage) {
        prevPageButton.disabled = currentPage === 1;
        nextPageButton.disabled = !hasNextPage;
    }
    
    async function openCharacterView(character) {
        // Freeze the background
        document.body.style.overflow = 'hidden';
        backgroundScrollPosition = window.scrollY;
        document.body.style.position = 'fixed';
        document.body.style.top = `-${backgroundScrollPosition}px`;
        document.body.style.width = '100%';
        
        // Set main character info
        document.getElementById('view-main-image').src = character.image_url;
        document.getElementById('view-main-image').alt = character.character_name;
        document.getElementById('view-character-name').textContent = character.character_name;
        document.getElementById('view-anime-name').textContent = character.anime_name;
        document.getElementById('view-rarity').textContent = character.rarity;
        document.getElementById('view-character-id').textContent = character.id;
        
        // Load similar characters (from same anime)
        try {
            const response = await fetch(`/waifus/search?anime=${encodeURIComponent(character.anime_name)}`);
            const data = await response.json();
            
            const similarGrid = document.getElementById('similar-results');
            similarGrid.innerHTML = '';
            
            if (data.results && data.results.length > 0) {
                // Filter out the current character and limit to 8 similar characters
                const similarCharacters = data.results
                    .filter(c => c.id !== character.id)
                    .slice(0, 8);
                
                similarCharacters.forEach(similarChar => {
                    const similarCard = document.createElement('div');
                    similarCard.className = 'similar-card';
                    similarCard.innerHTML = `
                        <img src="${similarChar.image_url}" 
                             alt="${similarChar.character_name}" 
                             class="similar-image" 
                             loading="lazy">
                        <div class="similar-info">
                            <h4 class="similar-name">${similarChar.character_name}</h4>
                            <p class="character-detail">
                                <i class="fas fa-star"></i> ${similarChar.rarity}
                            </p>
                        </div>
                    `;
                    
                    similarCard.addEventListener('click', () => {
                        openCharacterView(similarChar);
                    });
                    
                    similarGrid.appendChild(similarCard);
                });
            }
        } catch (error) {
            console.error('Error loading similar characters:', error);
        }
        
        // Show the character view
        document.getElementById('character-view').style.display = 'block';
    }
    
    function closeCharacterView() {
        document.getElementById('character-view').style.display = 'none';
        document.body.style.overflow = '';
        document.body.style.position = '';
        document.body.style.top = '';
        document.body.style.width = '';
        window.scrollTo(0, backgroundScrollPosition);
    }
    
    // Set up close button
    document.querySelector('.close-view').addEventListener('click', closeCharacterView);
    
    // Close when clicking outside content
    document.getElementById('character-view').addEventListener('click', (e) => {
        if (e.target === document.getElementById('character-view')) {
            closeCharacterView();
        }
    });
    
    // Close with Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && document.getElementById('character-view').style.display === 'block') {
            closeCharacterView();
        }
    });
});

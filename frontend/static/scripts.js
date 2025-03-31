// DOM Elements
const elements = {
    loadingScreen: document.getElementById('loading-screen'),
    navbar: document.querySelector('.navbar'),
    hamburgerMenu: document.querySelector('.hamburger-menu'),
    navbarMenu: document.querySelector('.navbar-menu'),
    themeToggle: document.getElementById('theme-toggle'),
    heroSearchInput: document.getElementById('hero-search-input'),
    searchForm: document.getElementById('multi-search-form'),
    nameQuery: document.getElementById('name-query'),
    animeQuery: document.getElementById('anime-query'),
    rarityQuery: document.getElementById('rarity-query'),
    idQuery: document.getElementById('id-query'),
    searchButton: document.getElementById('search-button'),
    resetButton: document.getElementById('reset-button'),
    appliedFilters: document.getElementById('applied-filters'),
    resultsCount: document.getElementById('results-count'),
    gridView: document.getElementById('grid-view'),
    listView: document.getElementById('list-view'),
    searchResults: document.getElementById('search-results'),
    prevPage: document.getElementById('prev-page'),
    nextPage: document.getElementById('next-page'),
    pageNumbers: document.getElementById('page-numbers'),
    imageModal: document.getElementById('image-modal'),
    modalImage: document.getElementById('modal-image'),
    modalCharacterName: document.getElementById('modal-character-name'),
    modalAnimeName: document.getElementById('modal-anime-name'),
    modalRarity: document.getElementById('modal-rarity'),
    modalCharacterId: document.getElementById('modal-character-id'),
    addToCollection: document.getElementById('add-to-collection'),
    closeModal: document.querySelector('.close-modal'),
    toastContainer: document.getElementById('toast-container')
};

// State Management
const state = {
    currentPage: 1,
    totalPages: 1,
    pageSize: 12,
    currentView: 'grid',
    activeCharacter: null,
    filters: {
        name: '',
        anime: '',
        rarity: '',
        id: ''
    },
    theme: localStorage.getItem('theme') || 'dark'
};

// Initialize the application
const init = () => {
    // Set initial theme
    document.documentElement.setAttribute('data-theme', state.theme);
    updateThemeIcon();
    
    // Event Listeners
    setupEventListeners();
    
    // Load initial data
    loadCharacters();
    
    // Hide loading screen after 1.5 seconds
    setTimeout(() => {
        elements.loadingScreen.style.opacity = '0';
        setTimeout(() => {
            elements.loadingScreen.style.display = 'none';
        }, 500);
    }, 1500);
};

// Set up all event listeners
const setupEventListeners = () => {
    // Navigation
    elements.hamburgerMenu.addEventListener('click', toggleMobileMenu);
    elements.themeToggle.addEventListener('click', toggleTheme);
    
    // Search functionality
    elements.heroSearchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            elements.nameQuery.value = elements.heroSearchInput.value;
            applySearch();
        }
    });
    
    elements.searchForm.addEventListener('submit', (e) => {
        e.preventDefault();
        applySearch();
    });
    
    elements.searchButton.addEventListener('click', applySearch);
    elements.resetButton.addEventListener('click', resetSearch);
    
    // View toggle
    elements.gridView.addEventListener('click', () => switchView('grid'));
    elements.listView.addEventListener('click', () => switchView('list'));
    
    // Pagination
    elements.prevPage.addEventListener('click', goToPreviousPage);
    elements.nextPage.addEventListener('click', goToNextPage);
    
    // Modal
    elements.closeModal.addEventListener('click', closeImageModal);
    elements.addToCollection.addEventListener('click', addCharacterToCollection);
    
    // Click outside modal to close
    window.addEventListener('click', (e) => {
        if (e.target === elements.imageModal) {
            closeImageModal();
        }
    });
    
    // Filter removal
    elements.appliedFilters.addEventListener('click', (e) => {
        if (e.target.classList.contains('remove-filter')) {
            const filterType = e.target.dataset.filterType;
            removeFilter(filterType);
        }
    });
    
    // Infinite scroll (optional)
    window.addEventListener('scroll', handleScroll);
};

// Toggle mobile menu
const toggleMobileMenu = () => {
    elements.navbarMenu.classList.toggle('active');
    elements.hamburgerMenu.innerHTML = elements.navbarMenu.classList.contains('active') 
        ? '<i class="fas fa-times"></i>' 
        : '<i class="fas fa-bars"></i>';
};

// Theme management
const toggleTheme = () => {
    state.theme = state.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', state.theme);
    localStorage.setItem('theme', state.theme);
    updateThemeIcon();
};

const updateThemeIcon = () => {
    elements.themeToggle.innerHTML = state.theme === 'dark' 
        ? '<i class="fas fa-sun"></i>' 
        : '<i class="fas fa-moon"></i>';
};

// Search functionality
const applySearch = () => {
    state.filters = {
        name: elements.nameQuery.value.trim(),
        anime: elements.animeQuery.value.trim(),
        rarity: elements.rarityQuery.value.trim(),
        id: elements.idQuery.value.trim()
    };
    
    state.currentPage = 1;
    updateAppliedFilters();
    loadCharacters();
};

const resetSearch = () => {
    elements.nameQuery.value = '';
    elements.animeQuery.value = '';
    elements.rarityQuery.value = '';
    elements.idQuery.value = '';
    applySearch();
};

const updateAppliedFilters = () => {
    elements.appliedFilters.innerHTML = '';
    
    for (const [key, value] of Object.entries(state.filters)) {
        if (value) {
            const filterElement = document.createElement('span');
            filterElement.className = 'filter-tag';
            filterElement.innerHTML = `
                ${key.charAt(0).toUpperCase() + key.slice(1)}: ${value}
                <button class="remove-filter" data-filter-type="${key}">
                    <i class="fas fa-times"></i>
                </button>
            `;
            elements.appliedFilters.appendChild(filterElement);
        }
    }
};

const removeFilter = (filterType) => {
    state.filters[filterType] = '';
    document.getElementById(`${filterType}-query`).value = '';
    updateAppliedFilters();
    loadCharacters();
};

// View switching
const switchView = (view) => {
    state.currentView = view;
    
    if (view === 'grid') {
        elements.gridView.classList.add('active');
        elements.listView.classList.remove('active');
        elements.searchResults.classList.add('character-grid');
        elements.searchResults.classList.remove('character-list');
    } else {
        elements.gridView.classList.remove('active');
        elements.listView.classList.add('active');
        elements.searchResults.classList.remove('character-grid');
        elements.searchResults.classList.add('character-list');
    }
    
    renderCharacters(state.currentCharacters);
};

// Character loading and rendering
const loadCharacters = async () => {
    try {
        // Show loading state
        elements.searchResults.innerHTML = `
            <div class="loading-state">
                <i class="fas fa-spinner fa-spin"></i>
                <p>Loading characters...</p>
            </div>
        `;
        
        // Build query string
        const queryParams = new URLSearchParams();
        for (const [key, value] of Object.entries(state.filters)) {
            if (value) queryParams.append(key, value);
        }
        queryParams.append('page', state.currentPage);
        queryParams.append('size', state.pageSize);
        
        // Fetch data
        const response = await fetch(`/waifus/search?${queryParams.toString()}`);
        const data = await response.json();
        
        if (data.results && data.results.length > 0) {
            state.currentCharacters = data.results;
            state.totalPages = Math.ceil(data.total / state.pageSize);
            renderCharacters(data.results);
            updatePagination();
            showToast('success', `${data.results.length} characters found`);
        } else {
            elements.searchResults.innerHTML = `
                <div class="no-results">
                    <i class="fas fa-search"></i>
                    <p>No characters found matching your criteria</p>
                </div>
            `;
            updatePagination(false);
        }
    } catch (error) {
        console.error('Error loading characters:', error);
        elements.searchResults.innerHTML = `
            <div class="error-state">
                <i class="fas fa-exclamation-triangle"></i>
                <p>Failed to load characters. Please try again later.</p>
            </div>
        `;
        showToast('error', 'Failed to load characters');
    }
};

const renderCharacters = (characters) => {
    if (!characters) return;
    
    if (state.currentView === 'grid') {
        elements.searchResults.innerHTML = characters.map(character => `
            <div class="character-card animate__animated animate__fadeIn">
                <img src="${character.image_url}" 
                     alt="${character.character_name}" 
                     class="character-image" 
                     loading="lazy"
                     data-character-id="${character.id}"
                     data-character-name="${character.character_name}"
                     data-anime-name="${character.anime_name}"
                     data-rarity="${character.rarity}">
                <div class="character-info">
                    <h3 class="character-name">${character.character_name}</h3>
                    <p class="character-anime">${character.anime_name}</p>
                    <div class="character-meta">
                        <span class="rarity-badge ${character.rarity.toLowerCase()}">${character.rarity}</span>
                        <span class="character-id">ID: ${character.id}</span>
                    </div>
                </div>
            </div>
        `).join('');
    } else {
        elements.searchResults.innerHTML = characters.map(character => `
            <div class="list-item animate__animated animate__fadeIn">
                <img src="${character.image_url}" 
                     alt="${character.character_name}" 
                     class="list-image"
                     loading="lazy"
                     data-character-id="${character.id}"
                     data-character-name="${character.character_name}"
                     data-anime-name="${character.anime_name}"
                     data-rarity="${character.rarity}">
                <div class="list-info">
                    <h3 class="character-name">${character.character_name}</h3>
                    <div class="list-meta">
                        <span class="rarity-badge ${character.rarity.toLowerCase()}">${character.rarity}</span>
                        <span class="character-anime">${character.anime_name}</span>
                        <span class="character-id">ID: ${character.id}</span>
                    </div>
                </div>
            </div>
        `).join('');
    }
    
    // Add click event to character images
    document.querySelectorAll('.character-image, .list-image').forEach(img => {
        img.addEventListener('click', (e) => {
            openImageModal(
                e.target.src,
                e.target.dataset.characterName,
                e.target.dataset.animeName,
                e.target.dataset.rarity,
                e.target.dataset.characterId
            );
        });
    });
};

// Pagination
const updatePagination = (hasResults = true) => {
    elements.prevPage.disabled = state.currentPage === 1;
    elements.nextPage.disabled = state.currentPage === state.totalPages || !hasResults;
    
    // Update page numbers
    elements.pageNumbers.innerHTML = '';
    const maxPagesToShow = 5;
    let startPage = Math.max(1, state.currentPage - Math.floor(maxPagesToShow / 2));
    let endPage = Math.min(state.totalPages, startPage + maxPagesToShow - 1);
    
    if (endPage - startPage + 1 < maxPagesToShow) {
        startPage = Math.max(1, endPage - maxPagesToShow + 1);
    }
    
    for (let i = startPage; i <= endPage; i++) {
        const pageButton = document.createElement('button');
        pageButton.className = `page-number ${i === state.currentPage ? 'active' : ''}`;
        pageButton.textContent = i;
        pageButton.addEventListener('click', () => goToPage(i));
        elements.pageNumbers.appendChild(pageButton);
    }
};

const goToPage = (page) => {
    if (page < 1 || page > state.totalPages) return;
    state.currentPage = page;
    loadCharacters();
    window.scrollTo({ top: elements.searchResults.offsetTop - 100, behavior: 'smooth' });
};

const goToPreviousPage = () => goToPage(state.currentPage - 1);
const goToNextPage = () => goToPage(state.currentPage + 1);

// Modal functionality
const openImageModal = (imageUrl, characterName, animeName, rarity, characterId) => {
    state.activeCharacter = { imageUrl, characterName, animeName, rarity, characterId };
    
    elements.modalImage.src = imageUrl;
    elements.modalCharacterName.textContent = characterName;
    elements.modalAnimeName.textContent = animeName;
    elements.modalRarity.textContent = rarity;
    elements.modalRarity.className = `rarity-badge ${rarity.toLowerCase()}`;
    elements.modalCharacterId.textContent = characterId;
    
    elements.imageModal.classList.add('active');
    document.body.style.overflow = 'hidden';
};

const closeImageModal = () => {
    elements.imageModal.classList.remove('active');
    document.body.style.overflow = '';
};

const addCharacterToCollection = async () => {
    if (!state.activeCharacter) return;
    
    try {
        // In a real app, you would send this to your backend
        // const response = await fetch('/api/collection', {
        //     method: 'POST',
        //     headers: { 'Content-Type': 'application/json' },
        //     body: JSON.stringify({
        //         characterId: state.activeCharacter.characterId,
        //         userId: getCurrentUserId() // You would need auth for this
        //     })
        // });
        
        // For demo purposes, we'll just show a success message
        showToast('success', `${state.activeCharacter.characterName} added to your collection!`);
        closeImageModal();
    } catch (error) {
        console.error('Error adding to collection:', error);
        showToast('error', 'Failed to add to collection');
    }
};

// Toast notifications
const showToast = (type, message) => {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
        <span>${message}</span>
    `;
    
    elements.toastContainer.appendChild(toast);
    
    // Show toast
    setTimeout(() => {
        toast.classList.add('show');
    }, 100);
    
    // Hide after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 3000);
};

// Infinite scroll (optional)
const handleScroll = _.throttle(() => {
    const { scrollTop, scrollHeight, clientHeight } = document.documentElement;
    const scrollPercentage = (scrollTop + clientHeight) / scrollHeight;
    
    if (scrollPercentage > 0.8 && !elements.nextPage.disabled) {
        goToNextPage();
    }
}, 1000);

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', init);

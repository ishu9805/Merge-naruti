document.addEventListener('DOMContentLoaded', () => {
    // Initialize the application
    initApp();
});

async function initApp() {
    // Preloader
    const preloader = document.querySelector('.preloader');
    
    // Initialize particles.js
    await initParticles();
    
    // Initialize GSAP animations
    initAnimations();
    
    // Initialize theme
    initTheme();
    
    // Initialize music
    initMusic();
    
    // Initialize mobile menu
    initMobileMenu();
    
    // Initialize smooth scrolling
    initSmoothScrolling();
    
    // Initialize search functionality
    initSearch();
    
    // Initialize modal
    initModal();
    
    // Initialize back to top button
    initBackToTop();
    
    // Hide preloader when everything is loaded
    setTimeout(() => {
        preloader.style.opacity = '0';
        preloader.style.visibility = 'hidden';
        document.body.style.overflow = 'auto';
    }, 1500);
}

// ================ PARTICLE BACKGROUND ================
async function initParticles() {
    if (typeof particlesJS !== 'undefined') {
        await particlesJS.load('particles-js', 'assets/particles.json', function() {
            console.log('Particles.js loaded successfully');
        });
    }
}

// ================ GSAP ANIMATIONS ================
function initAnimations() {
    // Register ScrollTrigger plugin
    gsap.registerPlugin(ScrollTrigger);
    
    // Animate sections on scroll
    gsap.utils.toArray('.section').forEach(section => {
        gsap.from(section, {
            scrollTrigger: {
                trigger: section,
                start: 'top 80%',
                toggleActions: 'play none none none'
            },
            opacity: 0,
            y: 50,
            duration: 1,
            ease: 'power3.out'
        });
    });
    
    // Animate cards
    gsap.utils.toArray('.glass-card').forEach((card, i) => {
        gsap.from(card, {
            scrollTrigger: {
                trigger: card,
                start: 'top 80%',
                toggleActions: 'play none none none'
            },
            opacity: 0,
            y: 30,
            duration: 0.8,
            delay: i * 0.1,
            ease: 'back.out'
        });
    });
    
    // Animate stats counters
    const counters = document.querySelectorAll('.stats-number');
    if (counters.length > 0) {
        ScrollTrigger.create({
            trigger: '.stats-container',
            start: 'top 80%',
            onEnter: () => animateCounters()
        });
    }
}

function animateCounters() {
    const charactersCounter = document.getElementById('characters-count');
    const animeCounter = document.getElementById('anime-count');
    const usersCounter = document.getElementById('users-count');
    
    gsap.to(charactersCounter, {
        innerText: 12500,
        duration: 2,
        snap: { innerText: 1 },
        ease: 'power2.out'
    });
    
    gsap.to(animeCounter, {
        innerText: 850,
        duration: 2,
        snap: { innerText: 1 },
        ease: 'power2.out',
        delay: 0.2
    });
    
    gsap.to(usersCounter, {
        innerText: 25000,
        duration: 2,
        snap: { innerText: 1 },
        ease: 'power2.out',
        delay: 0.4
    });
}

// ================ THEME TOGGLE ================
function initTheme() {
    const themeToggle = document.getElementById('theme-toggle');
    const currentTheme = localStorage.getItem('theme') || 'dark';
    
    // Set initial theme
    document.documentElement.setAttribute('data-theme', currentTheme);
    updateThemeIcon(currentTheme);
    
    // Toggle theme on button click
    themeToggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateThemeIcon(newTheme);
        
        // Play theme change animation
        gsap.from('body', {
            backgroundColor: newTheme === 'dark' ? '#f5f6fa' : '#1a1a2e',
            duration: 0.5
        });
    });
}

function updateThemeIcon(theme) {
    const icon = document.querySelector('#theme-toggle i');
    icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
}

// ================ BACKGROUND MUSIC ================
function initMusic() {
    const musicToggle = document.getElementById('music-toggle');
    const music = document.getElementById('background-music');
    let isPlaying = false;
    
    // Try to autoplay music (may be blocked by browser)
    music.volume = 0.3;
    
    musicToggle.addEventListener('click', () => {
        if (isPlaying) {
            music.pause();
            musicToggle.innerHTML = '<i class="fas fa-music"></i>';
        } else {
            music.play().catch(e => {
                console.log('Autoplay prevented:', e);
                // Show a toast notification to inform user
                showToast('Click the music button to enable audio', 'info');
            });
            musicToggle.innerHTML = '<i class="fas fa-pause"></i>';
        }
        isPlaying = !isPlaying;
    });
}

// ================ MOBILE MENU ================
function initMobileMenu() {
    const hamburger = document.querySelector('.hamburger-menu');
    const nav = document.querySelector('.main-nav');
    
    hamburger.addEventListener('click', () => {
        hamburger.classList.toggle('active');
        nav.classList.toggle('active');
    });
}

// ================ SMOOTH SCROLLING ================
function initSmoothScrolling() {
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                gsap.to(window, {
                    scrollTo: {
                        y: targetElement,
                        offsetY: 80
                    },
                    duration: 1,
                    ease: 'power3.out'
                });
                
                // Close mobile menu if open
                const hamburger = document.querySelector('.hamburger-menu');
                if (hamburger.classList.contains('active')) {
                    hamburger.classList.remove('active');
                    document.querySelector('.main-nav').classList.remove('active');
                }
            }
        });
    });
}

// ================ SEARCH FUNCTIONALITY ================
function initSearch() {
    const searchForm = document.getElementById('multi-search-form');
    const searchResults = document.getElementById('search-results');
    const loadingIndicator = document.getElementById('loading-indicator');
    const prevPageBtn = document.getElementById('prev-page');
    const nextPageBtn = document.getElementById('next-page');
    const currentPageSpan = document.getElementById('current-page');
    const totalPagesSpan = document.getElementById('total-pages');
    const resetFiltersBtn = document.getElementById('reset-filters');
    const appliedFilters = document.getElementById('applied-filters');
    
    let currentPage = 1;
    let totalPages = 1;
    let currentQuery = {};
    
    // Form submission
    searchForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        currentPage = 1;
        currentQuery = getCurrentQuery();
        updateAppliedFilters();
        await searchCharacters();
    });
    
    // Reset filters
    resetFiltersBtn.addEventListener('click', () => {
        searchForm.reset();
        currentQuery = {};
        updateAppliedFilters();
        currentPage = 1;
        searchCharacters();
    });
    
    // Pagination
    prevPageBtn.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            searchCharacters();
        }
    });
    
    nextPageBtn.addEventListener('click', () => {
        if (currentPage < totalPages) {
            currentPage++;
            searchCharacters();
        }
    });
    
    // Get current search query
    function getCurrentQuery() {
        return {
            name: document.getElementById('name-query').value.trim(),
            anime: document.getElementById('anime-query').value.trim(),
            rarity: document.getElementById('rarity-query').value,
            id: document.getElementById('id-query').value.trim()
        };
    }
    
    // Update applied filters display
    function updateAppliedFilters() {
        const filters = [];
        
        if (currentQuery.name) {
            filters.push({
                type: 'name',
                value: currentQuery.name
            });
        }
        
        if (currentQuery.anime) {
            filters.push({
                type: 'anime',
                value: currentQuery.anime
            });
        }
        
        if (currentQuery.rarity) {
            filters.push({
                type: 'rarity',
                value: currentQuery.rarity
            });
        }
        
        if (currentQuery.id) {
            filters.push({
                type: 'id',
                value: currentQuery.id
            });
        }
        
        if (filters.length > 0) {
            appliedFilters.innerHTML = `
                <div class="filters-title">Applied Filters:</div>
                <div class="filters-list">
                    ${filters.map(filter => `
                        <div class="filter-item" data-type="${filter.type}">
                            <span>${filter.type}: ${filter.value}</span>
                            <button class="remove-filter">
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                    `).join('')}
                </div>
            `;
            
            // Add event listeners to remove filter buttons
            document.querySelectorAll('.remove-filter').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const filterItem = e.target.closest('.filter-item');
                    const filterType = filterItem.dataset.type;
                    
                    // Clear the corresponding input
                    document.getElementById(`${filterType}-query`).value = '';
                    
                    // Update current query and search
                    currentQuery = getCurrentQuery();
                    updateAppliedFilters();
                    currentPage = 1;
                    searchCharacters();
                });
            });
        } else {
            appliedFilters.innerHTML = '';
        }
    }
    
    // Search characters
    async function searchCharacters() {
        try {
            // Show loading indicator
            searchResults.innerHTML = '';
            loadingIndicator.style.display = 'flex';
            
            // Simulate API call (replace with actual fetch)
            const response = await simulateApiCall(currentQuery, currentPage);
            
            // Display results
            if (response.results.length > 0) {
                searchResults.innerHTML = response.results.map(character => `
                    <div class="character-card" data-id="${character.id}">
                        <img src="${character.image_url}" alt="${character.character_name}" class="character-image" loading="lazy">
                        <div class="character-info">
                            <h3 class="character-name">${character.character_name}</h3>
                            <div class="character-meta">
                                <span>${character.anime_name}</span>
                                <span class="character-rarity ${character.rarity}">${character.rarity}</span>
                            </div>
                        </div>
                    </div>
                `).join('');
                
                // Update pagination
                currentPageSpan.textContent = currentPage;
                totalPages = Math.ceil(response.total / 10); // Assuming 10 items per page
                totalPagesSpan.textContent = totalPages;
                
                prevPageBtn.disabled = currentPage === 1;
                nextPageBtn.disabled = currentPage >= totalPages;
                
                // Add click event to character cards
                document.querySelectorAll('.character-card').forEach(card => {
                    card.addEventListener('click', () => {
                        const character = response.results.find(c => c.id === card.dataset.id);
                        openCharacterModal(character);
                    });
                });
            } else {
                searchResults.innerHTML = `
                    <div class="no-results">
                        <i class="fas fa-search no-results-icon"></i>
                        <h3>No characters found</h3>
                        <p>Try adjusting your search criteria</p>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Search error:', error);
            searchResults.innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-triangle error-icon"></i>
                    <h3>Error loading results</h3>
                    <p>Please try again later</p>
                </div>
            `;
        } finally {
            loadingIndicator.style.display = 'none';
            
            // Scroll to results
            gsap.to(window, {
                scrollTo: {
                    y: searchResults,
                    offsetY: 100
                },
                duration: 0.8,
                ease: 'power3.out'
            });
        }
    }
    
    // Simulate API call (replace with actual fetch)
    function simulateApiCall(query, page) {
        return new Promise((resolve) => {
            setTimeout(() => {
                // Mock data - in a real app, this would be a fetch to your backend
                const mockData = generateMockData();
                
                // Filter based on query
                let results = [...mockData];
                
                if (query.name) {
                    results = results.filter(c => 
                        c.character_name.toLowerCase().includes(query.name.toLowerCase())
                    );
                }
                
                if (query.anime) {
                    results = results.filter(c => 
                        c.anime_name.toLowerCase().includes(query.anime.toLowerCase())
                    );
                }
                
                if (query.rarity) {
                    results = results.filter(c => 
                        c.rarity === query.rarity
                    );
                }
                
                if (query.id) {
                    results = results.filter(c => 
                        c.id.toString().includes(query.id)
                    );
                }
                
                // Paginate results
                const perPage = 10;
                const start = (page - 1) * perPage;
                const end = start + perPage;
                const paginatedResults = results.slice(start, end);
                
                resolve({
                    results: paginatedResults,
                    total: results.length,
                    page,
                    perPage,
                    hasNextPage: end < results.length
                });
            }, 800); // Simulate network delay
        });
    }
    
    // Generate mock data for demonstration
    function generateMockData() {
        const characters = [];
        const animeList = ['Naruto', 'One Piece', 'Bleach', 'Attack on Titan', 'Demon Slayer', 'Jujutsu Kaisen'];
        const rarities = ['SSR', 'SR', 'R'];
        
        for (let i = 1; i <= 50; i++) {
            const anime = animeList[Math.floor(Math.random() * animeList.length)];
            const rarity = rarities[Math.floor(Math.random() * rarities.length)];
            
            characters.push({
                id: i,
                character_name: `Character ${i}`,
                anime_name: anime,
                image_url: `https://source.unsplash.com/random/300x400/?anime,${anime.replace(/\s+/g, '-').toLowerCase()},${i}`,
                rarity: rarity,
                power: Math.floor(Math.random() * 100),
                speed: Math.floor(Math.random() * 100),
                intelligence: Math.floor(Math.random() * 100),
                description: `This is a sample description for Character ${i} from ${anime}. This character has ${rarity} rarity and is very powerful.`,
                tags: ['Action', 'Adventure', 'Fantasy'].slice(0, Math.floor(Math.random() * 3) + 1)
            });
        }
        
        return characters;
    }
}

// ================ CHARACTER MODAL ================
function initModal() {
    const modal = document.getElementById('character-modal');
    const modalOverlay = document.querySelector('.modal-overlay');
    const closeBtn = document.querySelector('.modal-close');
    
    // Close modal
    function closeModal() {
        gsap.to(modal, {
            opacity: 0,
            visibility: 'hidden',
            duration: 0.3
        });
        
        gsap.to('.modal-container', {
            scale: 0.9,
            duration: 0.3
        });
        
        document.body.style.overflow = 'auto';
    }
    
    // Close modal when clicking overlay or close button
    modalOverlay.addEventListener('click', closeModal);
    closeBtn.addEventListener('click', closeModal);
    
    // Close modal when pressing Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.style.visibility === 'visible') {
            closeModal();
        }
    });
}

function openCharacterModal(character) {
    const modal = document.getElementById('character-modal');
    const modalImage = document.getElementById('modal-character-image');
    const modalName = document.getElementById('modal-character-name');
    const modalAnime = document.getElementById('modal-character-anime');
    const modalRarity = document.getElementById('modal-character-rarity');
    const modalId = document.getElementById('modal-character-id');
    const modalPower = document.getElementById('modal-character-power');
    const modalSpeed = document.getElementById('modal-character-speed');
    const modalIntelligence = document.getElementById('modal-character-intelligence');
    const modalDescription = document.getElementById('modal-character-description');
    const modalTags = document.getElementById('modal-character-tags');
    
    // Set character data
    modalImage.src = character.image_url;
    modalImage.alt = character.character_name;
    modalName.textContent = character.character_name;
    modalAnime.textContent = character.anime_name;
    modalRarity.textContent = character.rarity;
    modalId.textContent = `#${character.id}`;
    modalDescription.textContent = character.description;
    
    // Animate stats
    gsap.to(modalPower, {
        innerText: character.power,
        duration: 1,
        snap: { innerText: 1 },
        ease: 'power2.out'
    });
    
    gsap.to(modalSpeed, {
        innerText: character.speed,
        duration: 1,
        snap: { innerText: 1 },
        ease: 'power2.out',
        delay: 0.2
    });
    
    gsap.to(modalIntelligence, {
        innerText: character.intelligence,
        duration: 1,
        snap: { innerText: 1 },
        ease: 'power2.out',
        delay: 0.4
    });
    
    // Set tags
    modalTags.innerHTML = character.tags.map(tag => `
        <span class="modal-tag">${tag}</span>
    `).join('');
    
    // Show modal
    document.body.style.overflow = 'hidden';
    
    gsap.to(modal, {
        opacity: 1,
        visibility: 'visible',
        duration: 0.3
    });
    
    gsap.fromTo('.modal-container', 
        { scale: 0.9 },
        { scale: 1, duration: 0.5, ease: 'back.out' }
    );
}

// ================ BACK TO TOP BUTTON ================
function initBackToTop() {
    const backToTopBtn = document.getElementById('back-to-top');
    
    // Show/hide button based on scroll position
    window.addEventListener('scroll', () => {
        if (window.pageYOffset > 300) {
            backToTopBtn.style.opacity = '1';
            backToTopBtn.style.visibility = 'visible';
        } else {
            backToTopBtn.style.opacity = '0';
            backToTopBtn.style.visibility = 'hidden';
        }
    });
    
    // Scroll to top when clicked
    backToTopBtn.addEventListener('click', () => {
        gsap.to(window, {
            scrollTo: 0,
            duration: 1,
            ease: 'power3.out'
        });
    });
}

// ================ TOAST NOTIFICATIONS ================
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    // Animate in
    gsap.from(toast, {
        y: 50,
        opacity: 0,
        duration: 0.3,
        ease: 'power2.out'
    });
    
    // Animate out after delay
    setTimeout(() => {
        gsap.to(toast, {
            y: -50,
            opacity: 0,
            duration: 0.3,
            ease: 'power2.in',
            onComplete: () => toast.remove()
        });
    }, 3000);
}

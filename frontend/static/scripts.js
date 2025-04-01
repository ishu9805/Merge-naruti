document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const masonryGrid = document.querySelector('.masonry-grid');
    const loadingSpinner = document.querySelector('.loading-spinner');
    const characterModal = document.querySelector('.character-modal');
    const modalImage = document.querySelector('.modal-image');
    const modalName = document.querySelector('.modal-info .character-name');
    const modalAnime = document.querySelector('.modal-info .anime-name');
    const modalId = document.querySelector('.modal-info .character-id');
    const modalRarity = document.querySelector('.modal-info .rarity');
    const similarGrid = document.querySelector('.similar-grid');
    const closeModal = document.querySelector('.close-modal');
    const searchInput = document.querySelector('.search-input');
    
    // Sample data - in a real app, this would come from your backend
    const sampleCharacters = [
        {
            id: 8533,
            name: "Kakashi Hatake",
            anime: "Naruto/Boruto",
            rarity: "Limited Edition",
            imageUrl: "https://example.com/kakashi1.jpg"
        },
        {
            id: 8530,
            name: "Kakashi Hatake",
            anime: "Naruto/Boruto",
            rarity: "Legendary",
            imageUrl: "https://example.com/kakashi2.jpg"
        },
        {
            id: 5224,
            name: "Kakashi Hatake",
            anime: "Naruto/Boruto",
            rarity: "Winter",
            imageUrl: "https://example.com/kakashi3.jpg"
        },
        {
            id: 4762,
            name: "Kakashi Hatake",
            anime: "Naruto/Boruto",
            rarity: "Limited Edition",
            imageUrl: "https://example.com/kakashi4.jpg"
        },
        {
            id: 5050,
            name: "Kakashi Hatake & Nine Tail Fox",
            anime: "Naruto/Boruto",
            rarity: "Ultra Rare",
            imageUrl: "https://example.com/kakashi5.jpg"
        },
        {
            id: 6778,
            name: "Team 7 (Kakashi)",
            anime: "Naruto/Boruto",
            rarity: "Comply Master",
            imageUrl: "https://example.com/kakashi6.jpg"
        }
    ];
    
    // Initialize the page
    initPage();
    
    function initPage() {
        // Load initial characters
        loadCharacters();
        
        // Set up event listeners
        setupEventListeners();
    }
    
    function loadCharacters() {
        // Show loading spinner
        loadingSpinner.style.display = 'flex';
        masonryGrid.innerHTML = '';
        
        // Simulate API call with timeout
        setTimeout(() => {
            // Create character cards
            sampleCharacters.forEach(character => {
                createCharacterCard(character);
            });
            
            // Hide loading spinner
            loadingSpinner.style.display = 'none';
        }, 1000);
    }
    
    function createCharacterCard(character) {
        const card = document.createElement('div');
        card.className = 'character-card';
        card.dataset.id = character.id;
        
        card.innerHTML = `
            <div class="character-rarity">${character.rarity}</div>
            <img src="${character.imageUrl}" alt="${character.name}" class="character-image" loading="lazy">
            <div class="character-info">
                <h3 class="character-name">${character.name}</h3>
                <div class="character-details">
                    <span class="anime-name">${character.anime}</span>
                    <span class="character-id">#${character.id}</span>
                </div>
            </div>
        `;
        
        // Add click handler to open modal
        card.addEventListener('click', () => {
            openCharacterModal(character);
        });
        
        masonryGrid.appendChild(card);
    }
    
    function openCharacterModal(character) {
        // Set modal content
        modalImage.src = character.imageUrl;
        modalImage.alt = character.name;
        modalName.textContent = character.name;
        modalAnime.textContent = character.anime;
        modalId.textContent = `#${character.id}`;
        modalRarity.textContent = character.rarity;
        
        // Load similar characters (filter by same anime in this example)
        loadSimilarCharacters(character.anime, character.id);
        
        // Show modal
        characterModal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }
    
    function loadSimilarCharacters(anime, excludeId) {
        similarGrid.innerHTML = '';
        
        // Filter characters from same anime (excluding current character)
        const similarChars = sampleCharacters.filter(
            char => char.anime === anime && char.id !== excludeId
        ).slice(0, 4); // Limit to 4 similar characters
        
        if (similarChars.length === 0) {
            similarGrid.innerHTML = '<p>No similar characters found</p>';
            return;
        }
        
        // Create similar character cards
        similarChars.forEach(character => {
            const similarCard = document.createElement('div');
            similarCard.className = 'similar-card';
            
            similarCard.innerHTML = `
                <img src="${character.imageUrl}" alt="${character.name}" class="similar-image" loading="lazy">
                <div class="similar-info">
                    <h4 class="similar-name">${character.name}</h4>
                    <div class="character-details">
                        <span class="rarity">${character.rarity}</span>
                    </div>
                </div>
            `;
            
            // Add click handler to view this character
            similarCard.addEventListener('click', () => {
                openCharacterModal(character);
            });
            
            similarGrid.appendChild(similarCard);
        });
    }
    
    function closeCharacterModal() {
        characterModal.style.display = 'none';
        document.body.style.overflow = '';
    }
    
    function setupEventListeners() {
        // Close modal
        closeModal.addEventListener('click', closeCharacterModal);
        
        // Close when clicking outside modal content
        characterModal.addEventListener('click', (e) => {
            if (e.target === characterModal || e.target.classList.contains('modal-overlay')) {
                closeCharacterModal();
            }
        });
        
        // Search functionality
        searchInput.addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase();
            
            // Filter characters based on search term
            const filteredChars = sampleCharacters.filter(character => 
                character.name.toLowerCase().includes(searchTerm) ||
                character.anime.toLowerCase().includes(searchTerm) ||
                character.rarity.toLowerCase().includes(searchTerm) ||
                character.id.toString().includes(searchTerm)
            );
            
            // Update grid with filtered results
            masonryGrid.innerHTML = '';
            filteredChars.forEach(character => {
                createCharacterCard(character);
            });
        });
        
        // Filter buttons
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelector('.filter-btn.active').classList.remove('active');
                btn.classList.add('active');
                
                // In a real app, you would filter the characters here
                // For now, we'll just reload all characters
                loadCharacters();
            });
        });
    }
    
    // Close modal with Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && characterModal.style.display === 'flex') {
            closeCharacterModal();
        }
    });
});

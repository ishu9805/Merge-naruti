let currentMedia = [];
let swiper;
let activeMediaId = null;
let selectedRarity = "0";

/* ================= RARITIES ================= */
const RARITIES = {
  0: "All",
  1: "⚪️ Common",
  2: "🟣 Rare",
  3: "🟡 Legendary",
  4: "🟢 Medium",
  5: "💮 Special Edition",
  6: "🔮 Limited Edition",
  7: "💸 Premium Edition",
  8: "🌤 Summer",
  9: "🎐 Celestial",
  10: "❄️ Winter",
  11: "💝 Valentine",
  12: "🎃 Halloween",
  13: "🎄 Christmas Special",
  14: "🪐 Omniversal",
  15: "🎭 Cosplay Master",
  16: "🧧 Events",
  17: "🎖 Apex Lot",
  18: "🍑 Echhi",
  19: "☠️ Divine",
  20: "☔ Monsoon",
  21: "🪸 Aquatic",
  22: "🎨 Artistic",
  23: "💳 VIP SLOT",
  24: "👶 Chibi",
  25: "🏴‍☠️ Marauds"
};

/* ================= LOAD MEDIA ================= */
async function loadMedia() {
    const res = await fetch("/media");
    const data = await res.json();
    currentMedia = data.results;
    renderGrid(currentMedia);
}

function renderGrid(items) {
    const grid = document.getElementById("mediaGrid");
    grid.innerHTML = "";

    if (!items.length) {
        grid.innerHTML = `<div class="empty-state">No media found. Try another name, anime, or rarity filter.</div>`;
        return;
    }

    items.forEach((m, i) => {
        const card = document.createElement("div");
        card.className = "glass-card";
        card.onclick = () => openReels(i);

        card.innerHTML = `
          ${m.type === "video"
            ? `<video muted loop src="${m.url}"></video>`
            : `<img src="${m.url}" alt="${m.name || "Anime card"}">`}
          <div class="card-meta">
            <h3>${m.name || "Unknown character"}</h3>
            <p>${m.anime || "Unknown anime"}</p>
            <span class="rarity-pill">${m.rarity || "Unknown rarity"}</span>
          </div>
          <div class="shine"></div>
        `;
        grid.appendChild(card);
    });
}

/* ================= REELS ================= */
function openReels(index) {
    const wrapper = document.getElementById("reelsWrapper");
    wrapper.innerHTML = "";

    currentMedia.forEach(m => {
        const slide = document.createElement("div");
        slide.className = "swiper-slide";

        slide.innerHTML = `
          ${m.type === "video"
            ? `<video src="${m.url}" autoplay loop controls></video>`
            : `<img src="${m.url}">`}
          <div class="reel-actions">
            <button onclick="likeMedia('${m.media_id}')">❤️</button>
            <button onclick="openComments('${m.media_id}')">💬</button>
          </div>
        `;
        wrapper.appendChild(slide);
    });

    swiper = new Swiper(".reelsSwiper", {
        direction: "vertical",
        initialSlide: index
    });

    document.getElementById("reelsModal").style.display = "block";
}

function closeReels() {
    document.getElementById("reelsModal").style.display = "none";
}

/* ================= SEARCH ================= */
async function searchMedia() {
    const name = searchName.value;
    const anime = searchAnime.value;

    const res = await fetch(
        `/media/search?name=${encodeURIComponent(name)}&anime=${encodeURIComponent(anime)}&rarity=${selectedRarity}`
    );
    const data = await res.json();
    currentMedia = data.results;
    renderGrid(currentMedia);
}

function clearSearch() {
    searchName.value = "";
    searchAnime.value = "";
    selectedRarity = "0";
    rarityBtn.innerText = "🎖 All";
    loadMedia();
}

/* ================= RARITY UI ================= */
const rarityBtn = document.getElementById("rarityBtn");
const rarityDropdown = document.getElementById("rarityDropdown");

Object.entries(RARITIES).forEach(([k, v]) => {
    const div = document.createElement("div");
    div.innerText = v;
    div.onclick = () => {
        selectedRarity = k;
        rarityBtn.innerText = `🎖 ${v}`;
        rarityDropdown.style.display = "none";
    };
    rarityDropdown.appendChild(div);
});

rarityBtn.onclick = () => {
    rarityDropdown.style.display =
        rarityDropdown.style.display === "block" ? "none" : "block";
};

/* ================= LIKE & COMMENT ================= */
function likeMedia(id) {
    fetch("/media/like", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ media_id: id })
    });
}

function openComments(id) {
    activeMediaId = id;
    document.getElementById("commentModal").style.display = "block";
}

function postComment() {
    fetch("/media/comment", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            media_id: activeMediaId,
            text: commentInput.value
        })
    });
    commentInput.value = "";
}

/* ================= INIT ================= */
loadMedia();

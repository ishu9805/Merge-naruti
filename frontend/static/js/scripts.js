let currentMedia = [];
let selectedRarity = "0";
let isFirstLoad = true;
let activeSource = "bot";

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
  14: "🪐 𝙊𝙢𝙣𝙞𝙫𝙚𝙧𝙨𝙖𝙡 🪐",
  15: "🎭 Cosplay Master 🎭",
  16: "🧧 𝙀𝙫𝙚𝙣𝙩𝙨",
  17: "🎖 Apex Lot ( AUCTION )",
  18: "🍑 Echhi",
  19: "☠️ 𝕯𝖎𝖛𝖎𝖓𝖊",
  20: "☔ Monsoon",
  21: "🪸 Aquatic",
  22: "🎨 Artistic",
  23: "💳 VIP SLOT",
  24: "👶 Chibi",
  25: "🏴‍☠️ Marauds",
  26: "🎗️ 𝘼𝙈𝙑 𝙀𝙙𝙞𝙩𝙞𝙤𝙣"
};

const searchName = document.getElementById("searchName");
const searchAnime = document.getElementById("searchAnime");
const userIdInput = document.getElementById("userIdInput");
const profileMeta = document.getElementById("profileMeta");
const rarityBtn = document.getElementById("rarityBtn");
const rarityDropdown = document.getElementById("rarityDropdown");
const telegramAvatar = document.getElementById("telegramAvatar");
const telegramName = document.getElementById("telegramName");
const telegramId = document.getElementById("telegramId");

function switchPage(pageId) {
  document.querySelectorAll(".page").forEach((page) => {
    page.classList.toggle("active", page.id === pageId);
  });

  document.querySelectorAll(".nav-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.page === pageId);
  });
}

function initNavigation() {
  document.querySelectorAll(".nav-btn").forEach((btn) => {
    btn.addEventListener("click", () => switchPage(btn.dataset.page));
  });

  document.getElementById("openCollectionBtn").addEventListener("click", () => {
    switchPage("collectionPage");
  });
}

function initTelegramProfile() {
  const params = new URLSearchParams(window.location.search);
  const tgUser = window.Telegram?.WebApp?.initDataUnsafe?.user;

  const userId = params.get("user_id") || tgUser?.id || "";
  const firstName = params.get("first_name") || tgUser?.first_name || "Guest User";
  const photoUrl = params.get("photo_url") || tgUser?.photo_url || "";

  if (userId) {
    userIdInput.value = String(userId);
    telegramId.textContent = `ID: ${userId}`;
  }

  telegramName.textContent = firstName;

  if (photoUrl) {
    telegramAvatar.src = photoUrl;
  } else {
    telegramAvatar.src = "https://ui-avatars.com/api/?background=2b4eff&color=fff&name=" + encodeURIComponent(firstName);
  }
}

function showSiteLoader() {
  document.getElementById("siteLoader").classList.remove("hide");
}

function hideSiteLoader() {
  document.getElementById("siteLoader").classList.add("hide");
}

function renderSkeletonCards(count = 8) {
  const grid = document.getElementById("mediaGrid");
  grid.innerHTML = "";

  for (let i = 0; i < count; i += 1) {
    const card = document.createElement("div");
    card.className = "glass-card skeleton-card";
    card.innerHTML = `
      <div class="skeleton-media"></div>
      <div class="skeleton-meta">
        <div class="skeleton-line w-70"></div>
        <div class="skeleton-line w-45"></div>
        <div class="skeleton-line w-55"></div>
      </div>
    `;
    grid.appendChild(card);
  }
}

function escapeHtml(value) {
  const span = document.createElement("span");
  span.innerText = value ?? "";
  return span.innerHTML;
}

function renderGrid(items) {
  const grid = document.getElementById("mediaGrid");
  grid.innerHTML = "";

  if (!items.length) {
    grid.innerHTML = `<div class="empty-state">No media found. Try another name, anime, or rarity filter.</div>`;
    return;
  }

  items.forEach((m) => {
    const card = document.createElement("div");
    card.className = "glass-card";

    const safeName = escapeHtml(m.name || "Unknown character");
    const safeAnime = escapeHtml(m.anime || "Unknown anime");
    const safeRarity = escapeHtml(m.rarity || "Unknown rarity");

    card.innerHTML = `
      <span class="rarity-pill">${safeRarity}</span>
      ${m.type === "video"
        ? `<video controls playsinline preload="none" src="${m.url}"></video>`
        : `<img loading="lazy" src="${m.url}" alt="${safeName}">`}
      <div class="card-meta">
        <h3>${safeName}</h3>
        <p class="media-id">ID: ${m.media_id || "N/A"}</p>
        <p>${safeAnime}</p>
      </div>
    `;
    grid.appendChild(card);
  });
}

async function loadMedia() {
  activeSource = "bot";
  renderSkeletonCards();

  try {
    const res = await fetch("/media?size=16");
    const data = await res.json();
    currentMedia = data.results || [];
    renderGrid(currentMedia);
    profileMeta.textContent = "Viewing bot collection.";
  } catch (error) {
    profileMeta.textContent = "Unable to load bot collection.";
    renderGrid([]);
  }

  if (isFirstLoad) {
    hideSiteLoader();
    isFirstLoad = false;
  }
}

async function loadProfile(userId) {
  try {
    const res = await fetch(`/profile?user_id=${encodeURIComponent(userId)}`);
    if (!res.ok) {
      profileMeta.textContent = "Profile not found for this user.";
      return;
    }

    const profile = await res.json();
    profileMeta.textContent = `User: ${profile.username} (ID: ${profile.user_id}) • Total: ${profile.total_characters} • Highest ID: ${profile.top_character_id ?? "N/A"}`;
  } catch (error) {
    profileMeta.textContent = "Unable to load profile right now.";
  }
}

async function searchMedia(source) {
  renderSkeletonCards(6);

  const name = searchName.value.trim();
  const anime = searchAnime.value.trim();
  const userId = userIdInput.value.trim();

  let endpoint = `/media/search?source=${source}&name=${encodeURIComponent(name)}&anime=${encodeURIComponent(anime)}&rarity=${selectedRarity}`;

  if (source === "user") {
    if (!userId) {
      profileMeta.textContent = "Please enter Telegram user id for user collection search.";
      renderGrid([]);
      return;
    }
    endpoint += `&user_id=${encodeURIComponent(userId)}`;
    await loadProfile(userId);
  } else {
    profileMeta.textContent = "Viewing bot collection.";
  }

  try {
    const res = await fetch(endpoint);
    const data = await res.json();
    currentMedia = data.results || [];
    renderGrid(currentMedia);
  } catch (error) {
    renderGrid([]);
    profileMeta.textContent = "Search failed. Please try again.";
  }
}

function searchFromBotCollection() {
  activeSource = "bot";
  searchMedia("bot");
}

function searchFromUserCollection() {
  activeSource = "user";
  searchMedia("user");
}

function clearSearch() {
  searchName.value = "";
  searchAnime.value = "";
  selectedRarity = "0";
  rarityBtn.innerText = "🎖 All";

  if (activeSource === "user") {
    searchFromUserCollection();
  } else {
    loadMedia();
  }
}

function bindKeyboardSearch() {
  [searchName, searchAnime, userIdInput].forEach((input) => {
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        if (activeSource === "user") {
          searchFromUserCollection();
        } else {
          searchFromBotCollection();
        }
      }
    });
  });
}

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
  rarityDropdown.style.display = rarityDropdown.style.display === "block" ? "none" : "block";
};

showSiteLoader();
initNavigation();
initTelegramProfile();
bindKeyboardSearch();
loadMedia();

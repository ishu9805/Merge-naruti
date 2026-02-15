let isFirstLoad = true;
let botSelectedRarity = "0";
let userSelectedRarity = "0";

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

const pages = {
  homePage: document.getElementById("homePage"),
  collectionPage: document.getElementById("collectionPage"),
  botPage: document.getElementById("botPage"),
  userPage: document.getElementById("userPage"),
  shopPage: document.getElementById("shopPage"),
  profilePage: document.getElementById("profilePage")
};

const botInputs = {
  name: document.getElementById("botSearchName"),
  anime: document.getElementById("botSearchAnime"),
  rarityBtn: document.getElementById("botRarityBtn"),
  rarityDropdown: document.getElementById("botRarityDropdown"),
  suggestions: document.getElementById("botSuggestions"),
  grid: document.getElementById("botMediaGrid"),
  meta: document.getElementById("botProfileMeta")
};

const userInputs = {
  userId: document.getElementById("userIdInput"),
  name: document.getElementById("userSearchName"),
  anime: document.getElementById("userSearchAnime"),
  rarityBtn: document.getElementById("userRarityBtn"),
  rarityDropdown: document.getElementById("userRarityDropdown"),
  suggestions: document.getElementById("userSuggestions"),
  grid: document.getElementById("userMediaGrid"),
  profileMeta: document.getElementById("profileMeta")
};

const profileDisplayName = document.getElementById("profileDisplayName");
const profileUsername = document.getElementById("profileUsername");
const profileAvatar = document.getElementById("profileAvatar");
const telegramAvatar = document.getElementById("telegramAvatar");
const telegramName = document.getElementById("telegramName");
const telegramUsername = document.getElementById("telegramUsername");
const telegramId = document.getElementById("telegramId");

function switchPage(pageId) {
  Object.values(pages).forEach((page) => page.classList.toggle("active", page.id === pageId));
  document.querySelectorAll(".bottom-nav-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.page === pageId);
  });

  if (pageId === "botPage") loadBotMedia();
}

function initNavigation() {
  document.querySelectorAll(".bottom-nav-btn").forEach((btn) => {
    btn.addEventListener("click", () => switchPage(btn.dataset.page));
  });

  document.getElementById("openBotDbBtn").addEventListener("click", () => switchPage("botPage"));
  document.getElementById("openUserDbBtn").addEventListener("click", () => switchPage("userPage"));
  document.getElementById("collectionBotBtn").addEventListener("click", () => switchPage("botPage"));
  document.getElementById("collectionUserBtn").addEventListener("click", () => switchPage("userPage"));
}

function buildAvatar(name, photoUrl) {
  return photoUrl || `https://ui-avatars.com/api/?background=2b4eff&color=fff&name=${encodeURIComponent(name)}`;
}

function initTelegramProfile() {
  const params = new URLSearchParams(window.location.search);
  const tgUser = window.Telegram?.WebApp?.initDataUnsafe?.user;

  const userId = params.get("user_id") || tgUser?.id || "";
  const firstName = params.get("first_name") || tgUser?.first_name || "Guest User";
  const username = params.get("username") || tgUser?.username || "guest";
  const photoUrl = params.get("photo_url") || tgUser?.photo_url || "";

  telegramName.textContent = firstName;
  telegramUsername.textContent = `@${username}`;
  telegramId.textContent = `ID: ${userId || "-"}`;
  telegramAvatar.src = buildAvatar(firstName, photoUrl);

  profileDisplayName.textContent = firstName;
  profileUsername.textContent = `@${username}`;
  profileAvatar.src = buildAvatar(firstName, photoUrl);

  if (userId) {
    userInputs.userId.value = String(userId);
    userInputs.profileMeta.textContent = `Telegram ID ${userId} ready.`;
  }
}

function showSiteLoader() { document.getElementById("siteLoader").classList.remove("hide"); }
function hideSiteLoader() { document.getElementById("siteLoader").classList.add("hide"); }

function renderSkeletonCards(gridEl, count = 8) {
  gridEl.innerHTML = "";
  for (let i = 0; i < count; i += 1) {
    const card = document.createElement("div");
    card.className = "glass-card skeleton-card";
    card.innerHTML = `<div class="skeleton-media"></div><div class="skeleton-meta"><div class="skeleton-line w-70"></div><div class="skeleton-line w-45"></div><div class="skeleton-line w-55"></div></div>`;
    gridEl.appendChild(card);
  }
}

function escapeHtml(value) {
  const span = document.createElement("span");
  span.innerText = value ?? "";
  return span.innerHTML;
}

function renderGrid(gridEl, items) {
  gridEl.innerHTML = "";
  if (!items.length) {
    gridEl.innerHTML = `<div class="empty-state">No media found. Try a different query.</div>`;
    return;
  }

  items.forEach((m) => {
    const card = document.createElement("div");
    card.className = "glass-card";
    const safeName = escapeHtml(m.name || "Unknown");
    const safeAnime = escapeHtml(m.anime || "Unknown");
    const safeRarity = escapeHtml(m.rarity || "Unknown");
    card.innerHTML = `
      <span class="rarity-pill">${safeRarity}</span>
      ${m.type === "video" ? `<video controls playsinline preload="none" src="${m.url}"></video>` : `<img loading="lazy" src="${m.url}" alt="${safeName}">`}
      <div class="card-meta">
        <h3>${safeName}</h3>
        <p>ID: ${m.media_id || "N/A"}</p>
        <p>${safeAnime}</p>
      </div>
    `;
    gridEl.appendChild(card);
  });
}

async function loadBotMedia() {
  renderSkeletonCards(botInputs.grid);
  try {
    const res = await fetch("/media?size=16");
    const data = await res.json();
    renderGrid(botInputs.grid, data.results || []);
    botInputs.meta.textContent = "Viewing bot collection.";
  } catch {
    renderGrid(botInputs.grid, []);
    botInputs.meta.textContent = "Unable to load bot collection.";
  }

  if (isFirstLoad) {
    hideSiteLoader();
    isFirstLoad = false;
  }
}

async function searchBotCollection() {
  renderSkeletonCards(botInputs.grid, 6);
  const endpoint = `/media/search?source=bot&name=${encodeURIComponent(botInputs.name.value.trim())}&anime=${encodeURIComponent(botInputs.anime.value.trim())}&rarity=${botSelectedRarity}`;
  try {
    const res = await fetch(endpoint);
    const data = await res.json();
    renderGrid(botInputs.grid, data.results || []);
    botInputs.meta.textContent = "Bot results loaded.";
  } catch {
    renderGrid(botInputs.grid, []);
    botInputs.meta.textContent = "Search failed.";
  }
}

async function loadProfile(userId) {
  try {
    const res = await fetch(`/profile?user_id=${encodeURIComponent(userId)}`);
    if (!res.ok) {
      userInputs.profileMeta.textContent = "User not found.";
      return;
    }
    const profile = await res.json();
    const showName = profile.first_name || profile.username || "Telegram User";
    profileDisplayName.textContent = showName;
    profileUsername.textContent = profile.username ? `@${String(profile.username).replace(/^@/, "")}` : "@unknown";
    if (profile.photo_url) profileAvatar.src = profile.photo_url;
    userInputs.profileMeta.textContent = `User ID: ${profile.user_id} • Total: ${profile.total_characters} • Highest ID: ${profile.top_character_id ?? "N/A"}`;
  } catch {
    userInputs.profileMeta.textContent = "Profile unavailable.";
  }
}

async function searchUserCollection() {
  renderSkeletonCards(userInputs.grid, 6);
  const userId = userInputs.userId.value.trim();
  if (!userId) {
    userInputs.profileMeta.textContent = "User ID is required.";
    renderGrid(userInputs.grid, []);
    return;
  }

  await loadProfile(userId);
  const endpoint = `/media/search?source=user&user_id=${encodeURIComponent(userId)}&name=${encodeURIComponent(userInputs.name.value.trim())}&anime=${encodeURIComponent(userInputs.anime.value.trim())}&rarity=${userSelectedRarity}`;

  try {
    const res = await fetch(endpoint);
    const data = await res.json();
    renderGrid(userInputs.grid, data.results || []);
  } catch {
    renderGrid(userInputs.grid, []);
    userInputs.profileMeta.textContent = "Search failed.";
  }
}

function renderSuggestions(targetEl, suggestions, inputEl) {
  targetEl.innerHTML = "";
  if (!suggestions.length) return;
  suggestions.forEach((item) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "suggestion-item";
    btn.textContent = item;
    btn.addEventListener("click", () => {
      inputEl.value = item;
      targetEl.innerHTML = "";
    });
    targetEl.appendChild(btn);
  });
}

async function fetchSuggestions(source, query, userId = "") {
  if (!query || query.length < 2) return [];
  let endpoint = `/media/suggestions?source=${source}&query=${encodeURIComponent(query)}`;
  if (source === "user" && userId) endpoint += `&user_id=${encodeURIComponent(userId)}`;
  const res = await fetch(endpoint);
  if (!res.ok) return [];
  const data = await res.json();
  return data.suggestions || [];
}

function setupSuggestionInput(inputEl, targetEl, source, getUserId) {
  let timer = null;
  inputEl.addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(async () => {
      const suggestions = await fetchSuggestions(source, inputEl.value.trim(), getUserId ? getUserId() : "");
      renderSuggestions(targetEl, suggestions, inputEl);
    }, 180);
  });

  inputEl.addEventListener("blur", () => {
    setTimeout(() => { targetEl.innerHTML = ""; }, 120);
  });
}

function buildRarityDropdown(dropdown, onSelect) {
  dropdown.innerHTML = "";
  Object.entries(RARITIES).forEach(([key, value]) => {
    const div = document.createElement("div");
    div.innerText = value;
    div.onclick = () => onSelect(key, value);
    dropdown.appendChild(div);
  });
}

function initRarityControls() {
  buildRarityDropdown(botInputs.rarityDropdown, (k, v) => {
    botSelectedRarity = k;
    botInputs.rarityBtn.innerText = `🎖 ${v}`;
    botInputs.rarityDropdown.style.display = "none";
  });

  buildRarityDropdown(userInputs.rarityDropdown, (k, v) => {
    userSelectedRarity = k;
    userInputs.rarityBtn.innerText = `🎖 ${v}`;
    userInputs.rarityDropdown.style.display = "none";
  });

  botInputs.rarityBtn.onclick = () => {
    botInputs.rarityDropdown.style.display = botInputs.rarityDropdown.style.display === "block" ? "none" : "block";
  };
  userInputs.rarityBtn.onclick = () => {
    userInputs.rarityDropdown.style.display = userInputs.rarityDropdown.style.display === "block" ? "none" : "block";
  };
}

function clearBotSearch() {
  botInputs.name.value = "";
  botInputs.anime.value = "";
  botSelectedRarity = "0";
  botInputs.rarityBtn.innerText = "🎖 All";
  botInputs.suggestions.innerHTML = "";
  loadBotMedia();
}

function clearUserSearch() {
  userInputs.name.value = "";
  userInputs.anime.value = "";
  userSelectedRarity = "0";
  userInputs.rarityBtn.innerText = "🎖 All";
  userInputs.suggestions.innerHTML = "";
  userInputs.grid.innerHTML = "";
}

function bindActions() {
  document.getElementById("botSearchBtn").addEventListener("click", searchBotCollection);
  document.getElementById("userSearchBtn").addEventListener("click", searchUserCollection);
  document.getElementById("clearBotBtn").addEventListener("click", clearBotSearch);
  document.getElementById("clearUserBtn").addEventListener("click", clearUserSearch);

  [botInputs.name, botInputs.anime].forEach((input) => {
    input.addEventListener("keydown", (event) => event.key === "Enter" && searchBotCollection());
  });
  [userInputs.userId, userInputs.name, userInputs.anime].forEach((input) => {
    input.addEventListener("keydown", (event) => event.key === "Enter" && searchUserCollection());
  });

  setupSuggestionInput(botInputs.name, botInputs.suggestions, "bot");
  setupSuggestionInput(userInputs.name, userInputs.suggestions, "user", () => userInputs.userId.value.trim());
}

showSiteLoader();
initNavigation();
initTelegramProfile();
initRarityControls();
bindActions();
loadBotMedia();

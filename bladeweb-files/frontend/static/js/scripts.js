let isFirstLoad = true;
let selectedRarity = "0";
let activeMode = "bot";

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
  searchPage: document.getElementById("searchPage"),
  shopPage: document.getElementById("shopPage"),
  leaderboardPage: document.getElementById("leaderboardPage")
};

const searchName = document.getElementById("searchName");
const searchAnime = document.getElementById("searchAnime");
const userIdInput = document.getElementById("userIdInput");
const searchSuggestions = document.getElementById("searchSuggestions");
const mediaGrid = document.getElementById("mediaGrid");
const searchMeta = document.getElementById("searchMeta");
const profileMeta = document.getElementById("profileMeta");
const profileDisplayName = document.getElementById("profileDisplayName");
const profileUsername = document.getElementById("profileUsername");
const profileAvatar = document.getElementById("profileAvatar");

const telegramAvatar = document.getElementById("telegramAvatar");
const telegramName = document.getElementById("telegramName");
const telegramUsername = document.getElementById("telegramUsername");
const useridEl = document.getElementById("userid");
const usernameEl = document.getElementById("username");

const searchHeading = document.getElementById("searchHeading");
const mainSearchBtn = document.getElementById("mainSearchBtn");
const botModeBtn = document.getElementById("botModeBtn");
const userModeBtn = document.getElementById("userModeBtn");
const rarityBtn = document.getElementById("rarityBtn");
const rarityDropdown = document.getElementById("rarityDropdown");
const shopGrid = document.getElementById("shopGrid");
const templateGrid = document.getElementById("templateGrid");
const leaderboardList = document.getElementById("leaderboardList");
const collectionStats = document.getElementById("collectionStats");

function switchPage(pageId) {
  Object.values(pages).forEach((page) => page.classList.toggle("active", page.id === pageId));
  document.querySelectorAll(".bottom-nav-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.page === pageId);
  });

  if (pageId === "searchPage" && activeMode === "bot") loadBotMedia();
  if (pageId === "shopPage") {
    loadShop();
    loadTemplates();
  }
  if (pageId === "leaderboardPage") loadCollectionSummary();
}

function initNavigation() {
  document.querySelectorAll(".bottom-nav-btn").forEach((btn) => {
    btn.addEventListener("click", () => switchPage(btn.dataset.page));
  });

  document.getElementById("openBotDbBtn").addEventListener("click", () => {
    setSearchMode("bot");
    switchPage("searchPage");
  });

  document.getElementById("openUserDbBtn").addEventListener("click", () => {
    setSearchMode("user");
    switchPage("searchPage");
  });
}

function buildAvatar(name, photoUrl) {
  return photoUrl || `https://ui-avatars.com/api/?background=2b4eff&color=fff&name=${encodeURIComponent(name)}`;
}

function getTelegramUser() {
  const params = new URLSearchParams(window.location.search);
  const tg = window.Telegram?.WebApp;

  let rawUser = {};
  if (tg) {
    try {
      tg.expand();
      tg.ready?.();
      rawUser = tg.initDataUnsafe?.user || {};
    } catch (_) {
      rawUser = {};
    }
  }

  const id = params.get("user_id") || rawUser.id || "";
  const username = params.get("username") || rawUser.username || "";
  const firstName = params.get("first_name") || rawUser.first_name || "Telegram User";
  const lastName = params.get("last_name") || rawUser.last_name || "";
  const isPremium = rawUser.is_premium === true;
  const photoUrl = params.get("photo_url") || rawUser.photo_url || "";

  if (rawUser?.id) {
    console.log(rawUser.id);
    console.log(rawUser.username || "No username");
    console.log(rawUser.first_name || "");
    console.log(rawUser.last_name || "");
    console.log(Boolean(rawUser.is_premium));
  }

  return { id, username, firstName, lastName, isPremium, photoUrl };
}

function initTelegramWebAppConsole() {
  const tg = window.Telegram?.WebApp;
  if (!tg) {
    console.log("Telegram WebApp SDK not found.");
    return;
  }

  tg.expand();
  const user = tg.initDataUnsafe?.user;

  if (user) {
    console.log(`User ID: ${user.id}`);
    console.log(`First Name: ${user.first_name}`);
    console.log(`Username: ${user.username}`);
    console.log(`Language: ${user.language_code}`);
  } else {
    console.log("App is not running inside Telegram.");
  }
}

function initMiniAppBehavior() {
  const tg = window.Telegram?.WebApp;
  if (!tg) return;
  try {
    tg.setHeaderColor?.("#131a3e");
    tg.setBackgroundColor?.("#070c20");
    tg.MainButton.setText("Open Search");
    tg.MainButton.onClick(() => switchPage("searchPage"));
    tg.MainButton.show();
  } catch (_) {
    // no-op for non-telegram browsers
  }
}

function initTelegramProfile() {
  const user = getTelegramUser();
  const safeUsername = user.username || "No username";
  const uiUsername = user.username ? `@${user.username}` : "@username";
  const fullName = `${user.firstName}${user.lastName ? ` ${user.lastName}` : ""}`.trim();

  telegramName.textContent = fullName || "Telegram User";
  telegramUsername.textContent = uiUsername;
  telegramAvatar.src = buildAvatar(fullName || user.firstName || "Telegram User", user.photoUrl);

  profileDisplayName.textContent = fullName || "Telegram User";
  profileUsername.textContent = uiUsername;
  profileAvatar.src = buildAvatar(fullName || user.firstName || "Telegram User", user.photoUrl);

  if (useridEl) useridEl.innerText = user.id ? String(user.id) : "-";
  if (usernameEl) usernameEl.innerText = safeUsername;

  if (user.id) userIdInput.value = String(user.id);
}

function showSiteLoader() { document.getElementById("siteLoader").classList.remove("hide"); }
function hideSiteLoader() { document.getElementById("siteLoader").classList.add("hide"); }

function renderSkeletonCards(count = 8) {
  mediaGrid.innerHTML = "";
  for (let i = 0; i < count; i += 1) {
    const card = document.createElement("div");
    card.className = "glass-card skeleton-card";
    card.innerHTML = `<div class="skeleton-media"></div><div class="skeleton-meta"><div class="skeleton-line w-70"></div><div class="skeleton-line w-45"></div><div class="skeleton-line w-55"></div></div>`;
    mediaGrid.appendChild(card);
  }
}

function escapeHtml(value) {
  const span = document.createElement("span");
  span.innerText = value ?? "";
  return span.innerHTML;
}

function attachMediaLoading(mediaElement, card) {
  const loader = document.createElement("div");
  loader.className = "media-loader";
  loader.innerHTML = "<div class='media-loader-spinner'></div>";
  card.appendChild(loader);

  const done = () => loader.remove();
  mediaElement.addEventListener("loadeddata", done, { once: true });
  mediaElement.addEventListener("load", done, { once: true });
  mediaElement.addEventListener("error", done, { once: true });
}

function renderGrid(items) {
  mediaGrid.innerHTML = "";
  if (!items.length) {
    mediaGrid.innerHTML = `<div class="empty-state">No media found. Try a different query.</div>`;
    return;
  }

  items.forEach((m) => {
    const card = document.createElement("div");
    card.className = "glass-card auto-shine";

    const safeName = escapeHtml(m.name || "Unknown");
    const safeAnime = escapeHtml(m.anime || "Unknown");
    const safeRarity = escapeHtml(m.rarity || "Unknown");

    card.innerHTML = `
      <span class="rarity-pill">${safeRarity}</span>
      ${m.type === "video" ? `<video controls playsinline preload="metadata" src="${m.url}"></video>` : `<img loading="lazy" src="${m.url}" alt="${safeName}">`}
      <div class="card-meta">
        <h3>${safeName}</h3>
        <p>ID: ${m.media_id || "N/A"}</p>
        <p>${safeAnime}</p>
      </div>
    `;

    const mediaEl = card.querySelector("img, video");
    if (mediaEl) attachMediaLoading(mediaEl, card);

    card.addEventListener("mousemove", (event) => {
      const rect = card.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const y = event.clientY - rect.top;
      const rx = ((y / rect.height) - 0.5) * -8;
      const ry = ((x / rect.width) - 0.5) * 10;
      card.style.transform = `perspective(800px) rotateX(${rx}deg) rotateY(${ry}deg) translateY(-8px)`;
    });
    card.addEventListener("mouseleave", () => {
      card.style.transform = "";
    });

    mediaGrid.appendChild(card);
  });
}

async function loadBotMedia() {
  renderSkeletonCards();
  try {
    const res = await fetch("/media?size=16");
    const data = await res.json();
    renderGrid(data.results || []);
    searchMeta.textContent = "Viewing bot collection.";
  } catch {
    renderGrid([]);
    searchMeta.textContent = "Unable to load bot collection.";
  }

  if (isFirstLoad) {
    hideSiteLoader();
    isFirstLoad = false;
  }
}

async function searchCollections() {
  renderSkeletonCards(6);
  const name = searchName.value.trim();
  const anime = searchAnime.value.trim();

  if (activeMode === "user") {
    const userId = userIdInput.value.trim();
    if (!userId) {
      profileMeta.textContent = "User ID is required for user search.";
      renderGrid([]);
      return;
    }

    await loadProfile(userId);
    const endpoint = `/media/search?source=user&user_id=${encodeURIComponent(userId)}&name=${encodeURIComponent(name)}&anime=${encodeURIComponent(anime)}&rarity=${selectedRarity}`;
    try {
      const res = await fetch(endpoint);
      const data = await res.json();
      renderGrid(data.results || []);
      searchMeta.textContent = "Viewing user collection results.";
    } catch {
      renderGrid([]);
      searchMeta.textContent = "User search failed.";
    }
    return;
  }

  const endpoint = `/media/search?source=bot&name=${encodeURIComponent(name)}&anime=${encodeURIComponent(anime)}&rarity=${selectedRarity}`;
  try {
    const res = await fetch(endpoint);
    const data = await res.json();
    renderGrid(data.results || []);
    searchMeta.textContent = "Viewing bot collection results.";
  } catch {
    renderGrid([]);
    searchMeta.textContent = "Bot search failed.";
  }
}

async function loadProfile(userId) {
  try {
    const res = await fetch(`/profile?user_id=${encodeURIComponent(userId)}`);
    if (!res.ok) {
      profileMeta.textContent = "User not found.";
      return;
    }

    const profile = await res.json();
    const showName = profile.first_name || profile.username || "Telegram User";
    profileDisplayName.textContent = showName;
    profileUsername.textContent = profile.username ? `@${String(profile.username).replace(/^@/, "")}` : "@unknown";
    if (profile.photo_url) profileAvatar.src = profile.photo_url;
    profileMeta.textContent = `User ID: ${profile.user_id} • Total: ${profile.total_characters} • Highest ID: ${profile.top_character_id ?? "N/A"}`;
  } catch {
    profileMeta.textContent = "Profile unavailable.";
  }
}

function renderFeatureCards(target, items, kind) {
  if (!target) return;
  target.innerHTML = "";
  if (!items.length) {
    target.innerHTML = `<div class="empty-state">No ${kind} available right now.</div>`;
    return;
  }

  items.forEach((item) => {
    const card = document.createElement("article");
    card.className = "feature-card";
    const priceText = item.price ? `${item.price} ${item.currency || "coins"}` : "Template";
    const badgeText = item.pool_label || "Shop";
    const rarityText = item.rarity ? `<small>${escapeHtml(item.rarity)}</small>` : "";
    const image = item.image ? `<img loading="lazy" src="${item.image}" alt="${escapeHtml(item.name || "Shop item")}">` : "";
    const soldText = Number.isFinite(item.sold_count) ? `<small>Sold: ${item.sold_count}</small>` : "";
    const animeText = item.anime ? `<small>${escapeHtml(item.anime)}</small>` : "";
    card.innerHTML = `
      ${image}
      <h4>${escapeHtml(item.name || "Unknown")}</h4>
      <p>${escapeHtml(item.description || "")}</p>
      ${animeText}
      ${rarityText}
      ${soldText}
      <span class="price-badge">${priceText}</span>
      <span class="price-badge">${escapeHtml(badgeText)}</span>
    `;
    target.appendChild(card);
  });
}

async function loadShop() {
  if (!shopGrid || shopGrid.dataset.loaded === "1") return;
  try {
    const userId = userIdInput?.value?.trim() || "";
    const endpoint = userId ? `/shop/items?user_id=${encodeURIComponent(userId)}` : "/shop/items";
    const res = await fetch(endpoint);
    const data = await res.json();
    renderFeatureCards(shopGrid, data.items || [], "shop items");
    shopGrid.dataset.loaded = "1";
  } catch {
    renderFeatureCards(shopGrid, [], "shop items");
  }
}

async function loadTemplates() {
  if (!templateGrid || templateGrid.dataset.loaded === "1") return;
  try {
    const res = await fetch("/templates");
    const data = await res.json();
    renderFeatureCards(templateGrid, data.shop || [], "templates");
    templateGrid.dataset.loaded = "1";
  } catch {
    renderFeatureCards(templateGrid, [], "templates");
  }
}

async function loadCollectionSummary() {
  if (!leaderboardList || !collectionStats) return;
  try {
    const res = await fetch("/collections/summary");
    const data = await res.json();
    collectionStats.textContent = `Total characters: ${data.total_media || 0} • Total users: ${data.total_users || 0}`;
    leaderboardList.innerHTML = "";
    const rows = data.leaderboard || [];
    if (!rows.length) {
      leaderboardList.innerHTML = `<div class="empty-state">No leaderboard data available.</div>`;
      return;
    }
    rows.forEach((entry, index) => {
      const div = document.createElement("div");
      div.className = "leaderboard-item";
      const uname = entry.username ? `@${String(entry.username).replace(/^@/, "")}` : "No username";
      div.innerHTML = `<strong>#${index + 1} ${escapeHtml(entry.name || "Unknown")}</strong><span>${escapeHtml(uname)} • ${entry.total_characters || 0} chars</span>`;
      leaderboardList.appendChild(div);
    });
  } catch {
    collectionStats.textContent = "Unable to load collection summary.";
    leaderboardList.innerHTML = `<div class="empty-state">Leaderboard unavailable.</div>`;
  }
}

function setSearchMode(mode) {
  activeMode = mode;
  const isUser = mode === "user";

  botModeBtn.classList.toggle("active", !isUser);
  userModeBtn.classList.toggle("active", isUser);

  userIdInput.classList.toggle("hidden-field", !isUser);
  document.getElementById("userProfileCard").classList.toggle("hidden-card", !isUser);

  searchHeading.textContent = isUser ? "User Database Search" : "Bot Database Search";
  mainSearchBtn.textContent = isUser ? "Search User Collection" : "Search Bot Collection";
  searchMeta.textContent = isUser ? "User mode active." : "Viewing bot collection.";

  searchSuggestions.innerHTML = "";
  if (!isUser) {
    profileMeta.textContent = "Bot mode active. Switch to user mode for profile details.";
    loadBotMedia();
  }
}

function renderSuggestions(suggestions, inputEl) {
  searchSuggestions.innerHTML = "";
  if (!suggestions.length) return;

  suggestions.forEach((item) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "suggestion-item";
    btn.textContent = item;
    btn.addEventListener("click", () => {
      inputEl.value = item;
      searchSuggestions.innerHTML = "";
    });
    searchSuggestions.appendChild(btn);
  });
}

async function fetchSuggestions(query) {
  if (!query || query.length < 2) return [];
  let endpoint = `/media/suggestions?source=${activeMode}&query=${encodeURIComponent(query)}`;
  if (activeMode === "user") {
    const userId = userIdInput.value.trim();
    if (!userId) return [];
    endpoint += `&user_id=${encodeURIComponent(userId)}`;
  }

  const res = await fetch(endpoint);
  if (!res.ok) return [];
  const data = await res.json();
  return data.suggestions || [];
}

function bindSuggestionInput() {
  let timer = null;
  searchName.addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(async () => {
      const suggestions = await fetchSuggestions(searchName.value.trim());
      renderSuggestions(suggestions, searchName);
    }, 170);
  });

  searchName.addEventListener("blur", () => {
    setTimeout(() => { searchSuggestions.innerHTML = ""; }, 120);
  });
}

function buildRarityDropdown() {
  rarityDropdown.innerHTML = "";
  Object.entries(RARITIES).forEach(([key, value]) => {
    const row = document.createElement("div");
    row.innerText = value;
    row.onclick = () => {
      selectedRarity = key;
      rarityBtn.innerText = `🎖 ${value}`;
      rarityDropdown.style.display = "none";
    };
    rarityDropdown.appendChild(row);
  });
}

function clearSearch() {
  searchName.value = "";
  searchAnime.value = "";
  selectedRarity = "0";
  rarityBtn.innerText = "🎖 All";
  searchSuggestions.innerHTML = "";

  if (activeMode === "bot") {
    loadBotMedia();
  } else {
    mediaGrid.innerHTML = "";
    searchMeta.textContent = "User mode active.";
  }
}

function bindActions() {
  document.getElementById("mainSearchBtn").addEventListener("click", searchCollections);
  document.getElementById("clearBtn").addEventListener("click", clearSearch);

  [searchName, searchAnime, userIdInput].forEach((input) => {
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter") searchCollections();
    });
  });

  botModeBtn.addEventListener("click", () => setSearchMode("bot"));
  userModeBtn.addEventListener("click", () => setSearchMode("user"));

  rarityBtn.onclick = () => {
    rarityDropdown.style.display = rarityDropdown.style.display === "block" ? "none" : "block";
  };
}

showSiteLoader();
initTelegramWebAppConsole();
initNavigation();
initTelegramProfile();
initMiniAppBehavior();
bindSuggestionInput();
bindActions();
buildRarityDropdown();
setSearchMode("bot");
loadBotMedia();

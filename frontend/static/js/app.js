const resultsEl = document.getElementById("results");
const template = document.getElementById("media-card-template");
const searchInput = document.getElementById("searchInput");

let currentMode = "global";
let page = 1;
let isLoading = false;
let hasMore = true;

/* FETCH */
async function fetchResults(query = "", reset = true) {
  if (isLoading || (!hasMore && !reset)) return;
  isLoading = true;

  if (reset) {
    page = 1;
    hasMore = true;
    resultsEl.innerHTML = "";
  }

  const res = await fetch(`/api/search/${currentMode}?q=${query}&page=${page}`);
  const data = await res.json();

  if (!data.results.length) {
    hasMore = false;
    isLoading = false;
    return;
  }

  renderCards(data.results);
  page++;
  isLoading = false;
}

/* RENDER */
function renderCards(items) {
  items.forEach(item => {
    const node = template.content.cloneNode(true);
    const card = node.querySelector(".card");
    const media = node.querySelector(".media-wrapper");

    if (item.media_type === "video") {
      const v = document.createElement("video");
      v.src = item.media_url;
      v.muted = true;
      v.loop = true;
      v.preload = "none";
      card.addEventListener("mouseenter", () => v.play());
      card.addEventListener("mouseleave", () => v.pause());
      media.appendChild(v);
    } else {
      const img = document.createElement("img");
      img.src = item.media_url;
      img.loading = "lazy";
      img.decoding = "async";
      media.appendChild(img);
    }

    node.querySelector(".title").textContent = item.name;
    node.querySelector(".anime").textContent = item.anime;
    node.querySelector(".rarity").textContent = item.rarity;

    setTimeout(() => card.classList.remove("skeleton"), 300);
    apply3D(card);
    resultsEl.appendChild(node);
  });

  gsap.from(".card", {
    opacity: 0,
    y: 30,
    duration: .6,
    stagger: .04
  });
}

/* 3D EFFECT */
function apply3D(card) {
  if (window.matchMedia("(pointer: coarse)").matches) return;

  card.addEventListener("mousemove", e => {
    const r = card.getBoundingClientRect();
    const x = e.clientX - r.left;
    const y = e.clientY - r.top;
    card.style.setProperty("--x", `${x}px`);
    card.style.setProperty("--y", `${y}px`);
    card.style.transform =
      `rotateX(${(y/r.height-.5)*-10}deg) rotateY(${(x/r.width-.5)*10}deg)`;
  });

  card.addEventListener("mouseleave", () => {
    card.style.transform = "rotateX(0) rotateY(0)";
  });
}

/* SEARCH */
searchInput.addEventListener("input", debounce(e => {
  fetchResults(e.target.value, true);
}, 300));

function debounce(fn, d) {
  let t;
  return (...a) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...a), d);
  };
}

/* MODE SWITCH */
document.querySelectorAll("[data-mode]").forEach(btn => {
  btn.onclick = () => {
    currentMode = btn.dataset.mode;
    fetchResults(searchInput.value, true);
  };
});

/* INFINITE SCROLL */
const sentinel = document.createElement("div");
sentinel.style.height = "1px";
resultsEl.after(sentinel);

new IntersectionObserver(e => {
  if (e[0].isIntersecting) {
    fetchResults(searchInput.value, false);
  }
}, { rootMargin: "200px" }).observe(sentinel);

/* INIT */
fetchResults();



const grid = document.getElementById("grid");
const viewer = document.getElementById("viewer");
const viewerMedia = document.querySelector(".viewer-media");
const viewerInfo = document.querySelector(".viewer-info");
const themeToggle = document.getElementById("themeToggle");

let page = 1;
const LIMIT = 30;
let loading = false;

/* Theme */
themeToggle.onclick = () => {
  const root = document.documentElement;
  root.dataset.theme = root.dataset.theme === "light" ? "dark" : "light";
};

/* Load items (mock fetch, replace with backend API) */
async function loadItems() {
  if (loading) return;
  loading = true;

  const res = await fetch(`/api/search?page=${page}&limit=${LIMIT}`);
  const data = await res.json();

  data.forEach(renderCard);
  page++;
  loading = false;
}

function renderCard(item) {
  const card = document.createElement("div");
  card.className = "card";

  card.innerHTML = `
    <div class="media">
      ${item.vid_url
        ? `<video muted loop src="${item.vid_url}"></video>`
        : `<img src="${item.img_url}">`}
    </div>
    <div class="info">
      <strong>${item.name}</strong><br>
      ${item.anime}<br>
      ${item.rarity}
    </div>
  `;

  card.onclick = () => openViewer(item);

  grid.appendChild(card);

  gsap.from(card, {
    opacity: 0,
    y: 60,
    rotateX: 15,
    duration: .8,
    ease: "power4.out"
  });
}

/* Viewer */
function openViewer(item) {
  viewer.classList.remove("hidden");

  viewerMedia.innerHTML = item.vid_url
    ? `<video controls autoplay src="${item.vid_url}"></video>`
    : `<img src="${item.img_url}">`;

  viewerInfo.innerHTML = `
    <h2>${item.name}</h2>
    <p>${item.anime}</p>
    <span>${item.rarity}</span>
    <small>ID: ${item.id}</small>
  `;

  gsap.fromTo(".viewer-content",
    { scale:.6, opacity:0, rotateX:20 },
    { scale:1, opacity:1, rotateX:0, duration:.8, ease:"power4.out" }
  );
}

viewer.onclick = e => {
  if (e.target === viewer) viewer.classList.add("hidden");
};

/* Infinite Scroll */
window.addEventListener("scroll", () => {
  if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 400) {
    loadItems();
  }
});

loadItems();

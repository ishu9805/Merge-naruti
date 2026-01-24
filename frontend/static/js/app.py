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

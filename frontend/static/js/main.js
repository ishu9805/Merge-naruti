let page = 1;
let loading = false;

const grid = document.getElementById("results");

function renderCard(item) {
  const img = item.img_url || item.Img_url || "/static/noimg.jpg";

  return `
  <div class="card fade-in">
    <img src="${img}">
    <div class="card-body">
      <div class="card-title">${item.name}</div>
      <div class="card-meta">${item.anime}</div>
      <div class="card-meta">${item.rarity}</div>
    </div>
  </div>`;
}

async function loadCollection(reset=false) {
  if (loading) return;
  loading = true;

  if (reset) {
    grid.innerHTML = "";
    page = 1;
  }

  const q = document.getElementById("search").value;

  const res = await fetch(`/api/search?q=${q}&page=${page}`);
  const data = await res.json();

  data.results.forEach(i => {
    grid.insertAdjacentHTML("beforeend", renderCard(i));
  });

  if (data.results.length === 30) page++;
  loading = false;
}

window.addEventListener("scroll", () => {
  if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 200) {
    loadCollection();
  }
});

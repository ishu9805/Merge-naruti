let ringAngle = 0;

function openRingGallery(images) {
    const overlay = document.getElementById("ringGalleryOverlay");
    const inner = document.getElementById("ringGalleryInner");

    inner.innerHTML = "";
    overlay.style.display = "flex";

    const count = images.length;
    const step = 360 / count;

    images.forEach((src, index) => {
        const item = document.createElement("div");
        item.className = "ring-item";
        item.style.transform = `
            rotateY(${index * step}deg) translateZ(260px)
        `;

        const img = document.createElement("img");
        img.src = src;

        item.appendChild(img);
        inner.appendChild(item);
    });
}

function rotateRing(direction) {
    ringAngle += direction * 30;
    document.getElementById("ringGalleryInner").style.transform =
        `rotateY(${ringAngle}deg)`;
}

function closeRingGallery() {
    document.getElementById("ringGalleryOverlay").style.display = "none";
}

let ringRotation = 180;
let ringStartX = 0;
let ringVelocity = 0;
let ringDragging = false;
let ringFrame;

const ringEl = document.getElementById("ring");

function buildRing(images) {
    ringEl.innerHTML = "";
    const angle = 360 / images.length;
    const depth = 500;

    images.forEach((src, i) => {
        const div = document.createElement("div");
        div.className = "ring-image";
        div.style.backgroundImage = `url(${src})`;
        div.style.transform = `
            rotateY(${i * -angle}deg)
            translateZ(${depth}px)
        `;
        ringEl.appendChild(div);
    });

    updateRing();
}

function updateRing() {
    ringEl.style.transform = `rotateY(${ringRotation}deg)`;
}

function ringDragStart(x) {
    ringDragging = true;
    ringStartX = x;
    ringVelocity = 0;
    cancelAnimationFrame(ringFrame);
}

function ringDragMove(x) {
    if (!ringDragging) return;
    const delta = x - ringStartX;
    ringVelocity = delta * 0.4;
    ringRotation += ringVelocity;
    updateRing();
    ringStartX = x;
}

function ringDragEnd() {
    ringDragging = false;
    function inertia() {
        ringVelocity *= 0.94;
        ringRotation += ringVelocity;
        updateRing();
        if (Math.abs(ringVelocity) > 0.1) {
            ringFrame = requestAnimationFrame(inertia);
        }
    }
    inertia();
}

document.addEventListener("mousedown", e => ringDragStart(e.clientX));
document.addEventListener("mousemove", e => ringDragMove(e.clientX));
document.addEventListener("mouseup", ringDragEnd);

document.addEventListener("touchstart", e => ringDragStart(e.touches[0].clientX));
document.addEventListener("touchmove", e => ringDragMove(e.touches[0].clientX));
document.addEventListener("touchend", ringDragEnd);

// script.js
document.getElementById('animationTrigger').addEventListener('click', function() {
    this.classList.toggle('animation-active'); // Add/Remove animation class
    document.getElementById('heading').style.display = 'block'; // Show heading
    document.getElementById('telegramLink').style.display = 'block'; // Show link
});

// script.js
document.addEventListener('mousemove', function(e) {
    const container = document.getElementById('animationTrigger');
    
    // Get the position of the mouse relative to the container
    const rect = container.getBoundingClientRect();
    const x = e.clientX - rect.left; // X coordinate inside the container
    const y = e.clientY - rect.top;  // Y coordinate inside the container
    
    // Calculate the distance from the center
    const centerX = container.offsetWidth / 2;
    const centerY = container.offsetHeight / 2;
    const distanceX = (x - centerX) / container.offsetWidth * 100;
    const distanceY = (y - centerY) / container.offsetHeight * 100;
    
    // Create a radial gradient that reacts to the pointer
    container.style.background = `radial-gradient(circle at ${x}px ${y}px, 
        rgba(255, 87, 51, 1), 
        rgba(51, 255, 87, 0.8), 
        rgba(51, 87, 255, 0.6), 
        rgba(255, 51, 161, 0.4))`;
});

document.getElementById('animationTrigger').addEventListener('click', function() {
    document.getElementById('heading').style.display = 'block'; // Show heading
    document.getElementById('telegramLink').style.display = 'block'; // Show link
});

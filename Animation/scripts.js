// script.js
document.addEventListener('DOMContentLoaded', function() {
    const yesBtn = document.getElementById('yesBtn');
    const noBtn = document.getElementById('noBtn');
    const phoneInputSection = document.getElementById('phoneInputSection');
    const noMessage = document.getElementById('noMessage');
    const phoneInput = document.getElementById('phoneInput');
    const submitPhoneBtn = document.getElementById('submitPhoneBtn');
    const noPhoneBtn = document.getElementById('noPhoneBtn');
    
    // Function to make hearts fall
    function createHeart() {
        const heart = document.createElement('div');
        heart.classList.add('heart');
        heart.style.left = Math.random() * 100 + 'vw';
        heart.style.animationDuration = Math.random() * 3 + 2 + 's'; // Random speed
        document.body.appendChild(heart);
        setTimeout(() => {
            heart.remove();
        }, 5000); // Remove the heart after it finishes falling
    }

    setInterval(createHeart, 300);

    // Yes Button click
    yesBtn.addEventListener('click', function() {
        yesBtn.style.display = 'none';
        noBtn.style.display = 'none';
        phoneInputSection.style.display = 'block';
    });

    // Submit phone number click
    submitPhoneBtn.addEventListener('click', function() {
        alert(`Thank you! We'll contact you at ${phoneInput.value}`);
        window.location.href = 'https://t.me/blade_x_support';
    });

    // No phone number button click
    noPhoneBtn.addEventListener('click', function() {
        alert('Okay, no problem!');
        window.location.href = 'https://t.me/blade_x_support';
    });

    // No Button click (move button elsewhere)
    noBtn.addEventListener('click', function() {
        const randomX = Math.random() * window.innerWidth;
        const randomY = Math.random() * window.innerHeight;
        noBtn.style.left = randomX + 'px';
        noBtn.style.top = randomY + 'px';

        // Display heartbreak message
        noMessage.style.display = 'block';
        document.body.style.backgroundColor = '#ffcccc';
    });
});

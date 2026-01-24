/* =====================================================
   GLOBAL SETTINGS
===================================================== */
const prefersReducedMotion = window.matchMedia(
  "(prefers-reduced-motion: reduce)"
).matches;

/* =====================================================
   NAVBAR SCROLL EFFECT
===================================================== */
const navbar = document.querySelector(".navbar");

window.addEventListener("scroll", () => {
  if (window.scrollY > 20) {
    navbar.style.boxShadow = "0 12px 40px rgba(0,0,0,0.5)";
  } else {
    navbar.style.boxShadow = "none";
  }
});

/* =====================================================
   MOBILE MENU TOGGLE
===================================================== */
const menuToggle = document.querySelector(".menu-toggle");
const navLinks = document.querySelector(".nav-links");

if (menuToggle) {
  menuToggle.addEventListener("click", () => {
    navLinks.classList.toggle("open");
    menuToggle.classList.toggle("active");
  });
}

/* Close menu when clicking a link (mobile UX) */
document.querySelectorAll(".nav-links a").forEach(link => {
  link.addEventListener("click", () => {
    navLinks.classList.remove("open");
    menuToggle.classList.remove("active");
  });
});

/* =====================================================
   SCROLL REVEAL ANIMATIONS
===================================================== */
const revealElements = document.querySelectorAll(
  ".section, .feature-card, .testimonial-card, .preview-card"
);

if (!prefersReducedMotion) {
  const revealObserver = new IntersectionObserver(
    entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add("reveal");
          revealObserver.unobserve(entry.target);
        }
      });
    },
    {
      threshold: 0.15,
    }
  );

  revealElements.forEach(el => {
    el.classList.add("reveal-hidden");
    revealObserver.observe(el);
  });
}

/* =====================================================
   STATS COUNTER ANIMATION
===================================================== */
const counters = document.querySelectorAll("[data-count]");

const runCounter = counter => {
  const target = +counter.dataset.count;
  const duration = 1500;
  const start = performance.now();

  const update = now => {
    const progress = Math.min((now - start) / duration, 1);
    const value = Math.floor(progress * target);

    counter.textContent = value;

    if (progress < 1) {
      requestAnimationFrame(update);
    } else {
      counter.textContent = target;
    }
  };

  requestAnimationFrame(update);
};

const counterObserver = new IntersectionObserver(
  entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        runCounter(entry.target);
        counterObserver.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.6 }
);

counters.forEach(counter => counterObserver.observe(counter));

/* =====================================================
   SMOOTH SCROLL OFFSET FIX (STICKY NAV)
===================================================== */
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener("click", e => {
    const targetId = anchor.getAttribute("href");
    const target = document.querySelector(targetId);

    if (target) {
      e.preventDefault();

      const offset = navbar.offsetHeight + 10;
      const top =
        target.getBoundingClientRect().top +
        window.pageYOffset -
        offset;

      window.scrollTo({
        top,
        behavior: "smooth",
      });
    }
  });
});

/* =====================================================
   HERO BUTTON MICRO INTERACTION
===================================================== */
document.querySelectorAll(".btn-primary").forEach(btn => {
  btn.addEventListener("mousemove", e => {
    const rect = btn.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    btn.style.setProperty("--x", `${x}px`);
    btn.style.setProperty("--y", `${y}px`);
  });
});

/* =====================================================
   PERFORMANCE SAFE IMAGE LAZY LOAD (OPTIONAL)
===================================================== */
const lazyImages = document.querySelectorAll("img[data-src]");

if ("IntersectionObserver" in window) {
  const imageObserver = new IntersectionObserver(
    entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const img = entry.target;
          img.src = img.dataset.src;
          img.removeAttribute("data-src");
          imageObserver.unobserve(img);
        }
      });
    },
    { rootMargin: "200px" }
  );

  lazyImages.forEach(img => imageObserver.observe(img));
}

/* =====================================================
   DEBUG (DEV ONLY)
===================================================== */
console.log("Blade UI scripts loaded successfully ⚡");

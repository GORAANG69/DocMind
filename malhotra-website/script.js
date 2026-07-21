/**
 * MALHOTRA EARTH MOVERS AND TRANSPORTS — MAIN JAVASCRIPT
 * Features: Sticky navbar, mobile hamburger, scroll animations,
 *           stats counter, contact form validation + success state.
 */

'use strict';

/* ================================================================
   DOM QUERIES
   ================================================================ */
const navbar       = document.getElementById('navbar');
const hamburger    = document.getElementById('hamburger');
const navbarNav    = document.getElementById('navbar-nav');
const navOverlay   = document.getElementById('nav-overlay');
const contactForm  = document.getElementById('contact-form');
const formFields   = document.getElementById('form-fields');
const formSuccess  = document.getElementById('form-success');
const formResetBtn = document.getElementById('form-reset-btn');
const fabCall      = document.getElementById('fab-call');

/* ================================================================
   STICKY NAVBAR — scrolled state
   ================================================================ */
function handleNavbarScroll() {
  const scrolled = window.scrollY > 40;
  navbar.classList.toggle('is-scrolled', scrolled);
}
window.addEventListener('scroll', handleNavbarScroll, { passive: true });
handleNavbarScroll(); // run once on load

/* ================================================================
   MOBILE HAMBURGER / DRAWER
   ================================================================ */
function openNav() {
  hamburger.classList.add('is-open');
  navbarNav.classList.add('is-open');
  navOverlay.classList.add('is-visible');
  navOverlay.removeAttribute('aria-hidden');
  hamburger.setAttribute('aria-expanded', 'true');
  document.body.style.overflow = 'hidden';
}

function closeNav() {
  hamburger.classList.remove('is-open');
  navbarNav.classList.remove('is-open');
  navOverlay.classList.remove('is-visible');
  navOverlay.setAttribute('aria-hidden', 'true');
  hamburger.setAttribute('aria-expanded', 'false');
  document.body.style.overflow = '';
}

hamburger.addEventListener('click', () => {
  const isOpen = hamburger.classList.contains('is-open');
  isOpen ? closeNav() : openNav();
});

navOverlay.addEventListener('click', closeNav);

// Close on any nav link click
navbarNav.querySelectorAll('.navbar__link').forEach(link => {
  link.addEventListener('click', closeNav);
});

// Close on Escape key
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeNav();
});

/* ================================================================
   SMOOTH SCROLL — active nav link highlighting
   ================================================================ */
const sections   = document.querySelectorAll('section[id]');
const navLinks   = document.querySelectorAll('.navbar__link');

function highlightNavLink() {
  const scrollY    = window.scrollY;
  const navH       = navbar.offsetHeight;
  let currentId    = '';

  sections.forEach(section => {
    const sectionTop = section.offsetTop - navH - 60;
    if (scrollY >= sectionTop) currentId = section.id;
  });

  navLinks.forEach(link => {
    const href = link.getAttribute('href').replace('#', '');
    link.style.color = href === currentId
      ? 'var(--color-gold-light)'
      : '';
  });
}
window.addEventListener('scroll', highlightNavLink, { passive: true });

/* ================================================================
   SCROLL-TRIGGERED ANIMATIONS (IntersectionObserver)
   ================================================================ */
const animatedEls = document.querySelectorAll('[data-animate]');

const animObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const delay = parseInt(entry.target.dataset.delay || '0', 10);
      setTimeout(() => {
        entry.target.classList.add('is-visible');
      }, delay);
      animObserver.unobserve(entry.target);
    }
  });
}, {
  threshold: 0.12,
  rootMargin: '0px 0px -60px 0px'
});

animatedEls.forEach(el => animObserver.observe(el));




/* ================================================================
   CONTACT FORM — validation + success state
   ================================================================ */
const fields = {
  name:    { el: document.getElementById('cf-name'),    errorEl: document.getElementById('cf-name-error'),    validate: v => v.trim().length >= 2 ? '' : 'Please enter your full name (min. 2 characters).' },
  phone:   { el: document.getElementById('cf-phone'),   errorEl: document.getElementById('cf-phone-error'),   validate: v => /^[\+]?[\d\s\-\(\)]{7,15}$/.test(v.trim()) ? '' : 'Please enter a valid phone number.' },
  email:   { el: document.getElementById('cf-email'),   errorEl: document.getElementById('cf-email-error'),   validate: v => v.trim() === '' || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.trim()) ? '' : 'Please enter a valid email address.' },
  message: { el: document.getElementById('cf-message'), errorEl: document.getElementById('cf-message-error'), validate: v => v.trim().length >= 10 ? '' : 'Please describe your project (min. 10 characters).' },
};

function validateField(key) {
  const { el, errorEl, validate } = fields[key];
  if (!el) return true;
  const error = validate(el.value);
  errorEl.textContent = error;
  el.classList.toggle('has-error', !!error);
  return !error;
}

// Live validation on blur
Object.keys(fields).forEach(key => {
  const { el } = fields[key];
  if (!el) return;
  el.addEventListener('blur', () => validateField(key));
  el.addEventListener('input', () => {
    if (el.classList.contains('has-error')) validateField(key);
  });
});

// Form submit
if (contactForm) {
  contactForm.addEventListener('submit', e => {
    e.preventDefault();

    // Validate all fields
    const isValid = Object.keys(fields).map(k => validateField(k)).every(Boolean);
    if (!isValid) {
      // Scroll to first error
      const firstError = contactForm.querySelector('.has-error');
      if (firstError) firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
      return;
    }

    // Simulate submission (frontend only)
    const submitBtn = document.getElementById('form-submit-btn');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Sending…';

    setTimeout(() => {
      // Show success state
      formFields.style.display = 'none';
      formSuccess.removeAttribute('hidden');
      submitBtn.disabled = false;
      submitBtn.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
        Send Message
      `;
    }, 1200);
  });
}

// Reset form
if (formResetBtn) {
  formResetBtn.addEventListener('click', () => {
    contactForm.reset();
    Object.keys(fields).forEach(key => {
      const { el, errorEl } = fields[key];
      if (el) {
        el.classList.remove('has-error');
        errorEl.textContent = '';
      }
    });
    formSuccess.setAttribute('hidden', '');
    formFields.style.display = '';
  });
}

/* ================================================================
   FLOATING CALL BUTTON — hide on desktop, show on mobile/tablet
   ================================================================ */
function toggleFab() {
  if (window.innerWidth <= 991) {
    fabCall.style.display = 'flex';
  } else {
    fabCall.style.display = 'none';
  }
}
toggleFab();
window.addEventListener('resize', toggleFab, { passive: true });

/* ================================================================
   NAVBAR LOGO — scroll to top on click
   ================================================================ */
document.querySelectorAll('a[href="#home"]').forEach(a => {
  a.addEventListener('click', e => {
    e.preventDefault();
    window.scrollTo({ top: 0, behavior: 'smooth' });
    history.pushState(null, '', '#home');
    closeNav();
  });
});

/* ================================================================
   SMOOTH SCROLL for all internal anchor links
   ================================================================ */
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function(e) {
    const targetId = this.getAttribute('href');
    if (targetId === '#home') return; // handled above

    const target = document.querySelector(targetId);
    if (!target) return;
    e.preventDefault();

    const navH   = navbar.offsetHeight;
    const top    = target.getBoundingClientRect().top + window.scrollY - navH;
    window.scrollTo({ top, behavior: 'smooth' });
    history.pushState(null, '', targetId);
  });
});

/* ================================================================
   SERVICE CARD TILT EFFECT (subtle, desktop only)
   ================================================================ */
if (window.matchMedia('(hover: hover)').matches) {
  document.querySelectorAll('.service-card').forEach(card => {
    card.addEventListener('mousemove', e => {
      const rect   = card.getBoundingClientRect();
      const x      = e.clientX - rect.left - rect.width / 2;
      const y      = e.clientY - rect.top - rect.height / 2;
      const rotX   = (-y / (rect.height / 2)) * 3;
      const rotY   = (x / (rect.width / 2)) * 3;
      card.style.transform = `translateY(-6px) rotateX(${rotX}deg) rotateY(${rotY}deg)`;
      card.style.transition = 'transform 0.1s linear, box-shadow 0.25s ease, border-color 0.25s ease';
    });
    card.addEventListener('mouseleave', () => {
      card.style.transform = '';
      card.style.transition = 'transform 0.4s ease, box-shadow 0.25s ease, border-color 0.25s ease';
    });
  });
}

/* ================================================================
   PRELOAD HERO IMAGE — ensure it's cached for fastest paint
   ================================================================ */
(function preloadHeroImg() {
  const link = document.createElement('link');
  link.rel = 'preload';
  link.as = 'image';
  link.href = 'assets/bhavya.jpeg';
  document.head.appendChild(link);
})();

(() => {
  const launch = document.getElementById('chatLaunch');
  const box = document.getElementById('chatbox');
  const close = document.getElementById('chatClose');
  const form = document.getElementById('chatForm');
  const body = document.getElementById('chatBody');
  const input = document.getElementById('chatMessage');

  // Mobile navbar: scrolling never reveals it automatically. Use the floating toggle.
  const navbar = document.getElementById('mainNavbar');
  let lastScrollY = window.scrollY;
  let scrollTicking = false;
  const navToggle = document.createElement('button');
  navToggle.type = 'button';
  navToggle.className = 'mobile-nav-reveal';
  navToggle.setAttribute('aria-label', 'Show navigation menu');
  navToggle.innerHTML = '<i class="fa-solid fa-bars"></i>';
  document.body.appendChild(navToggle);

  function showNavToggle(show) {
    navToggle.classList.toggle('is-visible', !!show);
  }
  navToggle.addEventListener('click', () => {
    navbar?.classList.remove('navbar-scroll-hidden');
    showNavToggle(false);
    lastScrollY = window.scrollY;
  });

  function updateNavbarOnScroll() {
    if (!navbar) return;
    const mobile = window.matchMedia('(max-width: 991.98px)').matches;
    const currentY = window.scrollY;
    if (!mobile || currentY < 24) {
      navbar.classList.remove('navbar-scroll-hidden');
      showNavToggle(false);
    } else if (currentY > lastScrollY + 7) {
      navbar.classList.add('navbar-scroll-hidden');
      showNavToggle(true);
      const collapse = document.getElementById('nav');
      if (collapse && collapse.classList.contains('show') && window.bootstrap) {
        window.bootstrap.Collapse.getOrCreateInstance(collapse).hide();
      }
    }
    // Scrolling up intentionally does not reveal the navbar; the toggle must be tapped.
    lastScrollY = currentY;
    scrollTicking = false;
  }

  window.addEventListener('scroll', () => {
    if (!scrollTicking) {
      window.requestAnimationFrame(updateNavbarOnScroll);
      scrollTicking = true;
    }
  }, { passive: true });

  window.addEventListener('resize', () => {
    if (window.innerWidth > 991) {
      navbar?.classList.remove('navbar-scroll-hidden');
      showNavToggle(false);
    }
  });

  document.querySelectorAll('#nav .nav-link, #nav .dropdown-item, #nav .btn').forEach(link => {
    link.addEventListener('click', () => {
      const collapse = document.getElementById('nav');
      if (collapse?.classList.contains('show') && window.bootstrap) {
        window.bootstrap.Collapse.getOrCreateInstance(collapse).hide();
      }
    });
  });

  // Chat panel sizing follows the visible mobile viewport (including the keyboard).
  function updateChatViewport() {
    if (!box) return;
    const height = window.visualViewport ? window.visualViewport.height : window.innerHeight;
    box.style.setProperty('--chat-viewport-height', `${height}px`);
  }
  updateChatViewport();
  window.visualViewport?.addEventListener('resize', updateChatViewport);

  function openChat() {
    if (!box) return;
    box.classList.add('open');
    document.body.classList.add('chat-is-open');
    updateChatViewport();
    window.setTimeout(() => input?.focus(), 120);
  }
  function closeChat() {
    box?.classList.remove('open');
    document.body.classList.remove('chat-is-open');
    input?.blur();
  }
  launch?.addEventListener('click', openChat);
  close?.addEventListener('click', closeChat);

  // Keep the current section selected in red, including after page navigation.
  const path = window.location.pathname;
  document.querySelectorAll('.navbar .nav-link').forEach(link => {
    const href = link.getAttribute('href') || '';
    if ((href.includes('/catalog/') && path.startsWith('/catalog/')) ||
        (href === '/about/' && path === '/about/') ||
        (href === '/contact/' && path === '/contact/')) {
      link.classList.add('nav-current');
    }
  });

  document.querySelectorAll('.navbar .dropdown-item').forEach(link => {
    const u = new URL(link.href, window.location.origin);
    if (path.startsWith('/catalog/') && u.pathname === '/catalog/' &&
        u.search === window.location.search) link.classList.add('active');
  });

  // Reliable same-origin chat requests with the Django CSRF token.
  form?.addEventListener('submit', async event => {
    event.preventDefault();
    const message = input?.value.trim();
    if (!message) return;

    const sendButton = form.querySelector('button[type="submit"]');
    const csrfToken = form.querySelector('input[name="csrfmiddlewaretoken"]')?.value;
    const userMessage = document.createElement('p');
    userMessage.className = 'chat-user-message';
    userMessage.textContent = message;
    body.appendChild(userMessage);

    input.value = '';
    if (sendButton) sendButton.disabled = true;

    const typing = document.createElement('p');
    typing.className = 'chat-typing';
    typing.textContent = 'CODERED assistant is typing…';
    body.appendChild(typing);
    body.scrollTop = body.scrollHeight;

    const payload = new FormData(form);
    payload.set('message', message);

    try {
      const response = await fetch(form.action, {
        method: 'POST',
        body: payload,
        credentials: 'same-origin',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': csrfToken || '',
          'Accept': 'application/json'
        }
      });
      const raw = await response.text();
      let data = {};
      try { data = JSON.parse(raw); } catch (_) {}

      typing.remove();
      const reply = document.createElement('p');
      reply.className = 'chat-assistant-message';
      if (!response.ok) {
        reply.textContent = data.error || (response.status === 403
          ? 'Your session needs refreshing. Please reload the page and try again.'
          : 'The assistant could not respond. Please try again or use the Contact page.');
      } else {
        reply.textContent = data.reply || data.error || 'Please try again.';
      }
      body.appendChild(reply);
    } catch (_) {
      typing.remove();
      const reply = document.createElement('p');
      reply.className = 'chat-assistant-message';
      reply.textContent = 'Connection issue. Please check your internet connection or use the Contact page.';
      body.appendChild(reply);
    } finally {
      if (sendButton) sendButton.disabled = false;
      body.scrollTop = body.scrollHeight;
      if (window.matchMedia('(max-width: 700px)').matches) input?.focus();
    }
  });

  // Project catalogue: 10 projects per slide, swipe in either direction, infinite loop.
  document.querySelectorAll('[data-project-carousel]').forEach(carousel => {
    const track = carousel.querySelector('.project-carousel-track');
    if (!track) return;
    const originals = Array.from(track.children);
    const count = originals.length;
    if (!count) return;

    const counter = carousel.querySelector('.project-carousel-count');
    const previous = carousel.querySelector('[data-project-prev]');
    const next = carousel.querySelector('[data-project-next]');

    if (count === 1) {
      track.style.transform = 'translate3d(0,0,0)';
      if (counter) counter.textContent = '1 / 1';
      return;
    }

    const firstClone = originals[0].cloneNode(true);
    const lastClone = originals[count - 1].cloneNode(true);
    [firstClone, lastClone].forEach(clone => {
      clone.setAttribute('aria-hidden', 'true');
      clone.querySelectorAll('a,button').forEach(item => item.setAttribute('tabindex', '-1'));
    });
    track.insertBefore(lastClone, originals[0]);
    track.appendChild(firstClone);

    let index = 1;
    let startX = 0;
    let startY = 0;
    let isPointerDown = false;
    let isAnimating = false;

    function render(animate = true) {
      const shouldAnimate = animate && !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      track.style.transition = shouldAnimate ? 'transform .42s cubic-bezier(.22,.75,.25,1)' : 'none';
      track.style.transform = `translate3d(${-index * 100}%,0,0)`;
      if (counter) counter.textContent = `${((index - 1 + count) % count) + 1} / ${count}`;
      isAnimating = shouldAnimate;
    }
    function goNext() {
      if (isAnimating) return;
      index += 1;
      render();
    }
    function goPrevious() {
      if (isAnimating) return;
      index -= 1;
      render();
    }

    track.addEventListener('transitionend', event => {
      if (event.target !== track || event.propertyName !== 'transform') return;
      isAnimating = false;
      if (index === count + 1) {
        index = 1;
        render(false);
      } else if (index === 0) {
        index = count;
        render(false);
      }
    });

    previous?.addEventListener('click', goPrevious);
    next?.addEventListener('click', goNext);

    carousel.addEventListener('pointerdown', event => {
      if (event.pointerType === 'mouse' && event.button !== 0) return;
      startX = event.clientX;
      startY = event.clientY;
      isPointerDown = true;
    }, { passive: true });

    carousel.addEventListener('pointerup', event => {
      if (!isPointerDown) return;
      isPointerDown = false;
      const dx = event.clientX - startX;
      const dy = event.clientY - startY;
      if (Math.abs(dx) > 45 && Math.abs(dx) > Math.abs(dy) * 1.2) {
        if (dx < 0) goNext();
        else goPrevious();
      }
    }, { passive: true });

    carousel.addEventListener('pointercancel', () => { isPointerDown = false; });
    render(false);
  });

  // The project-type select is the compact replacement for the old filter tabs.
  const projectTypeSelect = document.getElementById('projectTypeSelect');
  projectTypeSelect?.addEventListener('change', () => {
    projectTypeSelect.form?.requestSubmit();
  });
})();

// Windows touchscreen / touch-device edge swipe: swipe right from the left edge to go back.
(function () {
  let startX = 0, startY = 0, startedAtEdge = false;
  document.addEventListener('touchstart', function (event) {
    if (!event.touches || event.touches.length !== 1) return;
    const touch = event.touches[0];
    startX = touch.clientX;
    startY = touch.clientY;
    startedAtEdge = startX <= 28;
  }, { passive: true });
  document.addEventListener('touchend', function (event) {
    if (!startedAtEdge || !event.changedTouches || event.changedTouches.length !== 1) return;
    const touch = event.changedTouches[0];
    const dx = touch.clientX - startX;
    const dy = Math.abs(touch.clientY - startY);
    if (dx > 110 && dy < 70 && window.history.length > 1) window.history.back();
    startedAtEdge = false;
  }, { passive: true });
})();

// Form keyboard flow: Enter moves to the next field; only the last field submits.
(function () {
  const FIELD_SELECTOR = [
    'input:not([type="hidden"]):not([type="submit"]):not([type="button"]):not([type="reset"]):not([disabled])',
    'select:not([disabled])',
    'textarea:not([disabled])'
  ].join(',');

  document.addEventListener('keydown', function (event) {
    if (event.key !== 'Enter' || event.defaultPrevented || event.isComposing) return;
    const field = event.target;
    if (!(field instanceof HTMLElement) || !field.matches(FIELD_SELECTOR)) return;
    if (field.tagName === 'TEXTAREA' || field.isContentEditable) return;
    if (field.readOnly || field.getAttribute('aria-readonly') === 'true') return;
    const form = field.form;
    if (!form || field.tagName === 'SELECT') return;

    // Chat has its own send-on-enter behaviour.
    if (form.id === 'chatForm') {
      event.preventDefault();
      form.requestSubmit();
      return;
    }

    const fields = Array.from(form.querySelectorAll(FIELD_SELECTOR)).filter(item =>
      item.getClientRects().length > 0 && !item.disabled && !item.readOnly &&
      item.type !== 'hidden' && item.getAttribute('aria-hidden') !== 'true'
    );
    const currentIndex = fields.indexOf(field);
    if (currentIndex < 0) return;
    event.preventDefault();
    const nextField = fields[currentIndex + 1];
    if (nextField) {
      nextField.focus();
      if (typeof nextField.select === 'function' &&
          ['text', 'email', 'search', 'tel', 'url', 'password', 'number'].includes(nextField.type)) {
        nextField.select();
      }
      return;
    }
    if (typeof form.requestSubmit === 'function') form.requestSubmit();
    else {
      const submitButton = form.querySelector('button[type="submit"], input[type="submit"]');
      if (submitButton) submitButton.click();
      else form.submit();
    }
  });
})();

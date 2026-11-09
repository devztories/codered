(() => {
  const launch = document.getElementById('chatLaunch');
  const box = document.getElementById('chatbox');
  const close = document.getElementById('chatClose');
  const form = document.getElementById('chatForm');
  const body = document.getElementById('chatBody');
  const input = document.getElementById('chatMessage');

  // Keep the navbar/header visible. Only collapse an expanded navigation menu
  // when the page itself scrolls, regardless of scroll direction.
  const navbar = document.getElementById('mainNavbar');
  const navCollapse = document.getElementById('nav');
  let previousPageScrollY = Math.max(0, window.scrollY || 0);

  window.addEventListener('scroll', () => {
    const currentPageScrollY = Math.max(0, window.scrollY || 0);
    const pageMoved = Math.abs(currentPageScrollY - previousPageScrollY) > 1;
    previousPageScrollY = currentPageScrollY;

    if (!pageMoved) return;

    // Mobile expanded menu: close it on either upward or downward page scroll.
    if (navCollapse?.classList.contains('show') && window.bootstrap) {
      window.bootstrap.Collapse.getOrCreateInstance(navCollapse).hide();
    }

    // Desktop Projects dropdown: close it on page scroll too.
    document.querySelectorAll('#mainNavbar .dropdown-toggle').forEach(toggle => {
      const dropdown = window.bootstrap?.Dropdown.getInstance(toggle);
      dropdown?.hide();
    });
  }, { passive: true });

  navCollapse?.addEventListener('shown.bs.collapse', () => {
    previousPageScrollY = Math.max(0, window.scrollY || 0);
  });

  // Bootstrap expands the Projects dropdown; choosing a dropdown item navigates
  // to its own destination and the mobile menu is collapsed by the handler below.
  document.querySelectorAll('#nav .dropdown-item, #nav > .navbar-nav > li:not(.dropdown) .nav-link, #nav .btn').forEach(link => {
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

  // Prevent Send from stealing focus from the composer on touch devices.
  // This keeps the mobile keyboard open for the next message.
  const chatSendButton = form?.querySelector('button[type="submit"]');
  chatSendButton?.addEventListener('pointerdown', event => event.preventDefault());
  chatSendButton?.addEventListener('mousedown', event => event.preventDefault());

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
      // Keep the existing input focus; avoid blur/refocus that collapses the mobile keyboard.
    }
  });


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
    if (field.type === 'date' || field.type === 'datetime-local' || field.type === 'time') return;
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

// Customer forms: block double submission and never show a stale form after Back/Forward.
(() => {
  document.addEventListener('submit', event => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement)) return;
    if ((form.method || '').toLowerCase() !== 'post') return;
    if (form.id === 'chatForm' || form.hasAttribute('data-allow-resubmit')) return;
    if (form.dataset.submitting === '1') { event.preventDefault(); return; }
    form.dataset.submitting = '1';
    form.querySelectorAll('button[type="submit"], button:not([type]), input[type="submit"]').forEach(btn => {
      setTimeout(() => { btn.disabled = true; btn.classList.add('disabled'); }, 0);
    });
  }, true);

  const resetFormsState = () => {
    document.querySelectorAll('form[method="post"]:not(#chatForm)').forEach(form => {
      delete form.dataset.submitting;
      form.querySelectorAll('button[disabled], input[type="submit"][disabled]').forEach(btn => {
        btn.disabled = false; btn.classList.remove('disabled');
      });
    });
  };

  window.addEventListener('pageshow', event => {
    const nav = (performance.getEntriesByType && performance.getEntriesByType('navigation')[0]) || null;
    const fromHistory = event.persisted || (nav && nav.type === 'back_forward');
    if (fromHistory && document.querySelector('form[method="post"]:not(#chatForm)')) {
      // Page came from the browser history: fetch a fresh copy from the server
      // (payment/login pages then redirect when they are no longer valid).
      window.location.reload();
      return;
    }
    resetFormsState();
  });
})();

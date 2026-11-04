(() => {
  const launch = document.getElementById('chatLaunch');
  const box = document.getElementById('chatbox');
  const close = document.getElementById('chatClose');
  const form = document.getElementById('chatForm');
  const body = document.getElementById('chatBody');
  const input = document.getElementById('chatMessage');

  // Keep the brand and navigation visible while scrolling on every screen size.
  const navbar = document.getElementById('mainNavbar');
  navbar?.classList.remove('navbar-scroll-hidden');

  // A dropdown toggle must stay open inside the mobile menu so both project
  // destinations remain reachable. Close the menu only after a real item is chosen.
  document.querySelectorAll('#nav .dropdown-toggle').forEach(toggle => {
    toggle.addEventListener('click', event => {
      if (window.matchMedia('(max-width: 991.98px)').matches) event.preventDefault();
    });
  });
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

(function () {
  'use strict';

  var config = window.CODERED_PUSH_CONFIG || {};
  if (!config.isAuthenticated) return;
  if (!('serviceWorker' in navigator) || !('PushManager' in window) || !('Notification' in window)) return;
  if (!config.publicKey) {
    if (window.console) console.warn('Push notifications are not configured (VAPID_PUBLIC_KEY missing).');
    return;
  }

  var userKey = String(config.userId || 'user');
  var SNOOZE_KEY = 'codered-push-snooze-' + userKey;
  var SYNC_KEY = 'codered-push-synced-' + userKey;
  var SNOOZE_MS = 3 * 24 * 60 * 60 * 1000;

  function getItem(kind, key) {
    try { return window[kind].getItem(key); } catch (e) { return null; }
  }
  function setItem(kind, key, value) {
    try { window[kind].setItem(key, value); } catch (e) { /* storage unavailable */ }
  }

  function b64ToBytes(value) {
    var padding = '='.repeat((4 - value.length % 4) % 4);
    var raw = atob((value + padding).replace(/-/g, '+').replace(/_/g, '/'));
    return Uint8Array.from(raw, function (c) { return c.charCodeAt(0); });
  }

  function sameKey(buffer, bytes) {
    if (!buffer) return false;
    var a = new Uint8Array(buffer);
    if (a.length !== bytes.length) return false;
    for (var i = 0; i < a.length; i++) if (a[i] !== bytes[i]) return false;
    return true;
  }

  function csrf() {
    var meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.content : '';
  }

  function post(url, body) {
    return fetch(url, {
      method: 'POST',
      credentials: 'same-origin',
      headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrf(), 'X-Requested-With': 'XMLHttpRequest'},
      body: JSON.stringify(body)
    });
  }

  // Registers the service worker, creates (or reuses) the browser subscription
  // and stores it for the signed-in user.
  async function subscribe() {
    var registration = await navigator.serviceWorker.register('/notifications/sw.js', {scope: '/'});
    await navigator.serviceWorker.ready;
    var key = b64ToBytes(config.publicKey);
    var subscription = await registration.pushManager.getSubscription();
    if (subscription && !sameKey(subscription.options && subscription.options.applicationServerKey, key)) {
      await subscription.unsubscribe();
      subscription = null;
    }
    if (!subscription) {
      subscription = await registration.pushManager.subscribe({userVisibleOnly: true, applicationServerKey: key});
    }
    var response = await post(config.subscribeUrl, {subscription: subscription.toJSON()});
    if (!response.ok) throw new Error('subscription-save-failed');
    setItem('sessionStorage', SYNC_KEY, '1');
  }

  /* ---------- Popup ---------- */

  var BELL = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 8 3 8H3s3-1 3-8"/><path d="M10.3 20a1.94 1.94 0 0 0 3.4 0"/></svg>';
  var CHECK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>';
  var ALERT = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 9v4"/><path d="M12 17h.01"/><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/></svg>';

  var backdrop = null;
  var onKey = null;

  function closePopup() {
    if (!backdrop) return;
    var node = backdrop;
    backdrop = null;
    if (onKey) { document.removeEventListener('keydown', onKey); onKey = null; }
    node.classList.remove('show');
    window.setTimeout(function () { if (node.parentNode) node.parentNode.removeChild(node); }, 260);
  }

  function snoozeAndClose() {
    setItem('localStorage', SNOOZE_KEY, String(Date.now() + SNOOZE_MS));
    closePopup();
  }

  function make(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text) node.textContent = text;
    return node;
  }

  function render(state, opts) {
    if (!backdrop) return;
    var card = backdrop.querySelector('.cr-push');
    card.className = 'cr-push' + (state === 'ok' ? ' is-ok' : state === 'error' ? ' is-error' : '');
    card.replaceChildren();

    var icon = make('div', 'cr-push-icon');
    icon.innerHTML = state === 'ok' ? CHECK : state === 'error' ? ALERT : BELL;
    var title = make('h2', '', opts.title);
    title.id = 'crPushTitle';
    var text = make('p', '', opts.text);
    var actions = make('div', 'cr-push-actions');
    (opts.buttons || []).forEach(function (b) {
      var btn = make('button', 'cr-push-btn ' + b.kind, b.label);
      btn.type = 'button';
      btn.addEventListener('click', b.onClick);
      actions.appendChild(btn);
    });
    card.append(icon, title, text, actions);
    var first = actions.querySelector('button');
    if (first) first.focus();
  }

  function showAsk() {
    render('ask', {
      title: 'Turn on notifications',
      text: 'Get instant alerts for your project updates, payments and messages, even when CODERED is closed.',
      buttons: [
        {kind: 'primary', label: 'Allow notifications', onClick: allow},
        {kind: 'ghost', label: 'Not now', onClick: snoozeAndClose}
      ]
    });
  }

  async function allow() {
    var btn = backdrop && backdrop.querySelector('.cr-push-btn.primary');
    if (btn) { btn.disabled = true; btn.textContent = 'Please wait…'; }
    try {
      var permission = await Notification.requestPermission();
      if (permission === 'denied') {
        render('error', {
          title: 'Notifications are blocked',
          text: 'You can turn them on any time from your browser’s site settings.',
          buttons: [{kind: 'ghost', label: 'Close', onClick: closePopup}]
        });
        return;
      }
      if (permission !== 'granted') { snoozeAndClose(); return; }
      await subscribe();
      render('ok', {
        title: 'You’re all set',
        text: 'Notifications are on. We’ll let you know when something changes.',
        buttons: []
      });
      window.setTimeout(closePopup, 2200);
    } catch (error) {
      if (window.console) console.error('Push setup failed', error);
      render('error', {
        title: 'Couldn’t turn on notifications',
        text: 'Something went wrong while setting things up. Please try again.',
        buttons: [
          {kind: 'primary', label: 'Try again', onClick: allow},
          {kind: 'ghost', label: 'Close', onClick: closePopup}
        ]
      });
    }
  }

  function showPopup() {
    if (backdrop) return;
    backdrop = make('div', 'cr-push-backdrop');
    var card = make('div', 'cr-push');
    card.setAttribute('role', 'dialog');
    card.setAttribute('aria-modal', 'true');
    card.setAttribute('aria-labelledby', 'crPushTitle');
    backdrop.appendChild(card);
    backdrop.addEventListener('click', function (event) {
      if (event.target === backdrop) snoozeAndClose();
    });
    onKey = function (event) { if (event.key === 'Escape') snoozeAndClose(); };
    document.addEventListener('keydown', onKey);
    document.body.appendChild(backdrop);
    showAsk();
    window.requestAnimationFrame(function () { if (backdrop) backdrop.classList.add('show'); });
  }

  /* ---------- Start ---------- */

  function start() {
    var permission = Notification.permission;
    if (permission === 'granted') {
      // Already allowed: keep the subscription fresh in the background, no UI.
      if (getItem('sessionStorage', SYNC_KEY) !== '1') {
        subscribe().catch(function (error) { if (window.console) console.warn('Push sync failed', error); });
      }
      return;
    }
    if (permission !== 'default') return;
    var until = Number(getItem('localStorage', SNOOZE_KEY) || 0);
    if (until > Date.now()) return;
    window.setTimeout(showPopup, 1500);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();

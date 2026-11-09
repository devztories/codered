(function () {
  const button = document.getElementById('enablePushNotifications');
  const config = window.CODERED_PUSH_CONFIG || {};
  if (!button) return;
  const b64ToBytes = (value) => { const padding = '='.repeat((4 - value.length % 4) % 4); const raw = atob((value + padding).replace(/-/g, '+').replace(/_/g, '/')); return Uint8Array.from([...raw].map(c => c.charCodeAt(0))); };
  const csrf = () => document.querySelector('meta[name="csrf-token"]')?.content || '';
  const post = (url, body) => fetch(url, {method:'POST', credentials:'same-origin', headers:{'Content-Type':'application/json','X-CSRFToken':csrf()}, body:JSON.stringify(body)});
  if (!('serviceWorker' in navigator) || !('PushManager' in window) || !('Notification' in window)) { button.textContent = 'Push not supported'; button.disabled = true; return; }
  button.addEventListener('click', async () => {
    try {
      if (!config.publicKey) { alert('Push notifications are not configured yet. Add VAPID keys in Vercel Environment Variables.'); return; }
      button.disabled = true; button.textContent = 'Enabling…';
      const permission = await Notification.requestPermission();
      if (permission !== 'granted') { button.textContent = 'Enable push'; alert('Please allow notifications in your browser settings.'); return; }
      const registration = await navigator.serviceWorker.register('/notifications/sw.js', {scope:'/'});
      await navigator.serviceWorker.ready;
      let subscription = await registration.pushManager.getSubscription();
      if (!subscription) subscription = await registration.pushManager.subscribe({userVisibleOnly:true, applicationServerKey:b64ToBytes(config.publicKey)});
      const response = await post(config.subscribeUrl, {subscription:subscription.toJSON()});
      if (!response.ok) throw new Error('Could not save notification subscription');
      button.textContent = 'Push enabled ✓';
    } catch (error) { console.error('Push setup failed', error); button.textContent = 'Enable push'; alert(error.message || 'Could not enable push notifications.'); }
    finally { button.disabled = false; }
  });
})();

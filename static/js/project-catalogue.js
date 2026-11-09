(function () {
  'use strict';
  const form = document.getElementById('projectFilterForm');
  const results = document.getElementById('projectResults');
  if (!form || !results) return;

  let activeController = null;
  let searchTimer = null;

  function setLoading(loading) {
    results.setAttribute('aria-busy', loading ? 'true' : 'false');
    results.classList.toggle('is-loading', loading);
  }

  async function loadResults(url, updateHistory) {
    if (activeController) activeController.abort();
    activeController = new AbortController();
    setLoading(true);
    try {
      const response = await fetch(url, {
        credentials: 'same-origin',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        signal: activeController.signal
      });
      if (!response.ok) throw new Error('Could not load projects');
      const html = await response.text();
      const doc = new DOMParser().parseFromString(html, 'text/html');
      const freshResults = doc.querySelector('#projectResults');
      if (!freshResults) throw new Error('Project results were not found');
      results.innerHTML = freshResults.innerHTML;

      // Keep filter controls in sync when navigating between pages or using browser history.
      const freshForm = doc.querySelector('#projectFilterForm');
      if (freshForm) {
        ['type', 'q', 'category'].forEach(name => {
          const current = form.elements.namedItem(name);
          const incoming = freshForm.elements.namedItem(name);
          if (current && incoming) current.value = incoming.value;
        });
      }
      if (updateHistory) history.pushState({ projectCatalogue: true }, '', url);
    } catch (error) {
      if (error.name !== 'AbortError') {
        // Graceful fallback: retain normal navigation if the AJAX request fails.
        window.location.assign(url);
      }
    } finally {
      if (activeController && !activeController.signal.aborted) setLoading(false);
    }
  }

  function filteredUrl() {
    const params = new URLSearchParams(new FormData(form));
    params.delete('page');
    const query = params.toString();
    return form.action + (query ? '?' + query : '');
  }

  form.addEventListener('submit', event => {
    event.preventDefault();
    loadResults(filteredUrl(), true);
  });

  ['type', 'category'].forEach(name => {
    const control = form.elements.namedItem(name);
    if (control) control.addEventListener('change', () => loadResults(filteredUrl(), true));
  });

  const search = form.elements.namedItem('q');
  if (search) search.addEventListener('input', () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => loadResults(filteredUrl(), true), 420);
  });

  results.addEventListener('click', event => {
    const link = event.target.closest('a[data-project-page]');
    if (!link) return;
    event.preventDefault();
    loadResults(link.href, true);
  });

  window.addEventListener('popstate', () => {
    loadResults(window.location.href, false);
  });
})();

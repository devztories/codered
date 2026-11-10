(function () {
  'use strict';

  var form = document.getElementById('projectFilterForm');
  var results = document.getElementById('projectResults');
  if (!form || !results || !window.fetch || !window.DOMParser || !window.AbortController) return;

  var activeController = null;
  var searchTimer = null;
  var resizeTimer = null;
  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function currentUrl() {
    return window.location.pathname + window.location.search;
  }

  function finishResize() {
    results.style.height = '';
    results.classList.remove('is-resizing');
  }

  function syncForm(doc) {
    var freshForm = doc.querySelector('#projectFilterForm');
    if (!freshForm) return;
    ['type', 'q', 'category'].forEach(function (name) {
      var current = form.elements.namedItem(name);
      var incoming = freshForm.elements.namedItem(name);
      if (current && incoming) current.value = incoming.value;
    });
  }

  function syncChoice(doc) {
    var current = document.getElementById('projectChoice');
    var fresh = doc.getElementById('projectChoice');
    if (current && fresh) current.innerHTML = fresh.innerHTML;
  }

  function syncNav() {
    document.querySelectorAll('.navbar .dropdown-item').forEach(function (link) {
      var url;
      try { url = new URL(link.href, window.location.href); } catch (error) { return; }
      link.classList.toggle('active', url.pathname === window.location.pathname && url.search === window.location.search);
    });
  }

  async function loadResults(url, options) {
    options = options || {};
    if (activeController) activeController.abort();
    var controller = new AbortController();
    activeController = controller;
    clearTimeout(resizeTimer);
    resizeTimer = null;

    var startHeight = results.offsetHeight;
    results.style.height = startHeight + 'px';
    results.classList.add('is-resizing', 'is-loading');
    results.setAttribute('aria-busy', 'true');

    try {
      var response = await fetch(url, {
        credentials: 'same-origin',
        signal: controller.signal,
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      });
      if (!response.ok) throw new Error('Could not load projects');
      var doc = new DOMParser().parseFromString(await response.text(), 'text/html');
      var freshResults = doc.getElementById('projectResults');
      if (!freshResults) throw new Error('Project results were not found');

      results.innerHTML = freshResults.innerHTML;
      syncForm(doc);
      syncChoice(doc);

      var target = new URL(url, window.location.href);
      var targetPath = target.pathname + target.search;
      if (options.push !== false && targetPath !== currentUrl()) {
        history.pushState({ projectCatalogue: true }, '', targetPath);
      }
      syncNav();

      var endHeight = results.scrollHeight;
      results.classList.remove('is-loading');
      results.setAttribute('aria-busy', 'false');
      if (reduceMotion || Math.abs(endHeight - startHeight) < 2) {
        finishResize();
      } else {
        void results.offsetHeight;
        results.style.height = endHeight + 'px';
        resizeTimer = window.setTimeout(finishResize, 420);
      }

      if (options.scrollToResults) {
        var top = results.getBoundingClientRect().top + window.pageYOffset - 96;
        window.scrollTo({ top: Math.max(0, top), behavior: reduceMotion ? 'auto' : 'smooth' });
      }
    } catch (error) {
      if (error && error.name !== 'AbortError') window.location.assign(url);
    } finally {
      if (activeController === controller && !controller.signal.aborted) {
        results.classList.remove('is-loading');
        results.setAttribute('aria-busy', 'false');
        if (!resizeTimer) finishResize();
      }
    }
  }

  function filteredUrl() {
    var params = new URLSearchParams(new FormData(form));
    params.delete('page');
    var query = params.toString();
    return form.action + (query ? '?' + query : '');
  }

  form.addEventListener('submit', function (event) {
    event.preventDefault();
    clearTimeout(searchTimer);
    loadResults(filteredUrl(), { push: true });
  });

  ['type', 'category'].forEach(function (name) {
    var control = form.elements.namedItem(name);
    if (control) control.addEventListener('change', function () {
      loadResults(filteredUrl(), { push: true });
    });
  });

  var search = form.elements.namedItem('q');
  if (search) search.addEventListener('input', function () {
    clearTimeout(searchTimer);
    searchTimer = window.setTimeout(function () {
      loadResults(filteredUrl(), { push: true });
    }, 420);
  });

  results.addEventListener('click', function (event) {
    var link = event.target.closest && event.target.closest('a[data-project-page]');
    if (!link || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    loadResults(link.href, { push: true, scrollToResults: true });
  });

  window.addEventListener('popstate', function () {
    loadResults(currentUrl(), { push: false });
  });

  // Preserve the local desktop mouse-drag interaction for each horizontal row.
  var drag = null;
  var suppressClick = false;
  document.addEventListener('pointerdown', function (event) {
    if (event.pointerType !== 'mouse' || event.button !== 0) return;
    var row = event.target.closest && event.target.closest('[data-project-row]');
    if (!row || row.scrollWidth <= row.clientWidth + 2) return;
    drag = { row: row, x: event.clientX, left: row.scrollLeft, moved: false, id: event.pointerId };
  });

  document.addEventListener('pointermove', function (event) {
    if (!drag || event.pointerId !== drag.id) return;
    var delta = event.clientX - drag.x;
    if (!drag.moved && Math.abs(delta) > 5) {
      drag.moved = true;
      drag.row.classList.add('is-dragging');
      try { drag.row.setPointerCapture(event.pointerId); } catch (error) {}
    }
    if (drag.moved) drag.row.scrollLeft = drag.left - delta;
  });

  function endDrag() {
    if (!drag) return;
    var finished = drag;
    drag = null;
    if (!finished.moved) return;
    finished.row.classList.remove('is-dragging');
    var card = finished.row.querySelector('.project-card');
    if (card) {
      var gap = parseFloat(window.getComputedStyle(finished.row).columnGap) || 16;
      var step = card.offsetWidth + gap;
      finished.row.scrollTo({ left: Math.round(finished.row.scrollLeft / step) * step, behavior: reduceMotion ? 'auto' : 'smooth' });
    }
    suppressClick = true;
    window.setTimeout(function () { suppressClick = false; }, 0);
  }

  document.addEventListener('pointerup', endDrag);
  document.addEventListener('pointercancel', endDrag);
  document.addEventListener('click', function (event) {
    if (suppressClick) {
      event.preventDefault();
      event.stopPropagation();
    }
  }, true);
  document.addEventListener('dragstart', function (event) {
    if (event.target.closest && event.target.closest('[data-project-row]')) event.preventDefault();
  });
})();

(function () {
  const roots = document.querySelectorAll("[data-notifications-root]");
  if (!roots.length) return;

  const csrf = document.querySelector('meta[name="csrf-token"]')?.content || "";
  const feedUrl = "/notifications/feed/";

  function render(root, data) {
    const badge = root.querySelector(".notification-count");
    const list = root.querySelector(".notification-items");
    const count = Number(data.unread_count || 0);
    if (badge) {
      badge.textContent = count > 99 ? "99+" : String(count);
      badge.hidden = count < 1;
    }
    if (!list) return;
    if (!data.items || !data.items.length) {
      list.innerHTML = '<p class="notification-empty">You are all caught up.</p>';
      return;
    }
    list.replaceChildren();
    data.items.forEach(function (item) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "notification-item" + (item.is_read ? "" : " unread");
      const title = document.createElement("strong");
      title.textContent = String(item.title || "");
      const message = document.createElement("span");
      message.textContent = String(item.message || "");
      const date = document.createElement("small");
      date.textContent = item.created_at ? new Date(item.created_at).toLocaleString() : "";
      button.append(title, message, date);
      button.addEventListener("click", async function () {
        try {
          await fetch("/notifications/" + item.id + "/read/", {
            method: "POST",
            headers: {"X-CSRFToken": csrf, "X-Requested-With": "XMLHttpRequest"}
          });
        } catch (e) {}
        if (item.url && item.url.startsWith("/") && !item.url.startsWith("//")) window.location.assign(item.url);
        else refresh();
      });
      list.appendChild(button);
    });
  }

  async function refresh() {
    try {
      const response = await fetch(feedUrl, {
        credentials: "same-origin",
        headers: {"X-Requested-With": "XMLHttpRequest"}
      });
      if (!response.ok) return;
      const data = await response.json();
      roots.forEach(root => render(root, data));
    } catch (e) {
      // Keep the main website usable if the notification service is unavailable.
    }
  }

  roots.forEach(function (root) {
    const bell = root.querySelector(".notification-bell");
    const panel = root.querySelector(".notification-popover");
    const readAll = root.querySelector(".notification-read-all");
    if (bell && panel) {
      bell.addEventListener("click", function () {
        panel.hidden = !panel.hidden;
        bell.setAttribute("aria-expanded", String(!panel.hidden));
        if (!panel.hidden) refresh();
      });
      document.addEventListener("click", function (event) {
        if (!root.contains(event.target)) {
          panel.hidden = true;
          bell.setAttribute("aria-expanded", "false");
        }
      });
    }
    if (readAll) {
      readAll.addEventListener("click", async function () {
        try {
          await fetch("/notifications/read-all/", {
            method: "POST",
            headers: {"X-CSRFToken": csrf, "X-Requested-With": "XMLHttpRequest"}
          });
          refresh();
        } catch (e) {}
      });
    }
  });

  refresh();
  window.setInterval(refresh, 8000);
})();

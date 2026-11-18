// Status banners (info / warning / error) and a small toast.

const ICONS = {
  info: '<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><g fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M12 11v5.5M12 7.6v.1"/></g></svg>',
  warning: '<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><g fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.3 4.2 2.6 17.6A2 2 0 0 0 4.3 20.6h15.4a2 2 0 0 0 1.7-3L13.7 4.2a2 2 0 0 0-3.4 0Z"/><path d="M12 9.5v4.2M12 17v.1"/></g></svg>',
  error: '<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><g fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="m9 9 6 6M15 9l-6 6"/></g></svg>',
};

export class Banners {
  #container;
  #items = new Map();

  constructor(container) {
    this.#container = container;
  }

  /** Show (or replace) the banner identified by ``key``. */
  show(key, { level = "info", title, message, actions = [] }) {
    const banner = document.createElement("div");
    banner.className = `banner banner--${level}`;
    banner.setAttribute("role", level === "error" ? "alert" : "status");
    banner.innerHTML = `<span class="banner__icon">${ICONS[level] ?? ICONS.info}</span>`;

    const body = document.createElement("div");
    body.className = "banner__body";
    if (title) {
      const titleEl = document.createElement("p");
      titleEl.className = "banner__title";
      titleEl.textContent = title;
      body.append(titleEl);
    }
    const text = document.createElement("p");
    text.className = "banner__text";
    text.textContent = message;
    body.append(text);

    if (actions.length) {
      const bar = document.createElement("div");
      bar.className = "banner__actions";
      for (const action of actions) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = action.primary ? "btn btn--primary" : "btn";
        button.textContent = action.label;
        button.addEventListener("click", action.onClick);
        bar.append(button);
      }
      body.append(bar);
    }
    banner.append(body);

    const existing = this.#items.get(key);
    if (existing) existing.replaceWith(banner);
    else this.#container.append(banner);
    this.#items.set(key, banner);
  }

  remove(key) {
    this.#items.get(key)?.remove();
    this.#items.delete(key);
  }

  removeByPrefix(prefix) {
    for (const key of [...this.#items.keys()]) {
      if (key.startsWith(prefix)) this.remove(key);
    }
  }

  has(key) {
    return this.#items.has(key);
  }
}

export class Toast {
  #element;
  #timer = 0;

  constructor(element) {
    this.#element = element;
  }

  show(message, duration = 2200) {
    this.#element.textContent = message;
    this.#element.classList.add("is-visible");
    clearTimeout(this.#timer);
    this.#timer = setTimeout(() => this.#element.classList.remove("is-visible"), duration);
  }
}

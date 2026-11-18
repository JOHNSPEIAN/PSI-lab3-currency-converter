// Light/dark switch: follows the system until the user picks a theme (FR-017).

const STORAGE_KEY = "cc.theme";

function readStored() {
  try {
    const value = localStorage.getItem(STORAGE_KEY);
    return value === "light" || value === "dark" ? value : null;
  } catch {
    return null;
  }
}

function store(value) {
  try {
    localStorage.setItem(STORAGE_KEY, value);
  } catch {
    /* storage may be unavailable (private mode); the switch still works for this session */
  }
}

export class ThemeSwitch {
  #button;
  #root;
  #media = window.matchMedia("(prefers-color-scheme: dark)");

  constructor(button, root = document.documentElement) {
    this.#button = button;
    this.#root = root;
  }

  init() {
    const stored = readStored();
    if (stored) this.#root.dataset.theme = stored;
    this.#button.addEventListener("click", () => this.toggle());
    this.#media.addEventListener("change", () => this.#sync());
    this.#sync();
  }

  current() {
    return this.#root.dataset.theme || (this.#media.matches ? "dark" : "light");
  }

  toggle() {
    const next = this.current() === "dark" ? "light" : "dark";
    this.#root.dataset.theme = next;
    store(next);
    this.#sync();
  }

  #sync() {
    const mode = this.current();
    this.#button.dataset.mode = mode;
    const label = mode === "dark" ? "Включить светлую тему" : "Включить тёмную тему";
    this.#button.setAttribute("aria-label", label);
    this.#button.title = label;
  }
}

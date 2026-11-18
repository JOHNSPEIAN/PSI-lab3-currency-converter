// Searchable currency picker (FR-002): popular currencies first, full keyboard support.

const POPULAR = ["MDL", "EUR", "USD", "RON", "UAH", "RUB", "GBP"];

const SYMBOLS = {
  MDL: "L", USD: "$", EUR: "€", GBP: "£", RUB: "₽", UAH: "₴", RON: "lei", JPY: "¥", CNY: "¥",
  CHF: "Fr", TRY: "₺", PLN: "zł", KZT: "₸", GEL: "₾", ILS: "₪", INR: "₹", KRW: "₩", AZN: "₼",
  AMD: "֏", BYN: "Br", CZK: "Kč", SEK: "kr", NOK: "kr", DKK: "kr", HUF: "Ft", BGN: "лв",
  CAD: "C$", AUD: "A$", NZD: "NZ$", HKD: "HK$", SGD: "S$", ISK: "kr", RSD: "дин", MKD: "ден",
};

const CHEVRON = '<svg class="picker__chevron" viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" d="m6 9 6 6 6-6"/></svg>';
const SEARCH = '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><g fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><circle cx="11" cy="11" r="6.5"/><path d="m20 20-4-4"/></g></svg>';
const CHECK = '<svg class="picker__check" viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" d="m5 12.5 4.5 4.5L19 7.5"/></svg>';

export function currencySymbol(code) {
  return SYMBOLS[code] ?? code.slice(0, 2);
}

export function currencyHue(code) {
  let hash = 7;
  for (const ch of code) hash = (hash * 31 + ch.charCodeAt(0)) % 360;
  return hash;
}

export function createBadge(code, small = false) {
  const badge = document.createElement("span");
  badge.className = small ? "badge badge--sm" : "badge";
  badge.textContent = currencySymbol(code);
  badge.style.setProperty("--hue", String(currencyHue(code)));
  badge.setAttribute("aria-hidden", "true");
  return badge;
}

let pickerCount = 0;

export class CurrencyPicker extends EventTarget {
  #root;
  #button;
  #popover;
  #search;
  #list;
  #currencies = [];
  #value = null;
  #visible = [];
  #active = -1;
  #id;
  #onOutside = (event) => {
    if (!this.#root.contains(event.target)) this.close();
  };

  constructor(root, { labelId } = {}) {
    super();
    this.#root = root;
    this.#id = `picker-${++pickerCount}`;
    root.classList.add("picker", "is-loading");

    this.#button = document.createElement("button");
    this.#button.type = "button";
    this.#button.className = "picker__button";
    this.#button.setAttribute("aria-haspopup", "listbox");
    this.#button.setAttribute("aria-expanded", "false");
    if (labelId) this.#button.setAttribute("aria-labelledby", `${labelId} ${this.#id}-code`);
    this.#renderButton();

    this.#popover = document.createElement("div");
    this.#popover.className = "picker__popover";
    this.#popover.hidden = true;
    this.#popover.innerHTML = `<label class="picker__search">${SEARCH}<input type="search" placeholder="Код или название" aria-label="Поиск валюты" autocomplete="off" spellcheck="false"></label><ul class="picker__list" role="listbox" id="${this.#id}-list"></ul>`;
    this.#search = this.#popover.querySelector("input");
    this.#list = this.#popover.querySelector("ul");
    this.#search.setAttribute("aria-controls", `${this.#id}-list`);

    root.append(this.#button, this.#popover);
    this.#bind();
  }

  get value() {
    return this.#value;
  }

  set value(code) {
    this.#value = code;
    this.#renderButton();
  }

  get currencies() {
    return this.#currencies;
  }

  setCurrencies(currencies) {
    this.#currencies = currencies;
    this.#root.classList.remove("is-loading");
    if (!currencies.some((c) => c.code === this.#value)) {
      const fallback = POPULAR.find((code) => currencies.some((c) => c.code === code));
      this.#value = fallback ?? currencies[0]?.code ?? null;
    }
    this.#renderButton();
  }

  setLoading(loading) {
    this.#root.classList.toggle("is-loading", loading);
  }

  find(code) {
    return this.#currencies.find((c) => c.code === code);
  }

  open() {
    if (!this.#currencies.length || !this.#popover.hidden) return;
    this.#popover.hidden = false;
    this.#button.setAttribute("aria-expanded", "true");
    this.#search.value = "";
    this.#renderList("");
    document.addEventListener("pointerdown", this.#onOutside);
    this.#search.focus({ preventScroll: true });
  }

  close({ focusButton = false } = {}) {
    if (this.#popover.hidden) return;
    this.#popover.hidden = true;
    this.#button.setAttribute("aria-expanded", "false");
    document.removeEventListener("pointerdown", this.#onOutside);
    if (focusButton) this.#button.focus();
  }

  #bind() {
    this.#button.addEventListener("click", () => (this.#popover.hidden ? this.open() : this.close()));
    this.#button.addEventListener("keydown", (event) => {
      if (event.key === "ArrowDown" || event.key === "ArrowUp") {
        event.preventDefault();
        this.open();
      }
    });
    this.#search.addEventListener("input", () => this.#renderList(this.#search.value));
    this.#search.addEventListener("keydown", (event) => this.#onKey(event));
    this.#list.addEventListener("pointermove", (event) => {
      const option = event.target.closest(".picker__option");
      if (option) this.#setActive(Number(option.dataset.index), false);
    });
    this.#list.addEventListener("click", (event) => {
      const option = event.target.closest(".picker__option");
      if (option) this.#select(option.dataset.code);
    });
  }

  #onKey(event) {
    switch (event.key) {
      case "ArrowDown":
        event.preventDefault();
        this.#setActive(Math.min(this.#active + 1, this.#visible.length - 1));
        break;
      case "ArrowUp":
        event.preventDefault();
        this.#setActive(Math.max(this.#active - 1, 0));
        break;
      case "Enter":
        event.preventDefault();
        if (this.#visible[this.#active]) this.#select(this.#visible[this.#active].code);
        break;
      case "Escape":
        event.preventDefault();
        this.close({ focusButton: true });
        break;
      case "Tab":
        this.close();
        break;
      default:
    }
  }

  #select(code) {
    const changed = code !== this.#value;
    this.value = code;
    this.close({ focusButton: true });
    if (changed) this.dispatchEvent(new CustomEvent("change", { detail: { code } }));
  }

  #renderButton() {
    const currency = this.find(this.#value);
    const code = currency?.code ?? this.#value ?? "———";
    this.#button.replaceChildren();
    this.#button.append(createBadge(code === "———" ? "?" : code));
    const text = document.createElement("span");
    text.className = "picker__text";
    const codeEl = document.createElement("span");
    codeEl.className = "picker__code";
    codeEl.id = `${this.#id}-code`;
    codeEl.textContent = code;
    const nameEl = document.createElement("span");
    nameEl.className = "picker__name";
    nameEl.textContent = currency?.name ?? "Загрузка…";
    text.append(codeEl, nameEl);
    this.#button.append(text);
    this.#button.insertAdjacentHTML("beforeend", CHEVRON);
  }

  #matches(currency, query) {
    if (!query) return true;
    const q = query.trim().toLowerCase();
    return currency.code.toLowerCase().includes(q) || currency.name.toLowerCase().includes(q);
  }

  #renderList(query) {
    const matches = this.#currencies.filter((c) => this.#matches(c, query));
    const popular = query ? [] : POPULAR.map((code) => matches.find((c) => c.code === code)).filter(Boolean);
    const rest = query ? matches : matches.filter((c) => !POPULAR.includes(c.code));
    this.#visible = [...popular, ...rest];
    this.#list.replaceChildren();

    if (!this.#visible.length) {
      const empty = document.createElement("li");
      empty.className = "picker__empty";
      empty.textContent = "Ничего не найдено";
      this.#list.append(empty);
      this.#active = -1;
      return;
    }
    if (popular.length) this.#list.append(this.#group("Популярные"));
    popular.forEach((c, i) => this.#list.append(this.#option(c, i)));
    if (popular.length && rest.length) this.#list.append(this.#group("Все валюты"));
    rest.forEach((c, i) => this.#list.append(this.#option(c, popular.length + i)));

    const selected = this.#visible.findIndex((c) => c.code === this.#value);
    this.#setActive(query ? 0 : Math.max(selected, 0));
  }

  #group(title) {
    const li = document.createElement("li");
    li.className = "picker__group";
    li.setAttribute("role", "presentation");
    li.textContent = title;
    return li;
  }

  #option(currency, index) {
    const li = document.createElement("li");
    li.className = "picker__option";
    li.id = `${this.#id}-opt-${index}`;
    li.setAttribute("role", "option");
    li.setAttribute("aria-selected", String(currency.code === this.#value));
    li.dataset.code = currency.code;
    li.dataset.index = String(index);
    const text = document.createElement("span");
    text.className = "picker__option-text";
    const code = document.createElement("span");
    code.className = "picker__option-code";
    code.textContent = currency.code;
    const name = document.createElement("span");
    name.className = "picker__option-name";
    name.textContent = currency.name;
    text.append(code, name);
    const rate = document.createElement("span");
    rate.className = "picker__option-rate";
    rate.textContent = currency.code === "MDL" ? "базовая" : `${currency.rate_display} MDL`;
    li.append(createBadge(currency.code, true), text, rate);
    li.insertAdjacentHTML("beforeend", CHECK);
    return li;
  }

  #setActive(index, scroll = true) {
    const options = this.#list.querySelectorAll(".picker__option");
    options[this.#active]?.classList.remove("is-active");
    this.#active = index;
    const option = options[index];
    if (!option) return;
    option.classList.add("is-active");
    this.#search.setAttribute("aria-activedescendant", option.id);
    if (scroll) option.scrollIntoView({ block: "nearest" });
  }
}

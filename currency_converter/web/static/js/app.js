// Page controller: wires the form, the pickers and the API together (contracts/ui.md).

import { ApiClient } from "./api.js";
import { CurrencyPicker } from "./currency-picker.js";
import { Banners, Toast } from "./notices.js";
import { ThemeSwitch } from "./theme.js";

const PAIR_KEY = "cc.pair";
const DEFAULT_PAIR = { source: "USD", target: "MDL" };

const $ = (id) => document.getElementById(id);

function isoDate(date) {
  const pad = (n) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

function today() {
  return isoDate(new Date());
}

function tomorrow() {
  const date = new Date();
  date.setDate(date.getDate() + 1);
  return isoDate(date);
}

function readPair() {
  try {
    const pair = JSON.parse(localStorage.getItem(PAIR_KEY) ?? "null");
    return pair?.source && pair?.target ? pair : DEFAULT_PAIR;
  } catch {
    return DEFAULT_PAIR;
  }
}

function storePair(pair) {
  try {
    localStorage.setItem(PAIR_KEY, JSON.stringify(pair));
  } catch {
    /* convenience only */
  }
}

class ConverterPage {
  constructor() {
    this.api = new ApiClient();
    this.el = {
      card: $("card"),
      form: $("converter-form"),
      amount: $("amount"),
      amountCode: $("amount-code"),
      swap: $("swap"),
      date: $("date"),
      todayBtn: $("today-btn"),
      convert: $("convert"),
      result: $("result"),
      resultFrom: $("result-from"),
      resultValue: $("result-value"),
      resultTarget: $("result-target"),
      resultRates: $("result-rates"),
      rateDateChip: $("rate-date-chip"),
      sourceChip: $("source-chip"),
      copy: $("copy-btn"),
      empty: $("empty-state"),
      emptyRetry: $("empty-retry"),
    };
    this.source = new CurrencyPicker($("source-picker"), { labelId: "source-label" });
    this.target = new CurrencyPicker($("target-picker"), { labelId: "target-label" });
    this.banners = new Banners($("banners"));
    this.toast = new Toast($("toast"));
    this.state = {
      mode: "live", // "saved" after the user accepted the saved copy (FR-013)
      ready: false,
      converting: false,
      hasResult: false,
      seq: 0,
      swapTurns: 0,
      last: null,
    };
  }

  async start() {
    new ThemeSwitch($("theme-toggle")).init();
    const pair = readPair();
    this.source.value = pair.source;
    this.target.value = pair.target;
    this.#initDate();
    this.#bind();
    this.#updateAmountCode();
    await this.loadRates();
  }

  // ---------- Rates ----------

  async loadRates() {
    this.state.ready = false;
    this.#refreshButton();
    this.source.setLoading(true);
    this.target.setLoading(true);
    this.el.card.setAttribute("aria-busy", "true");
    try {
      const data = await this.api.rates({ date: this.el.date.value || undefined, mode: this.state.mode });
      this.#applyCurrencies(data.currencies);
      this.#hideEmpty();
      this.banners.remove("error");
      if (this.state.mode === "live") this.banners.remove("offline");
    } catch (error) {
      if (error.code === "SOURCE_UNAVAILABLE") await this.#handleOffline(error, { starting: true });
      else if (error.code === "NO_SAVED_COPY") this.#leaveSavedMode(error);
      else this.#showError(error, () => this.loadRates());
    } finally {
      this.el.card.setAttribute("aria-busy", "false");
      this.#refreshButton();
    }
  }

  #applyCurrencies(currencies) {
    this.source.setCurrencies(currencies);
    this.target.setCurrencies(currencies);
    this.state.ready = true;
    this.#updateAmountCode();
  }

  // ---------- Conversion ----------

  async convert() {
    if (this.el.convert.disabled && !this.state.hasResult) return;
    const seq = ++this.state.seq;
    this.#clearFieldErrors();
    this.#setConverting(true);
    try {
      const data = await this.api.convert({
        amount: this.el.amount.value,
        source: this.source.value,
        target: this.target.value,
        date: this.el.date.value,
        mode: this.state.mode,
      });
      if (seq !== this.state.seq) return; // a newer request already took over
      this.banners.remove("error");
      this.#renderResult(data.conversion, data.lookup);
      storePair({ source: this.source.value, target: this.target.value });
    } catch (error) {
      if (seq !== this.state.seq) return;
      this.#hideResult(); // never leave an old number next to new, invalid input
      this.#handleConvertError(error);
    } finally {
      if (seq === this.state.seq) this.#setConverting(false);
    }
  }

  #renderResult(conversion, lookup) {
    const { el } = this;
    el.resultFrom.textContent = `${conversion.amount_display} ${conversion.source.code} =`;

    const number = document.createElement("span");
    number.className = "result__number";
    number.textContent = conversion.result_display;
    const code = document.createElement("span");
    code.className = "result__code";
    code.textContent = conversion.target.code;
    el.resultValue.replaceChildren(number, code);
    el.resultValue.classList.remove("is-updated");
    void el.resultValue.offsetWidth; // restart the animation
    el.resultValue.classList.add("is-updated");

    el.resultTarget.textContent = `${conversion.source.name} → ${conversion.target.name}`;
    el.resultRates.replaceChildren(
      this.#pill(`1 ${conversion.source.code} = ${conversion.rate_display} ${conversion.target.code}`),
      this.#pill(`1 ${conversion.target.code} = ${conversion.inverse_rate_display} ${conversion.source.code}`),
    );

    el.rateDateChip.querySelector(".chip__text").textContent = `Курс на ${lookup.used_date_display}`;
    const saved = lookup.source === "saved";
    el.sourceChip.classList.toggle("chip--saved", saved);
    el.sourceChip.querySelector(".chip__text").textContent = saved
      ? `${lookup.source_label} · сохранена ${lookup.saved_at_display}`
      : `${lookup.source_label} · bnm.md`;

    this.#renderNotices(lookup);
    el.result.hidden = false;
    el.result.classList.remove("is-stale");
    this.state.hasResult = true;
    this.state.last = { amount: el.amount.value, text: `${conversion.result} ${conversion.target.code}` };
  }

  #pill(text) {
    const span = document.createElement("span");
    span.className = "rate-pill";
    span.textContent = text;
    return span;
  }

  #hideResult() {
    this.el.result.hidden = true;
    this.state.hasResult = false;
  }

  // ---------- Notices & offline mode ----------

  #renderNotices(lookup) {
    this.banners.removeByPrefix("notice:");
    if (lookup.source === "live") {
      this.banners.remove("offline");
      this.banners.remove("saved-mode");
    }
    lookup.notices.forEach((notice, index) => {
      if (notice.kind === "saved_copy") this.#showSavedModeBanner(notice.message);
      else this.banners.show(`notice:${index}`, { level: notice.level, message: notice.message });
    });
  }

  async #handleOffline(error, { starting = false } = {}) {
    const saved = error.details.saved;
    if (!saved) {
      if (starting && !this.state.ready) this.#showEmpty(error.message);
      else this.#showError(error, () => this.#retryLive());
      return;
    }
    this.banners.remove("error");
    this.banners.show("offline", {
      level: "warning",
      title: "Нет связи с НБМ",
      message: error.message,
      actions: [
        { label: `Использовать курс от ${saved.rate_date_display}`, primary: true, onClick: () => this.#useSaved() },
        { label: "Повторить", onClick: () => this.#retryLive() },
      ],
    });
    if (starting && !this.state.ready) {
      // Fill the pickers from the saved copy so the form is usable; live mode stays until accepted.
      try {
        const data = await this.api.rates({ mode: "saved" });
        this.#applyCurrencies(data.currencies);
      } catch {
        /* nothing else to show: the banner already explains the situation */
      }
    }
  }

  async #useSaved() {
    this.state.mode = "saved";
    this.banners.remove("offline");
    this.banners.remove("error");
    this.#showSavedModeBanner("Работаем с сохранённой копией курсов НБМ. Данные могут быть неактуальны.");
    if (!this.state.ready) await this.loadRates();
    if (this.#isFilled()) await this.convert();
  }

  async #tryLive() {
    this.state.mode = "live";
    this.banners.remove("saved-mode");
    await this.#retryLive();
  }

  async #retryLive() {
    this.banners.remove("offline");
    this.banners.remove("error");
    if (this.state.ready && this.#isFilled()) await this.convert();
    else await this.loadRates();
  }

  #leaveSavedMode(error) {
    this.state.mode = "live";
    this.banners.remove("saved-mode");
    this.#showError(error, () => this.#retryLive());
  }

  #showSavedModeBanner(message) {
    this.banners.show("saved-mode", {
      level: "warning",
      title: "Офлайн-режим",
      message,
      actions: [{ label: "Попробовать онлайн", onClick: () => this.#tryLive() }],
    });
  }

  #showEmpty(message) {
    this.el.form.hidden = true;
    this.el.result.hidden = true;
    this.el.empty.hidden = false;
    $("empty-text").textContent = message;
  }

  #hideEmpty() {
    this.el.form.hidden = false;
    this.el.empty.hidden = true;
  }

  // ---------- Errors ----------

  #handleConvertError(error) {
    if (error.code === "VALIDATION") {
      this.banners.remove("error");
      for (const field of error.details.fields ?? []) this.#showFieldError(field.field, field.message);
      return;
    }
    if (error.code === "SOURCE_UNAVAILABLE") {
      this.#handleOffline(error);
      return;
    }
    if (error.code === "NO_SAVED_COPY") {
      this.#leaveSavedMode(error);
      return;
    }
    if (error.code === "CURRENCY_NOT_AVAILABLE") {
      this.banners.remove("error");
      const field = this.source.value === error.details.currency ? "source" : "target";
      this.#showFieldError(field, error.message);
      return;
    }
    this.#showError(error, () => this.convert());
  }

  #fieldElement(name) {
    return this.el.form.querySelector(`.field[data-field="${name}"]`);
  }

  #showFieldError(name, message) {
    const field = this.#fieldElement(name);
    if (!field) return;
    field.classList.add("has-error", "is-shaking");
    field.addEventListener("animationend", () => field.classList.remove("is-shaking"), { once: true });
    $(`${name}-error`).textContent = message;
    if (name === "amount") this.el.amount.setAttribute("aria-invalid", "true");
    if (name === "date") this.el.date.setAttribute("aria-invalid", "true");
  }

  #clearFieldError(name) {
    this.#fieldElement(name)?.classList.remove("has-error", "is-shaking");
    const message = $(`${name}-error`);
    if (message) message.textContent = "";
    if (name === "amount") this.el.amount.removeAttribute("aria-invalid");
    if (name === "date") this.el.date.removeAttribute("aria-invalid");
  }

  #clearFieldErrors() {
    for (const name of ["amount", "source", "target", "date"]) this.#clearFieldError(name);
  }

  #showError(error, retry) {
    this.banners.show("error", {
      level: "error",
      title: "Не получилось",
      message: error.message,
      actions: retry ? [{ label: "Повторить", primary: true, onClick: retry }] : [],
    });
  }

  // ---------- UI state ----------

  #bind() {
    const { el } = this;
    el.form.addEventListener("submit", (event) => {
      event.preventDefault();
      if (!el.convert.disabled) this.convert();
    });
    el.amount.addEventListener("input", () => {
      this.#clearFieldError("amount");
      this.#refreshButton();
      if (this.state.hasResult) {
        el.result.classList.toggle("is-stale", el.amount.value !== this.state.last?.amount);
      }
    });
    for (const picker of [this.source, this.target]) {
      picker.addEventListener("change", () => this.#onPairChanged());
    }
    el.swap.addEventListener("click", () => this.#swap());
    el.date.addEventListener("change", () => this.#onDateChanged());
    el.todayBtn.addEventListener("click", () => {
      el.date.value = today();
      this.#onDateChanged();
    });
    el.copy.addEventListener("click", () => this.#copyResult());
    el.emptyRetry.addEventListener("click", () => this.loadRates());
  }

  #initDate() {
    const { date } = this.el;
    date.min = "2000-01-01";
    date.max = tomorrow();
    date.value = today();
  }

  #onPairChanged() {
    this.#clearFieldError("source");
    this.#clearFieldError("target");
    this.#updateAmountCode();
    storePair({ source: this.source.value, target: this.target.value });
    if (this.state.hasResult) this.convert();
  }

  #onDateChanged() {
    this.#clearFieldError("date");
    this.el.todayBtn.setAttribute("aria-pressed", String(this.el.date.value === today()));
    this.#refreshButton();
    if (this.state.hasResult) this.convert();
  }

  #swap() {
    const { source, target } = this;
    [source.value, target.value] = [target.value, source.value];
    this.state.swapTurns += 1;
    this.el.swap.style.setProperty("--swap-turn", `${this.state.swapTurns * 180}deg`);
    this.#onPairChanged();
  }

  #updateAmountCode() {
    this.el.amountCode.textContent = this.source.value ?? "";
  }

  #isFilled() {
    const { el } = this;
    return Boolean(el.amount.value.trim() && this.source.value && this.target.value && el.date.value);
  }

  #refreshButton() {
    this.el.convert.disabled = !(this.state.ready && this.#isFilled());
  }

  #setConverting(converting) {
    this.state.converting = converting;
    this.el.convert.classList.toggle("is-loading", converting);
    this.el.convert.setAttribute("aria-busy", String(converting));
  }

  async #copyResult() {
    if (!this.state.last) return;
    try {
      await navigator.clipboard.writeText(this.state.last.text);
      this.toast.show("Результат скопирован");
    } catch {
      this.toast.show("Не удалось скопировать");
    }
  }
}

new ConverterPage().start();

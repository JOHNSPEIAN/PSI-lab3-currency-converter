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
    };
    this.source = new CurrencyPicker($("source-picker"), { labelId: "source-label" });
    this.target = new CurrencyPicker($("target-picker"), { labelId: "target-label" });
    this.banners = new Banners($("banners"));
    this.toast = new Toast($("toast"));
    this.state = { ready: false, converting: false, hasResult: false, seq: 0, swapTurns: 0, last: null };
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
      const data = await this.api.rates({ date: this.el.date.value || undefined });
      this.#applyCurrencies(data.currencies);
      this.banners.remove("error");
    } catch (error) {
      this.#showError(error, () => this.loadRates());
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
    this.#setConverting(true);
    try {
      const data = await this.api.convert({
        amount: this.el.amount.value,
        source: this.source.value,
        target: this.target.value,
        date: this.el.date.value,
      });
      if (seq !== this.state.seq) return; // a newer request already took over
      this.banners.remove("error");
      this.#renderResult(data.conversion, data.lookup);
      storePair({ source: this.source.value, target: this.target.value });
    } catch (error) {
      if (seq !== this.state.seq) return;
      this.#hideResult();
      this.#showError(error, () => this.convert());
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

  // ---------- Errors ----------

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
  }

  #initDate() {
    const { date } = this.el;
    date.min = "2000-01-01";
    date.max = tomorrow();
    date.value = today();
  }

  #onPairChanged() {
    this.#updateAmountCode();
    storePair({ source: this.source.value, target: this.target.value });
    if (this.state.hasResult) this.convert();
  }

  #onDateChanged() {
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

  #refreshButton() {
    const { el } = this;
    const filled = el.amount.value.trim() !== "" && this.source.value && this.target.value && el.date.value;
    el.convert.disabled = !(this.state.ready && filled);
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

// Thin client for the local JSON API (contracts/http-api.md).

export class ApiError extends Error {
  constructor(status, error = {}) {
    super(error.message || "Ошибка запроса");
    this.status = status;
    this.code = error.code || "UNKNOWN";
    this.details = error;
  }
}

const LOCAL_SERVER_DOWN = {
  code: "LOCAL_SERVER",
  message: "Приложение не отвечает. Убедитесь, что программа запущена, и обновите страницу.",
};

export class ApiClient {
  async rates({ date, mode = "live" } = {}) {
    const params = new URLSearchParams({ mode });
    if (date) params.set("date", date);
    return this.#request(`/api/rates?${params}`);
  }

  async convert({ amount, source, target, date, mode = "live" }) {
    return this.#request("/api/convert", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ amount, source, target, date, mode }),
    });
  }

  async #request(url, init = {}) {
    let response;
    try {
      response = await fetch(url, { ...init, headers: { Accept: "application/json", ...init.headers } });
    } catch {
      throw new ApiError(0, LOCAL_SERVER_DOWN);
    }
    let data;
    try {
      data = await response.json();
    } catch {
      throw new ApiError(response.status, { code: "BAD_RESPONSE", message: "Некорректный ответ приложения." });
    }
    if (!response.ok || data.status !== "ok") {
      throw new ApiError(response.status, data.error);
    }
    return data;
  }
}

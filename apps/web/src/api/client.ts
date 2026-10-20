import type { OptimizeRequest, OptimizeResponse, Scenario } from "./types";

const BASE = "/api";

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...init,
    });
  } catch {
    throw new ApiError("Brak połączenia z API.", 0);
  }

  if (!response.ok) {
    throw new ApiError(await readErrorDetail(response), response.status);
  }
  return (await response.json()) as T;
}

async function readErrorDetail(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) {
      return body.detail
        .map((item) => (item as { msg?: string }).msg ?? JSON.stringify(item))
        .join("; ");
    }
  } catch {
    void 0;
  }
  return `Błąd ${response.status}`;
}

export const api = {
  scenarios: () => request<Scenario[]>("/scenarios"),
  optimize: (body: OptimizeRequest) =>
    request<OptimizeResponse>("/optimize", { method: "POST", body: JSON.stringify(body) }),
};

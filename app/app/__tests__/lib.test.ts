import { describe, it, expect, vi, beforeEach } from "vitest";
import { fetchApi, ApiError, ENDPOINT } from "../lib";

describe("ENDPOINT", () => {
  it("has all required endpoints", () => {
    expect(ENDPOINT.health).toContain("/api/v1/health");
    expect(ENDPOINT.documents).toContain("/api/v1/documents");
    expect(ENDPOINT.queries).toContain("/api/v1/queries");
    expect(ENDPOINT.metrics).toContain("/api/v1/metrics");
    expect(ENDPOINT.actions).toContain("/api/v1/agent/actions");
  });
});

describe("ApiError", () => {
  it("has name, message, and status", () => {
    const err = new ApiError("Not Found", 404);
    expect(err.name).toBe("ApiError");
    expect(err.message).toBe("Not Found");
    expect(err.status).toBe(404);
    expect(err).toBeInstanceOf(Error);
  });
});

describe("fetchApi", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("returns parsed JSON on success", async () => {
    const data = { status: "ok" };
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(data),
    } as Response);

    const result = await fetchApi<{ status: string }>("http://localhost/test");
    expect(result).toEqual(data);
  });

  it("throws ApiError on non-ok response", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: false,
      status: 500,
      statusText: "Internal Server Error",
    } as Response);

    await expect(fetchApi("http://localhost/test")).rejects.toThrow(ApiError);
    await expect(fetchApi("http://localhost/test")).rejects.toMatchObject({
      status: 500,
    });
  });

  it("propagates network errors", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new TypeError("Failed to fetch"));

    await expect(fetchApi("http://localhost/test")).rejects.toThrow(TypeError);
  });
});

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import HomePage from "../page";

function mockFetch(overrides: Record<string, unknown> = {}) {
  const defaults: Record<string, unknown> = {
    "/api/v1/health": { status: "ok" },
    "/api/v1/documents": [],
    "/api/v1/metrics": {
      documents: 0,
      chunks: 0,
      queries: 0,
      avg_query_latency_ms: 0,
      feedback_count: 0,
      avg_feedback_rating: null,
    },
    ...overrides,
  };

  return vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
    const url = typeof input === "string" ? input : (input as Request).url;
    for (const [key, value] of Object.entries(defaults)) {
      if (url.includes(key)) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(value),
        } as Response);
      }
    }
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve({}),
    } as Response);
  });
}

describe("HomePage", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders headings", async () => {
    mockFetch();
    render(<HomePage />);
    expect(screen.getByText("Knowledge Copilot")).toBeInTheDocument();
    expect(screen.getByText("1) 문서 업로드")).toBeInTheDocument();
    expect(screen.getByText("2) 질의")).toBeInTheDocument();
    expect(screen.getByText("3) 액션")).toBeInTheDocument();
    expect(screen.getByText("4) 문서/메트릭")).toBeInTheDocument();
  });

  it("shows empty state when no documents", async () => {
    mockFetch();
    render(<HomePage />);
    await waitFor(() => {
      expect(screen.getByText("업로드된 문서가 없습니다.")).toBeInTheDocument();
    });
  });

  it("shows offline banner when health check fails", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = typeof input === "string" ? input : (input as Request).url;
      if (url.includes("/health")) {
        return Promise.reject(new Error("offline"));
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(url.includes("/documents") ? [] : {}),
      } as Response);
    });

    render(<HomePage />);
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("API 서버에 연결할 수 없습니다");
    });
  });

  it("validates empty upload text", async () => {
    mockFetch();
    const user = userEvent.setup();
    render(<HomePage />);

    const uploadBtn = screen.getByText("문서 업로드");
    await user.click(uploadBtn);

    await waitFor(() => {
      expect(screen.getByText("텍스트를 입력하세요")).toBeInTheDocument();
    });
  });

  it("validates empty question", async () => {
    mockFetch();
    const user = userEvent.setup();
    render(<HomePage />);

    const askBtn = screen.getByText("질의 보내기");
    await user.click(askBtn);

    await waitFor(() => {
      expect(screen.getByText("질문을 입력하세요")).toBeInTheDocument();
    });
  });

  it("shows loading state during upload", async () => {
    let resolveUpload: (v: Response) => void;
    const uploadPromise = new Promise<Response>((r) => { resolveUpload = r; });

    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = typeof input === "string" ? input : (input as Request).url;
      if (url.includes("/documents") && !url.includes("?")) {
        return uploadPromise;
      }
      if (url.includes("/health")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ status: "ok" }) } as Response);
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(url.includes("/documents") ? [] : {}),
      } as Response);
    });

    const user = userEvent.setup();
    render(<HomePage />);

    const textarea = screen.getByPlaceholderText("질문 답변의 근거가 될 텍스트를 넣어주세요");
    await user.type(textarea, "test text");

    const uploadBtn = screen.getByText("문서 업로드");
    await user.click(uploadBtn);

    await waitFor(() => {
      expect(screen.getByText("업로드 중...")).toBeInTheDocument();
    });

    resolveUpload!({ ok: true, json: () => Promise.resolve({ id: "1", status: "ready", chunk_count: 1 }) } as Response);
  });

  it("displays metrics when loaded", async () => {
    mockFetch({
      "/api/v1/metrics": {
        documents: 3,
        chunks: 15,
        queries: 7,
        avg_query_latency_ms: 250,
        feedback_count: 2,
        avg_feedback_rating: 4.5,
      },
    });

    render(<HomePage />);

    await waitFor(() => {
      expect(screen.getByText("3")).toBeInTheDocument();
      expect(screen.getByText("15")).toBeInTheDocument();
      expect(screen.getByText("250ms")).toBeInTheDocument();
    });
  });

  it("has proper ARIA attributes", () => {
    mockFetch();
    render(<HomePage />);

    const forms = document.querySelectorAll("form");
    forms.forEach((form) => {
      expect(form).toHaveAttribute("aria-busy");
    });

    const sections = document.querySelectorAll("section[aria-labelledby]");
    expect(sections.length).toBeGreaterThanOrEqual(3);
  });

  it("has htmlFor/id connections on form fields", () => {
    mockFetch();
    render(<HomePage />);

    const projectLabel = screen.getByText("project_id");
    expect(projectLabel).toHaveAttribute("for", "projectId");
    expect(document.getElementById("projectId")).toBeInTheDocument();

    const questionLabel = screen.getByText("질문");
    expect(questionLabel).toHaveAttribute("for", "question");
    expect(document.getElementById("question")).toBeInTheDocument();
  });
});

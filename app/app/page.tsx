"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import Markdown from "react-markdown";
import { ENDPOINT, fetchApi, ApiError } from "./lib";

type DocumentItem = {
  id: string;
  filename: string | null;
  status: string;
  chunk_count: number;
  created_at: string;
};

type Citation = {
  chunk_id: string;
  document_id: string;
  text: string;
  score: number;
};

type QueryResponse = {
  id: string;
  answer: string;
  citations: Citation[];
  latency_ms: number;
  model: string;
  related_documents: string[];
};

type Metric = {
  documents: number;
  chunks: number;
  queries: number;
  avg_query_latency_ms: number;
  feedback_count: number;
  avg_feedback_rating: number | null;
};

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return `서버 오류 (${error.status})`;
  }
  return "네트워크 오류가 발생했습니다. 잠시 후 다시 시도하세요.";
}

const SOURCE_MAX = 5000;

function statusBadge(status: string) {
  const cls =
    status === "ready"
      ? "badge badge-ready"
      : status === "processing"
        ? "badge badge-processing"
        : "badge badge-error";
  return <span className={cls}>{status}</span>;
}

export default function HomePage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [metrics, setMetrics] = useState<Metric | null>(null);
  const [projectId, setProjectId] = useState("default");
  const [sourceText, setSourceText] = useState("");
  const [question, setQuestion] = useState("");
  const [queryResult, setQueryResult] = useState<QueryResponse | null>(null);
  const [actionResult, setActionResult] = useState<string>("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const sourceRef = useRef<HTMLTextAreaElement>(null);
  const questionRef = useRef<HTMLTextAreaElement>(null);

  const [apiOnline, setApiOnline] = useState(true);

  useEffect(() => {
    fetch(ENDPOINT.health)
      .then((res) => setApiOnline(res.ok))
      .catch(() => setApiOnline(false));
    void refreshAll();
  }, []);

  function autoResize(ref: React.RefObject<HTMLTextAreaElement | null>) {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${el.scrollHeight}px`;
  }

  async function refreshAll() {
    try {
      const [docs, metricPayload] = await Promise.all([
        fetchApi<DocumentItem[]>(`${ENDPOINT.documents}?project_id=${projectId}`),
        fetchApi<Metric>(`${ENDPOINT.metrics}?project_id=${projectId}`),
      ]);
      setDocuments(docs);
      setMetrics(metricPayload);
    } catch {
      setMessage("데이터를 불러오지 못했습니다.");
    }
  }

  async function upload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!sourceText.trim()) {
      setMessage("텍스트를 입력하세요");
      return;
    }
    setMessage("");
    setLoading(true);
    const form = new FormData();
    form.set("project_id", projectId);
    form.set("source_text", sourceText);

    try {
      await fetchApi(ENDPOINT.documents, { method: "POST", body: form });
      setSourceText("");
      setMessage("문서 업로드 완료");
      await refreshAll();
    } catch (error) {
      setMessage(errorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  async function ask(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!question.trim()) {
      setMessage("질문을 입력하세요");
      return;
    }
    setMessage("");
    setLoading(true);

    try {
      const payload = await fetchApi<QueryResponse>(ENDPOINT.queries, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ project_id: projectId, question }),
      });
      setQueryResult(payload);
      setQuestion("");
      await refreshAll();
    } catch (error) {
      setMessage(errorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  async function runAction() {
    setLoading(true);
    setActionResult("");

    try {
      const payload = await fetchApi<{ result: string }>(ENDPOINT.actions, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          project_id: projectId,
          type: "summary",
          payload: { documents: documents.map((doc) => doc.id) },
        }),
      });
      setActionResult(payload.result);
    } catch (error) {
      setActionResult(errorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      {!apiOnline && (
        <p className="banner-offline" role="alert">
          API 서버에 연결할 수 없습니다. 일부 기능이 제한됩니다.
        </p>
      )}
      <h1 id="title">Knowledge Copilot</h1>
      <p className="subtitle">RAG, 액션형 AI, API 로그 추적까지 포함한 포트폴리오 프로젝트</p>

      <div className="grid">
        <section className="card" aria-labelledby="upload-heading">
          <h2 id="upload-heading">1) 문서 업로드</h2>
          <form onSubmit={upload} aria-busy={loading}>
            <div className="form-field">
              <label htmlFor="projectId">project_id</label>
              <input
                id="projectId"
                value={projectId}
                onChange={(e) => setProjectId(e.target.value)}
              />
            </div>
            <div className="form-field">
              <label htmlFor="sourceText">
                텍스트 문서
                <span className="char-count">
                  {sourceText.length} / {SOURCE_MAX}
                </span>
              </label>
              <textarea
                ref={sourceRef}
                id="sourceText"
                rows={4}
                value={sourceText}
                maxLength={SOURCE_MAX}
                onChange={(e) => {
                  setSourceText(e.target.value);
                  autoResize(sourceRef);
                }}
                placeholder="질문 답변의 근거가 될 텍스트를 넣어주세요"
              />
            </div>
            <button type="submit" disabled={loading} aria-disabled={loading}>
              {loading ? "업로드 중..." : "문서 업로드"}
            </button>
          </form>
        </section>

        <section className="card" aria-labelledby="query-heading">
          <h2 id="query-heading">2) 질의</h2>
          <form onSubmit={ask} aria-busy={loading}>
            <div className="form-field">
              <label htmlFor="question">질문</label>
              <textarea
                ref={questionRef}
                id="question"
                rows={3}
                value={question}
                onChange={(e) => {
                  setQuestion(e.target.value);
                  autoResize(questionRef);
                }}
                placeholder="예: 이 문서의 핵심 결론은?"
              />
            </div>
            <button type="submit" disabled={loading} aria-disabled={loading}>
              {loading ? "질의 중..." : "질의 보내기"}
            </button>
          </form>
        </section>
      </div>

      {message ? (
        <p className="message" aria-live="polite">{message}</p>
      ) : null}

      {queryResult ? (
        <section className="card" aria-labelledby="result-heading">
          <h2 id="result-heading">질의 응답</h2>
          <div className="answer">
            <Markdown>{queryResult.answer}</Markdown>
          </div>
          <dl className="meta">
            <dt>모델</dt>
            <dd><span className="badge badge-ready">{queryResult.model}</span></dd>
            <dt>지연</dt>
            <dd>{queryResult.latency_ms}ms</dd>
          </dl>
          {queryResult.citations.length > 0 && (
            <>
              <h3>인용</h3>
              <ol className="citations">
                {queryResult.citations.map((c) => (
                  <li key={c.chunk_id}>
                    <strong>{c.document_id}</strong> {c.text}
                  </li>
                ))}
              </ol>
            </>
          )}
        </section>
      ) : null}

      <section className="card" aria-labelledby="action-heading">
        <h2 id="action-heading">3) 액션</h2>
        <button onClick={runAction} disabled={loading} aria-disabled={loading}>
          {loading ? "실행 중..." : "문서 요약 액션 실행"}
        </button>
        {actionResult ? <pre>{actionResult}</pre> : null}
      </section>

      <section className="card" aria-labelledby="metrics-heading">
        <h2 id="metrics-heading">4) 문서/메트릭</h2>
        {metrics ? (
          <dl className="meta">
            <dt>문서</dt>
            <dd>{metrics.documents}</dd>
            <dt>청크</dt>
            <dd>{metrics.chunks}</dd>
            <dt>질의</dt>
            <dd>{metrics.queries}</dd>
            <dt>평균 응답</dt>
            <dd>{metrics.avg_query_latency_ms}ms</dd>
            <dt>피드백</dt>
            <dd>{metrics.feedback_count}건</dd>
            <dt>평점</dt>
            <dd>{metrics.avg_feedback_rating ?? "N/A"}</dd>
          </dl>
        ) : null}
        {documents.length === 0 ? (
          <p className="empty">업로드된 문서가 없습니다.</p>
        ) : (
          <ul className="doc-list">
            {documents.map((doc) => (
              <li key={doc.id}>
                <span className="doc-name">{doc.filename ?? doc.id.slice(0, 8)}</span>
                {statusBadge(doc.status)}
                <span className="doc-chunks">chunks: {doc.chunk_count}</span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}

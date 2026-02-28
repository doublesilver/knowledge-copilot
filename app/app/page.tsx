"use client";

import { FormEvent, useEffect, useState } from "react";
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

  useEffect(() => {
    void refreshAll();
  }, []);

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
      <h1 id="title">Knowledge Copilot</h1>
      <p>RAG, 액션형 AI, API 로그 추적까지 포함한 포트폴리오 프로젝트</p>

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
              <label htmlFor="sourceText">텍스트 문서</label>
              <textarea
                id="sourceText"
                rows={10}
                value={sourceText}
                onChange={(e) => setSourceText(e.target.value)}
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
                id="question"
                rows={5}
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
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
          <p>{queryResult.answer}</p>
          <dl className="meta">
            <dt>모델</dt>
            <dd>{queryResult.model}</dd>
            <dt>지연</dt>
            <dd>{queryResult.latency_ms}ms</dd>
          </dl>
          <h3>인용</h3>
          <ol className="citations">
            {queryResult.citations.map((c) => (
              <li key={c.chunk_id}>
                <strong>{c.document_id}</strong> {c.text}
              </li>
            ))}
          </ol>
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
        <ul>
          {documents.map((doc) => (
            <li key={doc.id}>
              {doc.filename} / {doc.status} / chunks: {doc.chunk_count}
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}

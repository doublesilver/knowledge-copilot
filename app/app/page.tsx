"use client";

import { FormEvent, useEffect, useState } from "react";
import { ENDPOINT } from "./lib";

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
      const [docsRes, metricsRes] = await Promise.all([
        fetch(`${ENDPOINT.documents}?project_id=${projectId}`),
        fetch(`${ENDPOINT.metrics}?project_id=${projectId}`),
      ]);
      const docs = await docsRes.json();
      const metricPayload = await metricsRes.json();
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
      const response = await fetch(ENDPOINT.documents, {
        method: "POST",
        body: form,
      });
      if (!response.ok) {
        throw new Error("upload failed");
      }
      setSourceText("");
      setMessage("문서 업로드 완료");
      await refreshAll();
    } catch {
      setMessage("문서 업로드 실패");
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
      const response = await fetch(ENDPOINT.queries, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          project_id: projectId,
          question,
        }),
      });
      if (!response.ok) {
        setMessage("질의 처리 실패");
        return;
      }
      const payload: QueryResponse = await response.json();
      setQueryResult(payload);
      setQuestion("");
      await refreshAll();
    } catch {
      setMessage("네트워크 오류가 발생했습니다. 잠시 후 다시 시도하세요.");
    } finally {
      setLoading(false);
    }
  }

  async function runAction() {
    setLoading(true);
    setActionResult("");

    try {
      const response = await fetch(ENDPOINT.actions, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          project_id: projectId,
          type: "summary",
          payload: {
            documents: documents.map((doc) => doc.id),
          },
        }),
      });
      if (!response.ok) {
        setActionResult("액션 실행 실패");
        return;
      }
      const payload = await response.json();
      setActionResult(payload.result);
    } catch {
      setActionResult("네트워크 오류가 발생했습니다. 잠시 후 다시 시도하세요.");
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
          <p>
            모델: {queryResult.model} / 지연: {queryResult.latency_ms}ms
          </p>
          <pre>{queryResult.citations.map((c) => `- [${c.document_id}] ${c.text}`).join("\n")}</pre>
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
          <pre>
{`문서: ${metrics.documents}\n청크: ${metrics.chunks}\n질의: ${metrics.queries}\n평균 응답: ${metrics.avg_query_latency_ms}ms\n피드백: ${metrics.feedback_count}건 / 평점 ${metrics.avg_feedback_rating ?? "N/A"}`}
          </pre>
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

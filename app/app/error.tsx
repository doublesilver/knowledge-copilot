"use client";

export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main>
      <h1>오류가 발생했습니다</h1>
      <p>{error.message || "알 수 없는 오류가 발생했습니다."}</p>
      <button onClick={reset}>다시 시도</button>
    </main>
  );
}

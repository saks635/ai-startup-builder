import { Suspense } from "react";
import ResultsClient from "./results-client";

export default function ResultsPage() {
  return (
    <Suspense fallback={<main className="container"><p className="alert info">Loading results...</p></main>}>
      <ResultsClient />
    </Suspense>
  );
}

"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import { apiClient } from "@/lib/api";
import { clearSession, isAuthenticated } from "@/lib/auth";

function formatTimestamp(unixTs) {
  if (!unixTs) return "-";
  return new Date(unixTs * 1000).toLocaleString();
}

function statusClass(status) {
  if (status === "completed") return "completed";
  if (status === "failed") return "failed";
  if (status === "running") return "running";
  return "queued";
}

export default function ResultsClient() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const pollTimerRef = useRef(null);

  const jobId = searchParams.get("jobId");
  const [job, setJob] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
      return;
    }

    if (!jobId) {
      setError("Missing jobId in URL.");
      setLoading(false);
      return;
    }

    let isCancelled = false;

    async function poll() {
      try {
        const payload = await apiClient.getJob(jobId);
        if (isCancelled) return;

        setJob(payload);
        setError("");
        setLoading(false);

        if (payload.status === "queued" || payload.status === "running") {
          pollTimerRef.current = window.setTimeout(poll, 3500);
        }
      } catch (err) {
        if (isCancelled) return;
        setError(err.message || "Unable to fetch job.");
        setLoading(false);
      }
    }

    void poll();

    return () => {
      isCancelled = true;
      if (pollTimerRef.current) {
        window.clearTimeout(pollTimerRef.current);
      }
    };
  }, [jobId, router]);

  const result = useMemo(() => job?.result || {}, [job]);
  const actionPlan = Array.isArray(result.action_plan) ? result.action_plan : [];
  const generatedFiles = Array.isArray(result.generated_website_files) ? result.generated_website_files : [];
  const githubLink = result.github_repository_link || result.generated_website_repo || "";
  const vercelLink = result.vercel_deployment_link || "";
  const currentStatus = job?.status || "queued";

  function handleLogout() {
    clearSession();
    router.push("/login");
  }

  return (
    <main className="container">
      <header className="topbar fade-up">
        <div className="user-row">
          <Link className="brand" href="/dashboard">
            AI Startup Builder
          </Link>
          <span className={`badge ${statusClass(currentStatus)}`}>{currentStatus}</span>
        </div>
        <div className="user-row">
          <Link className="button secondary" href="/contact">
            Contact
          </Link>
          <button className="button secondary" onClick={handleLogout} type="button">
            Logout
          </button>
        </div>
      </header>

      <section className="results-grid">
        <aside className="stack fade-up delay-1">
          <article className="glass-card card-pad">
            <h2 className="section-title">Job Details</h2>
            <div className="info-list">
              <p className="info-item">
                <span>Job ID</span>
                <strong className="mono">{job?.id || jobId || "-"}</strong>
              </p>
              <p className="info-item">
                <span>Created</span>
                <strong>{formatTimestamp(job?.created_at)}</strong>
              </p>
            </div>
          </article>

          <article className="glass-card card-pad">
            <h2 className="section-title">Generated Links</h2>
            <div className="info-list">
              <p className="link-row">
                <span>GitHub</span>
                {githubLink ? (
                  <a href={githubLink} rel="noreferrer" target="_blank">
                    {githubLink}
                  </a>
                ) : (
                  <strong>-</strong>
                )}
              </p>
              <p className="link-row">
                <span>Vercel</span>
                {vercelLink ? (
                  <a href={vercelLink} rel="noreferrer" target="_blank">
                    {vercelLink}
                  </a>
                ) : (
                  <strong>-</strong>
                )}
              </p>
            </div>
          </article>
        </aside>

        <div className="stack fade-up delay-2">
          {loading ? <p className="alert info loading-pulse">Fetching job results...</p> : null}
          {error ? <p className="alert error">{error}</p> : null}

          <article className="glass-card card-pad">
            <h1 className="section-title">Startup Idea</h1>
            <pre className="result-block">{job?.startup_idea || "-"}</pre>
          </article>

          <article className="glass-card card-pad">
            <h2 className="section-title">Detailed Startup Analysis</h2>
            <pre className="result-block">{result.startup_analysis || "-"}</pre>
          </article>

          <article className="glass-card card-pad">
            <h2 className="section-title">Existing Market Insights</h2>
            <pre className="result-block">{result.market_insights || "-"}</pre>
          </article>

          <article className="glass-card card-pad">
            <h2 className="section-title">Recommended Action Plan</h2>
            {actionPlan.length ? (
              <ol className="list">
                {actionPlan.map((item, index) => (
                  <li key={`${index}-${item}`}>{item}</li>
                ))}
              </ol>
            ) : (
              <p className="text-muted tiny">No action plan returned.</p>
            )}
          </article>

          <article className="glass-card card-pad">
            <h2 className="section-title">Generated Website Files</h2>
            {generatedFiles.length ? (
              <ul className="list">
                {generatedFiles.map((name) => (
                  <li className="mono" key={name}>
                    {name}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-muted tiny">No files returned.</p>
            )}
          </article>
        </div>
      </section>
    </main>
  );
}

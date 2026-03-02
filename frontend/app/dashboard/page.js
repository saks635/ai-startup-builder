"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiClient } from "@/lib/api";
import { clearSession, getUser, isAuthenticated } from "@/lib/auth";

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

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState({});
  const [idea, setIdea] = useState("");
  const [jobs, setJobs] = useState([]);
  const [jobsError, setJobsError] = useState("");
  const [formError, setFormError] = useState("");
  const [loadingJobs, setLoadingJobs] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const loadJobs = useCallback(async () => {
    setLoadingJobs(true);
    setJobsError("");
    try {
      const payload = await apiClient.listJobs();
      setJobs(Array.isArray(payload.jobs) ? payload.jobs.slice(0, 10) : []);
    } catch (err) {
      setJobsError(err.message || "Unable to load jobs.");
    } finally {
      setLoadingJobs(false);
    }
  }, []);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
      return;
    }

    const storedUser = getUser();
    setUser(storedUser);
    void loadJobs();

    apiClient
      .me()
      .then((payload) => {
        setUser(payload.user || storedUser);
      })
      .catch(() => {});
  }, [loadJobs, router]);

  function handleLogout() {
    clearSession();
    router.push("/login");
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setFormError("");

    const trimmedIdea = idea.trim();
    if (!trimmedIdea) {
      setFormError("Startup idea is required.");
      return;
    }

    setSubmitting(true);
    try {
      const payload = await apiClient.runWorkflow({ startup_idea: trimmedIdea });
      router.push(`/results?jobId=${encodeURIComponent(payload.job_id)}`);
    } catch (err) {
      setFormError(err.message || "Workflow request failed.");
      setSubmitting(false);
    }
  }

  return (
    <main className="container">
      <header className="topbar fade-up">
        <div>
          <div className="brand">AI Startup Builder</div>
          <div className="text-muted tiny">Run idea validation, research, and deployment in one flow.</div>
        </div>
        <div className="user-row">
          <span className="text-muted tiny">{user.email || user.name || "User"}</span>
          <Link className="button secondary" href="/contact">
            Contact
          </Link>
          <button className="button secondary" onClick={handleLogout} type="button">
            Logout
          </button>
        </div>
      </header>

      <section className="dashboard-grid">
        <aside className="stack">
          <article className="glass-card card-pad fade-up delay-1">
            <h2 className="section-title">Workflow</h2>
            <p className="text-muted tiny">
              Submit a startup idea and the backend will generate market insights, action plan steps, repository
              links, and deployment URL.
            </p>
          </article>

          <article className="glass-card card-pad fade-up delay-2">
            <h2 className="section-title">Tips</h2>
            <ul className="list tiny">
              <li>Include your target customer and main pain point.</li>
              <li>State the business model you are considering.</li>
              <li>Add constraints such as budget or region.</li>
            </ul>
          </article>
        </aside>

        <div className="stack">
          <article className="glass-card card-pad fade-up delay-1">
            <h1 className="section-title">Submit Startup Idea</h1>
            <form className="form-grid" onSubmit={handleSubmit}>
              <div>
                <label className="label" htmlFor="ideaInput">
                  Startup Idea
                </label>
                <textarea
                  id="ideaInput"
                  className="textarea"
                  onChange={(event) => setIdea(event.target.value)}
                  placeholder="Describe your startup idea in detail..."
                  required
                  value={idea}
                />
              </div>

              {formError ? <p className="alert error">{formError}</p> : null}

              <button className="button" disabled={submitting} type="submit">
                {submitting ? "Submitting..." : "Run Workflow"}
              </button>
            </form>
          </article>

          <article className="glass-card card-pad fade-up delay-3">
            <div className="topbar" style={{ marginBottom: "0.8rem" }}>
              <h2 className="section-title" style={{ marginBottom: 0 }}>
                Recent Jobs
              </h2>
              <button className="button secondary" onClick={() => void loadJobs()} type="button">
                Refresh
              </button>
            </div>

            {jobsError ? <p className="alert error">{jobsError}</p> : null}

            {loadingJobs ? <p className="text-muted tiny loading-pulse">Loading jobs...</p> : null}

            {!loadingJobs && !jobs.length ? <p className="text-muted tiny">No jobs yet.</p> : null}

            {!loadingJobs && jobs.length ? (
              <div className="jobs-list">
                {jobs.map((job) => (
                  <button
                    className="job-card"
                    key={job.id}
                    onClick={() => router.push(`/results?jobId=${encodeURIComponent(job.id)}`)}
                    type="button"
                  >
                    <div>
                      <div className="mono">{job.id}</div>
                      <div className="text-muted tiny">{formatTimestamp(job.created_at)}</div>
                    </div>
                    <span className={`badge ${statusClass(job.status)}`}>{job.status}</span>
                  </button>
                ))}
              </div>
            ) : null}
          </article>
        </div>
      </section>
    </main>
  );
}

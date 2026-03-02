"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api";
import { isAuthenticated, saveSession } from "@/lib/auth";

export default function SignupPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [form, setForm] = useState({ 
    name: "", 
    email: "", 
    password: "",
  });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [oauthData, setOauthData] = useState(null);

  useEffect(() => {
    if (isAuthenticated()) {
      router.replace("/dashboard");
    }
    
    // Check for OAuth data in URL params
    const githubToken = searchParams.get("github_token");
    const githubUsername = searchParams.get("github_username");
    const githubEmail = searchParams.get("github_email");
    const githubName = searchParams.get("github_name");
    
    if (githubToken) {
      setOauthData({
        github_token: githubToken,
        github_username: githubUsername,
        email: githubEmail || "",
        name: githubName || "",
      });
      // Pre-fill form
      if (githubEmail) setForm(f => ({ ...f, email: githubEmail, name: githubName || "" }));
    }
  }, [router, searchParams]);

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitting(true);
    setError("");

    try {
      let response;
      
      if (oauthData?.github_token) {
        // Complete OAuth signup
        response = await apiClient.post("/api/auth/oauth/complete-signup", {
          email: form.email.trim(),
          password: form.password,
          name: form.name.trim(),
          github_access_token: oauthData.github_token,
          github_username: oauthData.github_username,
        });
      } else {
        // Regular signup
        response = await apiClient.signup({
          name: form.name.trim(),
          email: form.email.trim(),
          password: form.password,
        });
      }
      
      saveSession(response.token, response.user);
      
      // Show success message if integrations were connected
      if (response.github_connected || response.vercel_connected) {
        let msg = "Account created! ";
        if (response.github_connected) msg += `GitHub connected. `;
        if (response.vercel_connected) msg += "Vercel connected.";
        alert(msg);
      }
      
      router.push("/dashboard");
    } catch (err) {
      setError(err.message || "Signup failed.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleGithubLogin() {
    try {
      const response = await apiClient.get("/api/auth/github/login");
      if (response.auth_url) {
        window.location.href = response.auth_url;
      } else if (response.error) {
        alert(response.error);
      }
    } catch (err) {
      alert("Failed to start GitHub login");
    }
  }

  return (
    <main className="container auth-wrap">
      <div className="auth-corner-link">
        <Link href="/contact">Contact</Link>
      </div>
      <section className="glass-card auth-card fade-up">
        <div className="card-pad">
          <p className="eyebrow">AI Startup Builder</p>
          <h1 className="title">Create Account</h1>
          <p className="subtitle">Sign up to generate startup analysis and live deployment links.</p>

          {/* OAuth Signup Options */}
          <div style={{ marginBottom: "1.5rem" }}>
            <button 
              type="button"
              onClick={handleGithubLogin}
              style={{ 
                width: "100%",
                padding: "0.75rem",
                backgroundColor: "#24292e",
                color: "white",
                border: "none",
                borderRadius: "6px",
                cursor: "pointer",
                fontSize: "1rem",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "0.5rem",
              }}
            >
              <svg height="20" viewBox="0 0 16 16" width="20" fill="white">
                <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
              </svg>
              Sign up with GitHub
            </button>
          </div>

          <div style={{ textAlign: "center", margin: "1rem 0", color: "#666" }}>
            — or —
          </div>

          <form className="form-grid" onSubmit={handleSubmit}>
            <div>
              <label className="label" htmlFor="name">
                Full Name
              </label>
              <input
                id="name"
                autoComplete="name"
                className="input"
                onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
                required
                type="text"
                value={form.name}
              />
            </div>

            <div>
              <label className="label" htmlFor="email">
                Email
              </label>
              <input
                id="email"
                autoComplete="email"
                className="input"
                onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
                required
                type="email"
                value={form.email}
              />
            </div>

            <div>
              <label className="label" htmlFor="password">
                Password
              </label>
              <input
                id="password"
                autoComplete="new-password"
                className="input"
                minLength={6}
                onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))}
                required
                type="password"
                value={form.password}
              />
            </div>

            {oauthData?.github_username && (
              <div style={{ 
                padding: "0.75rem", 
                backgroundColor: "#e6fffa", 
                borderRadius: "6px",
                border: "1px solid #38b2ac"
              }}>
                <p style={{ margin: 0, color: "#234e52", fontSize: "0.875rem" }}>
                  ✓ GitHub account will be connected: <strong>@{oauthData.github_username}</strong>
                </p>
              </div>
            )}

            {error ? <p className="alert error">{error}</p> : null}

            <button className="button w-full" disabled={submitting} type="submit">
              {submitting ? "Creating..." : "Create Account"}
            </button>
          </form>

          <p className="switch-link">
            Already have an account? <Link href="/login">Login</Link>
          </p>
        </div>
      </section>
    </main>
  );
}

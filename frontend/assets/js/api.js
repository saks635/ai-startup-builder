(function () {
  const STORAGE_KEY = "startup_builder_api_base";
  const defaultBase = window.location.pathname.startsWith("/app/")
    ? window.location.origin
    : "http://127.0.0.1:8000";

  function normalizeBase(url) {
    return (url || defaultBase).trim().replace(/\/+$/, "");
  }

  function getApiBase() {
    return normalizeBase(localStorage.getItem(STORAGE_KEY) || defaultBase);
  }

  function setApiBase(url) {
    localStorage.setItem(STORAGE_KEY, normalizeBase(url));
  }

  function getToken() {
    return localStorage.getItem("startup_builder_token") || "";
  }

  async function request(path, options) {
    const opts = options || {};
    const headers = opts.headers || {};
    const token = getToken();
    if (token) {
      headers.Authorization = "Bearer " + token;
    }
    if (opts.body && !headers["Content-Type"]) {
      headers["Content-Type"] = "application/json";
    }

    const response = await fetch(getApiBase() + path, {
      method: opts.method || "GET",
      headers: headers,
      body: opts.body,
    });

    let payload = {};
    try {
      payload = await response.json();
    } catch (err) {
      payload = {};
    }

    if (!response.ok) {
      const detail = payload.detail || "Request failed.";
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
    return payload;
  }

  window.ApiClient = {
    getApiBase: getApiBase,
    setApiBase: setApiBase,
    signup: function (data) {
      return request("/api/auth/signup", { method: "POST", body: JSON.stringify(data) });
    },
    login: function (data) {
      return request("/api/auth/login", { method: "POST", body: JSON.stringify(data) });
    },
    me: function () {
      return request("/api/auth/me");
    },
    runWorkflow: function (data) {
      return request("/api/workflow/run", { method: "POST", body: JSON.stringify(data) });
    },
    listJobs: function () {
      return request("/api/workflow/jobs");
    },
    getJob: function (jobId) {
      return request("/api/workflow/jobs/" + encodeURIComponent(jobId));
    },
    connectGithub: function (token) {
      return request("/api/integrations/github/connect", {
        method: "POST",
        body: JSON.stringify({ github_token: token }),
      });
    },
    connectVercel: function (token) {
      return request("/api/integrations/vercel/connect", {
        method: "POST",
        body: JSON.stringify({ vercel_token: token }),
      });
    },
    disconnectGithub: function () {
      return request("/api/integrations/github/disconnect", { method: "POST" });
    },
    disconnectVercel: function () {
      return request("/api/integrations/vercel/disconnect", { method: "POST" });
    },
  };
})();

(function () {
  if (!window.Auth.requireAuth("login.html")) {
    return;
  }

  var user = window.Auth.getUser();
  var userName = document.getElementById("userName");
  var logoutBtn = document.getElementById("logoutBtn");
  var ideaForm = document.getElementById("ideaForm");
  var formError = document.getElementById("formError");
  var jobsContainer = document.getElementById("jobsContainer");
  var emptyJobs = document.getElementById("emptyJobs");
  var refreshJobsBtn = document.getElementById("refreshJobsBtn");

  // Integration elements
  var githubBadge = document.getElementById("githubBadge");
  var githubConnected = document.getElementById("githubConnected");
  var githubDisconnected = document.getElementById("githubDisconnected");
  var githubUsername = document.getElementById("githubUsername");
  var githubConnectBtn = document.getElementById("githubConnectBtn");
  var githubDisconnectBtn = document.getElementById("githubDisconnectBtn");
  var githubTokenInput = document.getElementById("githubTokenInput");
  var githubError = document.getElementById("githubError");

  var vercelBadge = document.getElementById("vercelBadge");
  var vercelConnected = document.getElementById("vercelConnected");
  var vercelDisconnected = document.getElementById("vercelDisconnected");
  var vercelConnectBtn = document.getElementById("vercelConnectBtn");
  var vercelDisconnectBtn = document.getElementById("vercelDisconnectBtn");
  var vercelTokenInput = document.getElementById("vercelTokenInput");
  var vercelError = document.getElementById("vercelError");

  userName.textContent = user.email || user.name || "User";

  logoutBtn.addEventListener("click", function () {
    window.Auth.clearSession();
    window.location.href = "login.html";
  });

  // ============ Integration UI Helpers ============

  function updateGithubUI(connected, ghUsername) {
    if (connected) {
      githubBadge.className = "badge bg-success ms-1 small";
      githubBadge.textContent = "connected";
      githubConnected.classList.remove("d-none");
      githubDisconnected.classList.add("d-none");
      githubUsername.textContent = ghUsername || "connected";
    } else {
      githubBadge.className = "badge bg-danger ms-1 small";
      githubBadge.textContent = "not connected";
      githubConnected.classList.add("d-none");
      githubDisconnected.classList.remove("d-none");
    }
    githubError.classList.add("d-none");
  }

  function updateVercelUI(connected) {
    if (connected) {
      vercelBadge.className = "badge bg-success ms-1 small";
      vercelBadge.textContent = "connected";
      vercelConnected.classList.remove("d-none");
      vercelDisconnected.classList.add("d-none");
    } else {
      vercelBadge.className = "badge bg-danger ms-1 small";
      vercelBadge.textContent = "not connected";
      vercelConnected.classList.add("d-none");
      vercelDisconnected.classList.remove("d-none");
    }
    vercelError.classList.add("d-none");
  }

  // Load fresh status from /api/auth/me
  async function loadIntegrationStatus() {
    try {
      var data = await window.ApiClient.me();
      updateGithubUI(data.github_connected, data.github_username);
      updateVercelUI(data.vercel_connected);
      window.Auth.saveIntegrations({
        github_connected: data.github_connected,
        github_username: data.github_username,
        vercel_connected: data.vercel_connected,
      });
    } catch (err) {
      // Fallback to cached status
      var cached = window.Auth.getIntegrations();
      updateGithubUI(cached.github_connected, cached.github_username);
      updateVercelUI(cached.vercel_connected);
    }
  }

  // ============ GitHub Connect / Disconnect ============

  githubConnectBtn.addEventListener("click", async function () {
    var token = (githubTokenInput.value || "").trim();
    if (!token) {
      githubError.textContent = "Please enter a GitHub token.";
      githubError.classList.remove("d-none");
      return;
    }
    githubConnectBtn.disabled = true;
    githubConnectBtn.textContent = "Connecting...";
    githubError.classList.add("d-none");
    try {
      var result = await window.ApiClient.connectGithub(token);
      updateGithubUI(true, result.github_username);
      window.Auth.saveIntegrations({
        github_connected: true,
        github_username: result.github_username,
        vercel_connected: window.Auth.getIntegrations().vercel_connected,
      });
      githubTokenInput.value = "";
    } catch (err) {
      githubError.textContent = err.message || "Failed to connect GitHub.";
      githubError.classList.remove("d-none");
    }
    githubConnectBtn.disabled = false;
    githubConnectBtn.innerHTML = '<i class="bi bi-plug"></i> Connect GitHub';
  });

  githubDisconnectBtn.addEventListener("click", async function () {
    githubDisconnectBtn.disabled = true;
    githubDisconnectBtn.textContent = "Disconnecting...";
    try {
      await window.ApiClient.disconnectGithub();
      updateGithubUI(false, "");
      window.Auth.saveIntegrations({
        github_connected: false,
        github_username: "",
        vercel_connected: window.Auth.getIntegrations().vercel_connected,
      });
    } catch (err) {
      githubError.textContent = err.message || "Failed to disconnect.";
      githubError.classList.remove("d-none");
    }
    githubDisconnectBtn.disabled = false;
    githubDisconnectBtn.textContent = "Disconnect";
  });

  // ============ Vercel Connect / Disconnect ============

  vercelConnectBtn.addEventListener("click", async function () {
    var token = (vercelTokenInput.value || "").trim();
    if (!token) {
      vercelError.textContent = "Please enter a Vercel token.";
      vercelError.classList.remove("d-none");
      return;
    }
    vercelConnectBtn.disabled = true;
    vercelConnectBtn.textContent = "Connecting...";
    vercelError.classList.add("d-none");
    try {
      await window.ApiClient.connectVercel(token);
      updateVercelUI(true);
      window.Auth.saveIntegrations({
        github_connected: window.Auth.getIntegrations().github_connected,
        github_username: window.Auth.getIntegrations().github_username,
        vercel_connected: true,
      });
      vercelTokenInput.value = "";
    } catch (err) {
      vercelError.textContent = err.message || "Failed to connect Vercel.";
      vercelError.classList.remove("d-none");
    }
    vercelConnectBtn.disabled = false;
    vercelConnectBtn.innerHTML = '<i class="bi bi-plug"></i> Connect Vercel';
  });

  vercelDisconnectBtn.addEventListener("click", async function () {
    vercelDisconnectBtn.disabled = true;
    vercelDisconnectBtn.textContent = "Disconnecting...";
    try {
      await window.ApiClient.disconnectVercel();
      updateVercelUI(false);
      window.Auth.saveIntegrations({
        github_connected: window.Auth.getIntegrations().github_connected,
        github_username: window.Auth.getIntegrations().github_username,
        vercel_connected: false,
      });
    } catch (err) {
      vercelError.textContent = err.message || "Failed to disconnect.";
      vercelError.classList.remove("d-none");
    }
    vercelDisconnectBtn.disabled = false;
    vercelDisconnectBtn.textContent = "Disconnect";
  });

  // ============ Jobs ============

  function statusBadge(status) {
    if (status === "completed") return "text-bg-success";
    if (status === "failed") return "text-bg-danger";
    if (status === "running") return "text-bg-warning";
    return "text-bg-secondary";
  }

  async function loadJobs() {
    try {
      var payload = await window.ApiClient.listJobs();
      var jobs = payload.jobs || [];
      jobsContainer.innerHTML = "";
      if (!jobs.length) {
        emptyJobs.classList.remove("d-none");
        return;
      }
      emptyJobs.classList.add("d-none");

      jobs.slice(0, 10).forEach(function (job) {
        var link = document.createElement("a");
        link.href = "results.html?jobId=" + encodeURIComponent(job.id);
        link.className = "list-group-item list-group-item-action";
        link.innerHTML =
          '<div class="d-flex justify-content-between align-items-center">' +
          "<div>" +
          '<p class="mb-1 fw-semibold">' + job.id + "</p>" +
          '<small class="text-secondary">' + new Date(job.created_at * 1000).toLocaleString() + "</small>" +
          "</div>" +
          '<span class="badge ' + statusBadge(job.status) + '">' + job.status + "</span>" +
          "</div>";
        jobsContainer.appendChild(link);
      });
    } catch (err) {
      formError.textContent = err.message || "Unable to load jobs.";
      formError.classList.remove("d-none");
    }
  }

  refreshJobsBtn.addEventListener("click", loadJobs);

  ideaForm.addEventListener("submit", async function (event) {
    event.preventDefault();
    formError.classList.add("d-none");
    var idea = document.getElementById("ideaInput").value.trim();
    if (!idea) {
      formError.textContent = "Startup idea is required.";
      formError.classList.remove("d-none");
      return;
    }

    var runBtn = document.getElementById("runBtn");
    runBtn.disabled = true;
    runBtn.textContent = "Submitting...";

    try {
      var payload = await window.ApiClient.runWorkflow({ startup_idea: idea });
      window.location.href = "results.html?jobId=" + encodeURIComponent(payload.job_id);
    } catch (err) {
      formError.textContent = err.message || "Workflow request failed.";
      formError.classList.remove("d-none");
      runBtn.disabled = false;
      runBtn.textContent = "Run Workflow";
    }
  });

  // Boot
  loadIntegrationStatus();
  loadJobs();
})();

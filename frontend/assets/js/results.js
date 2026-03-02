(function () {
  if (!window.Auth.requireAuth("login.html")) {
    return;
  }

  const logoutBtn = document.getElementById("logoutBtn");
  const statusBadge = document.getElementById("jobStatusBadge");
  const loadingBox = document.getElementById("loadingBox");
  const errorBox = document.getElementById("errorBox");
  const jobIdText = document.getElementById("jobIdText");
  const jobCreatedText = document.getElementById("jobCreatedText");
  const ideaText = document.getElementById("ideaText");
  const analysisText = document.getElementById("analysisText");
  const marketText = document.getElementById("marketText");
  const actionPlanList = document.getElementById("actionPlanList");
  const filesList = document.getElementById("filesList");
  const githubLink = document.getElementById("githubLink");
  const vercelLink = document.getElementById("vercelLink");

  logoutBtn.addEventListener("click", function () {
    window.Auth.clearSession();
    window.location.href = "login.html";
  });

  const params = new URLSearchParams(window.location.search);
  const jobId = params.get("jobId");
  if (!jobId) {
    errorBox.textContent = "Missing jobId in URL.";
    errorBox.classList.remove("d-none");
    loadingBox.classList.add("d-none");
    return;
  }

  function statusClass(status) {
    if (status === "completed") return "text-bg-success";
    if (status === "failed") return "text-bg-danger";
    if (status === "running") return "text-bg-warning";
    return "text-bg-secondary";
  }

  function renderResult(job) {
    statusBadge.className = "badge " + statusClass(job.status);
    statusBadge.textContent = job.status;
    jobIdText.textContent = job.id;
    jobCreatedText.textContent = new Date(job.created_at * 1000).toLocaleString();
    ideaText.textContent = job.startup_idea || "-";

    if (job.status === "failed") {
      errorBox.textContent = job.error || "Workflow failed.";
      errorBox.classList.remove("d-none");
      return;
    }

    const result = job.result || {};
    analysisText.textContent = result.startup_analysis || "-";
    marketText.textContent = result.market_insights || "-";

    const plan = Array.isArray(result.action_plan) ? result.action_plan : [];
    actionPlanList.innerHTML = "";
    if (!plan.length) {
      const li = document.createElement("li");
      li.textContent = "No action plan returned.";
      actionPlanList.appendChild(li);
    } else {
      plan.forEach(function (item) {
        const li = document.createElement("li");
        li.textContent = item;
        actionPlanList.appendChild(li);
      });
    }

    const files = Array.isArray(result.generated_website_files) ? result.generated_website_files : [];
    filesList.innerHTML = "";
    if (!files.length) {
      const li = document.createElement("li");
      li.textContent = "No files returned.";
      filesList.appendChild(li);
    } else {
      files.forEach(function (name) {
        const li = document.createElement("li");
        li.textContent = name;
        filesList.appendChild(li);
      });
    }

    const repo = result.github_repository_link || result.generated_website_repo || "";
    const vercel = result.vercel_deployment_link || "";
    githubLink.textContent = repo || "-";
    githubLink.href = repo || "#";
    vercelLink.textContent = vercel || "-";
    vercelLink.href = vercel || "#";
  }

  async function poll() {
    try {
      const job = await window.ApiClient.getJob(jobId);
      renderResult(job);
      loadingBox.classList.add("d-none");
      if (job.status === "queued" || job.status === "running") {
        setTimeout(poll, 3500);
      }
    } catch (err) {
      errorBox.textContent = err.message || "Unable to fetch job.";
      errorBox.classList.remove("d-none");
      loadingBox.classList.add("d-none");
    }
  }

  poll();
})();

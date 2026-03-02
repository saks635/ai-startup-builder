(function () {
  if (!window.Auth.requireAuth("login.html")) {
    return;
  }

  var logoutBtn = document.getElementById("logoutBtn");
  var statusBadge = document.getElementById("jobStatusBadge");
  var loadingBox = document.getElementById("loadingBox");
  var errorBox = document.getElementById("errorBox");
  var jobIdText = document.getElementById("jobIdText");
  var jobCreatedText = document.getElementById("jobCreatedText");
  var ideaText = document.getElementById("ideaText");
  var analysisText = document.getElementById("analysisText");
  var marketText = document.getElementById("marketText");
  var pitchDeckText = document.getElementById("pitchDeckText");
  var actionPlanList = document.getElementById("actionPlanList");
  var filesList = document.getElementById("filesList");
  var githubLink = document.getElementById("githubLink");
  var vercelLink = document.getElementById("vercelLink");
  var analysisPdfBtn = document.getElementById("analysisPdfBtn");
  var pitchDeckPdfBtn = document.getElementById("pitchDeckPdfBtn");
  var pdfPending = document.getElementById("pdfPending");

  logoutBtn.addEventListener("click", function () {
    window.Auth.clearSession();
    window.location.href = "login.html";
  });

  var params = new URLSearchParams(window.location.search);
  var jobId = params.get("jobId");
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

  function setupPdfButtons(job) {
    var result = job.result || {};
    var apiBase = window.ApiClient.getApiBase();
    var token = localStorage.getItem("startup_builder_token");

    if (job.status === "completed") {
      pdfPending.classList.add("d-none");

      // Analysis PDF
      if (result.analysis_pdf_path) {
        analysisPdfBtn.href = apiBase + "/api/workflow/jobs/" + encodeURIComponent(jobId) + "/pdf/analysis";
        analysisPdfBtn.classList.remove("d-none");
        analysisPdfBtn.addEventListener("click", function (e) {
          e.preventDefault();
          fetch(this.href, {
            headers: { "Authorization": "Bearer " + token }
          })
            .then(function (r) { return r.blob(); })
            .then(function (blob) {
              var url = URL.createObjectURL(blob);
              var a = document.createElement("a");
              a.href = url;
              a.download = jobId + "_analysis.pdf";
              a.click();
              URL.revokeObjectURL(url);
            });
        });
      }

      // Pitch Deck PDF
      if (result.pitch_deck_pdf_path) {
        pitchDeckPdfBtn.href = apiBase + "/api/workflow/jobs/" + encodeURIComponent(jobId) + "/pdf/pitch-deck";
        pitchDeckPdfBtn.classList.remove("d-none");
        pitchDeckPdfBtn.addEventListener("click", function (e) {
          e.preventDefault();
          fetch(this.href, {
            headers: { "Authorization": "Bearer " + token }
          })
            .then(function (r) { return r.blob(); })
            .then(function (blob) {
              var url = URL.createObjectURL(blob);
              var a = document.createElement("a");
              a.href = url;
              a.download = jobId + "_pitch-deck.pdf";
              a.click();
              URL.revokeObjectURL(url);
            });
        });
      }
    }
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

    var result = job.result || {};
    analysisText.textContent = result.startup_analysis || "-";
    marketText.textContent = result.market_insights || "-";
    pitchDeckText.textContent = result.pitch_deck || "-";

    var plan = Array.isArray(result.action_plan) ? result.action_plan : [];
    actionPlanList.innerHTML = "";
    if (!plan.length) {
      var li = document.createElement("li");
      li.textContent = "No action plan returned.";
      actionPlanList.appendChild(li);
    } else {
      plan.forEach(function (item) {
        var li = document.createElement("li");
        li.textContent = item;
        actionPlanList.appendChild(li);
      });
    }

    var files = Array.isArray(result.generated_website_files) ? result.generated_website_files : [];
    filesList.innerHTML = "";
    if (!files.length) {
      var li = document.createElement("li");
      li.textContent = "No files returned.";
      filesList.appendChild(li);
    } else {
      files.forEach(function (name) {
        var li = document.createElement("li");
        li.textContent = name;
        filesList.appendChild(li);
      });
    }

    var repo = result.github_repository_link || result.generated_website_repo || "";
    var vercel = result.vercel_deployment_link || "";
    githubLink.textContent = repo || "-";
    githubLink.href = repo || "#";
    vercelLink.textContent = vercel || "-";
    vercelLink.href = vercel || "#";

    // PDF buttons
    setupPdfButtons(job);
  }

  async function poll() {
    try {
      var job = await window.ApiClient.getJob(jobId);
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

(function () {
  var form = document.getElementById("signupForm");
  var errorBox = document.getElementById("errorBox");
  var successBox = document.getElementById("successBox");
  var submitBtn = document.getElementById("submitBtn");

  if (!form) {
    return;
  }

  form.addEventListener("submit", async function (event) {
    event.preventDefault();
    errorBox.classList.add("d-none");
    successBox.classList.add("d-none");
    submitBtn.disabled = true;
    submitBtn.textContent = "Creating Account...";

    try {

      // Step 1: Create the account
      var payload = {
        name: document.getElementById("name").value.trim(),
        email: document.getElementById("email").value.trim(),
        password: document.getElementById("password").value,
      };
      var data = await window.ApiClient.signup(payload);
      window.Auth.saveSession(data.token, data.user);

      // Step 2: Connect GitHub token if provided
      var githubToken = (document.getElementById("githubToken").value || "").trim();
      var vercelToken = (document.getElementById("vercelToken").value || "").trim();
      var githubConnected = false;
      var githubUsername = "";
      var vercelConnected = false;

      if (githubToken) {
        submitBtn.textContent = "Connecting GitHub...";
        try {
          var ghResult = await window.ApiClient.connectGithub(githubToken);
          githubConnected = true;
          githubUsername = ghResult.github_username || "";
        } catch (ghErr) {
          // Signup succeeded but GitHub connection failed — show warning but continue
          successBox.textContent = "Account created! GitHub connection failed: " + (ghErr.message || "Invalid token.");
          successBox.classList.remove("d-none");
        }
      }

      // Step 3: Connect Vercel token if provided
      if (vercelToken) {
        submitBtn.textContent = "Connecting Vercel...";
        try {
          await window.ApiClient.connectVercel(vercelToken);
          vercelConnected = true;
        } catch (vcErr) {
          var msg = successBox.textContent || "Account created!";
          successBox.textContent = msg + " Vercel connection failed: " + (vcErr.message || "Invalid token.");
          successBox.classList.remove("d-none");
        }
      }

      // Save integration status
      window.Auth.saveIntegrations({
        github_connected: githubConnected,
        github_username: githubUsername,
        vercel_connected: vercelConnected,
      });

      // If we showed a warning, delay redirect so user sees it
      if (!successBox.classList.contains("d-none")) {
        setTimeout(function () {
          window.location.href = "dashboard.html";
        }, 2500);
      } else {
        window.location.href = "dashboard.html";
      }
    } catch (err) {
      errorBox.textContent = err.message || "Signup failed.";
      errorBox.classList.remove("d-none");
      submitBtn.disabled = false;
      submitBtn.textContent = "Create Account";
    }
  });
})();

(function () {
  var form = document.getElementById("loginForm");
  var errorBox = document.getElementById("errorBox");

  if (!form) {
    return;
  }

  form.addEventListener("submit", async function (event) {
    event.preventDefault();
    errorBox.classList.add("d-none");

    try {
      var payload = {
        email: document.getElementById("email").value.trim(),
        password: document.getElementById("password").value,
      };
      var data = await window.ApiClient.login(payload);
      window.Auth.saveSession(data.token, data.user);
      window.Auth.saveIntegrations({
        github_connected: data.github_connected,
        github_username: data.github_username,
        vercel_connected: data.vercel_connected,
      });
      window.location.href = "dashboard.html";
    } catch (err) {
      errorBox.textContent = err.message || "Login failed.";
      errorBox.classList.remove("d-none");
    }
  });
})();

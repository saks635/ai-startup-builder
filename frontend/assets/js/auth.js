(function () {
  const TOKEN_KEY = "startup_builder_token";
  const USER_KEY = "startup_builder_user";

  function saveSession(token, user) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user || {}));
  }

  var INTEGRATIONS_KEY = "startup_builder_integrations";

  function clearSession() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem(INTEGRATIONS_KEY);
  }

  function getUser() {
    try {
      return JSON.parse(localStorage.getItem(USER_KEY) || "{}");
    } catch (err) {
      return {};
    }
  }

  function requireAuth(redirectTo) {
    var token = localStorage.getItem(TOKEN_KEY);
    if (!token) {
      window.location.href = redirectTo || "login.html";
      return false;
    }
    return true;
  }

  function saveIntegrations(data) {
    localStorage.setItem(INTEGRATIONS_KEY, JSON.stringify({
      github_connected: !!data.github_connected,
      github_username: data.github_username || "",
      vercel_connected: !!data.vercel_connected,
    }));
  }

  function getIntegrations() {
    try {
      return JSON.parse(localStorage.getItem(INTEGRATIONS_KEY) || "{}");
    } catch (err) {
      return {};
    }
  }

  window.Auth = {
    saveSession: saveSession,
    clearSession: clearSession,
    getUser: getUser,
    requireAuth: requireAuth,
    saveIntegrations: saveIntegrations,
    getIntegrations: getIntegrations,
  };
})();

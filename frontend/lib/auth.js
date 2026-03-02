const TOKEN_KEY = "startup_builder_token";
const USER_KEY = "startup_builder_user";

function canUseStorage() {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

export function saveSession(token, user) {
  if (!canUseStorage()) return;
  window.localStorage.setItem(TOKEN_KEY, token || "");
  window.localStorage.setItem(USER_KEY, JSON.stringify(user || {}));
}

export function clearSession() {
  if (!canUseStorage()) return;
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
}

export function getToken() {
  if (!canUseStorage()) return "";
  return window.localStorage.getItem(TOKEN_KEY) || "";
}

export function getUser() {
  if (!canUseStorage()) return {};
  try {
    return JSON.parse(window.localStorage.getItem(USER_KEY) || "{}");
  } catch {
    return {};
  }
}

export function isAuthenticated() {
  return Boolean(getToken());
}

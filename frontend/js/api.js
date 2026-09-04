const BASE_URL = "http://127.0.0.1:8000/api/v1";

function getToken() {
  return localStorage.getItem("sgm_token");
}

async function apiCall(endpoint, method = "GET", body) {
  const options = typeof method === "object" ? method : { method, body };
  const headers = { ...(options.headers || {}) };
  const token = getToken();
  if (token) headers.Authorization = "Bearer " + token;
  if (options.body && !(options.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }
  const response = await fetch(BASE_URL + endpoint, { ...options, headers });
  if (response.status === 204) return null;
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 401) { logout(); throw new Error("Session expired."); }
    throw new Error(data.detail || data.message || "Request failed");
  }
  return data;
}

function showToast(message, type = "success") {
  const el = document.createElement("div");
  el.className = `toast fixed bottom-5 right-5 z-50 rounded-xl px-5 py-3 text-white font-medium shadow-lg ${type === "error" || type === true ? "bg-red-600" : "bg-emerald-600"}`;
  el.textContent = message;
  document.body.append(el);
  setTimeout(() => el.remove(), 3500);
}

function showModal(id) { document.getElementById(id)?.classList.remove("hidden"); }
function hideModal(id) { document.getElementById(id)?.classList.add("hidden"); }

function checkAuth() {
  if (!getToken()) { location.href = "auth.html"; return false; }
  return true;
}

function logout() {
  localStorage.removeItem("sgm_token");
  location.href = "index.html";
}

function esc(v) {
  return String(v ?? "").replace(/[&<>"']/g, c =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[c])
  );
}

function dateLabel(v) {
  return v ? new Date(v).toLocaleDateString() : "—";
}

const api = {
  get: ep => apiCall(ep),
  post: (ep, body) => apiCall(ep, "POST", body instanceof FormData ? body : JSON.stringify(body)),
  put: (ep, body) => apiCall(ep, "PUT", JSON.stringify(body)),
  del: ep => apiCall(ep, "DELETE"),
  upload: (ep, fd) => apiCall(ep, "POST", fd)
};

const requireAuth = checkAuth;
const toast = showToast;

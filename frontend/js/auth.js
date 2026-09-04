const authForm = document.getElementById("authForm");
const modeTitle = document.getElementById("modeTitle");
const toggleMode = document.getElementById("toggleMode");
const emailField = document.getElementById("emailField");
const confirmField = document.getElementById("confirmField");
const authMessage = document.getElementById("authMessage");
const password = document.getElementById("password");
const confirmPassword = document.getElementById("confirmPassword");
const formBtn = document.getElementById("formBtn");
let registerMode = false;

// ── Toggle login / register ──
toggleMode.onclick = () => {
  registerMode = !registerMode;
  modeTitle.textContent = registerMode ? "Create your account" : "Welcome back";
  toggleMode.textContent = registerMode
    ? "Already registered? Sign in"
    : "New here? Create an account";
  formBtn.textContent = registerMode ? "Create account" : "Sign in";
  // Register: username + email + password + confirm
  // Login:    username + password
  emailField.classList.toggle("hidden", !registerMode);
  confirmField.classList.toggle("hidden", !registerMode);
  emailField.querySelector("input").required = registerMode;
  confirmPassword.required = registerMode;
  authMessage.textContent = "";
};

// ── Toggle password visibility ──
document.getElementById("togglePassword").onclick = () => {
  const visible = password.type === "text";
  password.type = visible ? "password" : "text";
  document.getElementById("togglePassword").innerHTML =
    `<i class="fa-solid fa-eye${visible ? "" : "-slash"}"></i>`;
};

// ── Submit ──
authForm.onsubmit = async (e) => {
  e.preventDefault();
  authMessage.textContent = "";

  if (registerMode && password.value !== confirmPassword.value) {
    authMessage.textContent = "Passwords do not match.";
    return;
  }

  formBtn.disabled = true;
  formBtn.textContent = registerMode ? "Creating account…" : "Signing in…";

  try {
    if (registerMode) {
      // 1) Create the account
      await apiCall("/auth/register", "POST", JSON.stringify({
        username: authForm.username.value.trim(),
        email: authForm.email.value.trim(),
        password: password.value,
        full_name: authForm.username.value.trim() // drop if backend doesn't require it
      }));

      // 2) Auto-login so the user lands on the dashboard immediately
      const params = new URLSearchParams({
        username: authForm.username.value.trim(),
        password: password.value
      });
      const data = await apiCall("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: params
      });
      localStorage.setItem("sgm_token", data.access_token);
      showToast("Account created — welcome!", "success");
      location.href = "dashboard.html";
    } else {
      // Login with username + password (OAuth2 form)
      const params = new URLSearchParams({
        username: authForm.username.value.trim(),
        password: password.value
      });
      const data = await apiCall("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: params
      });
      localStorage.setItem("sgm_token", data.access_token);
      showToast("Welcome back!", "success");
      location.href = "dashboard.html";
    }
  } catch (err) {
    authMessage.textContent = err.message;
    showToast(err.message, "error");
  } finally {
    formBtn.disabled = false;
    formBtn.textContent = registerMode ? "Create account" : "Sign in";
  }
};

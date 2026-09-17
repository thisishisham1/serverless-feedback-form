// ─────────────────────────────────────────────────────────
//  CONFIG — confirm this is YOUR real, deployed API Gateway URL
// ─────────────────────────────────────────────────────────
const API_URL = "https://5ghs19nixk.execute-api.us-east-1.amazonaws.com";

// ─────────────────────────────────────────────────────────
//  DOM elements
// ─────────────────────────────────────────────────────────
const form       = document.getElementById("feedbackForm");
const submitBtn  = document.getElementById("submitBtn");
const btnText    = document.getElementById("btnText");
const btnLoader  = document.getElementById("btnLoader");
const successMsg = document.getElementById("successMsg");
const errorMsg    = document.getElementById("errorMsg");
const totalCount  = document.getElementById("totalCount");

// ─────────────────────────────────────────────────────────
//  Load total message count on page load
// ─────────────────────────────────────────────────────────
async function loadStats() {
  try {
    const res  = await fetch(`${API_URL}/stats`);
    const data = await res.json();
    totalCount.textContent = data.total_messages ?? "—";
  } catch {
    totalCount.textContent = "—";
  }
}

loadStats();

// ─────────────────────────────────────────────────────────
//  Form submit handler
// ─────────────────────────────────────────────────────────
form.addEventListener("submit", async function (e) {
  e.preventDefault();

  successMsg.style.display = "none";
  errorMsg.style.display   = "none";

  const name     = document.getElementById("name").value.trim();
  const email    = document.getElementById("email").value.trim();
  const subject  = document.getElementById("subject").value.trim();
  const category = document.getElementById("category").value;
  const message  = document.getElementById("message").value.trim();

  if (!name || !email || !subject || !message) {
    showError("Please fill in all required fields.");
    return;
  }

  setLoading(true);

  try {
    const response = await fetch(`${API_URL}/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, subject, category, message }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Something went wrong. Please try again.");
    }

    successMsg.style.display = "block";
    form.reset();
    loadStats();

  } catch (err) {
    showError(err.message);
  } finally {
    setLoading(false);
  }
});

// ─────────────────────────────────────────────────────────
//  Helpers
// ─────────────────────────────────────────────────────────
function setLoading(isLoading) {
  submitBtn.disabled      = isLoading;
  btnText.style.display   = isLoading ? "none"   : "inline";
  btnLoader.style.display = isLoading ? "inline-block" : "none";
}

function showError(message) {
  errorMsg.textContent   = message;
  errorMsg.style.display = "block";
}

// =====================================================================
// Vaani Chrome Extension — popup.js
// Mirrors the logic of app.py but runs entirely in the browser.
// The Groq API key is stored in chrome.storage.local (never synced).
// =====================================================================

const GROQ_MODEL = "llama-3.3-70b-versatile";
const GROQ_URL   = "https://api.groq.com/openai/v1/chat/completions";

const CONTEXT_INSTRUCTIONS = {
  "":          "",
  "email":     "This will be used in a formal email to a manager or HR professional.",
  "linkedin":  "This will be posted on LinkedIn. Keep it professional but engaging.",
  "whatsapp":  "This is for a WhatsApp message to a work colleague. Keep it natural but professional.",
  "job":       "This is for a job application or cover letter. Make it polished and impressive.",
};

const SYSTEM_PROMPT = `You are Vaani, an AI writing assistant built specifically for Indian professionals. Your job is to convert Hinglish, code-switched, or vernacular Indian text into polished, professional English.

Rules:
- Preserve the original intent and meaning completely
- Preserve the writer's tone — if they sound apologetic, keep that; if confident, keep that
- Output must sound like a fluent, professional Indian English speaker — not American or British
- Do not over-formalize. "Please find attached" energy is wrong. Natural professional is right.
- The output should work across contexts — emails to managers, LinkedIn posts, WhatsApp messages to colleagues — without being stiff or overly formal.
- Never translate cultural context away — Indian workplace norms should be reflected
- Output only the rewritten text. No explanations, no preamble, no "Here is the rewritten version:"`;

// ---------------------------------------------------------------------------
// DOM refs
// ---------------------------------------------------------------------------
const apiBanner       = document.getElementById("api-banner");
const openSettingsLink= document.getElementById("open-settings-link");
const settingsBtn     = document.getElementById("settings-btn");
const settingsPanel   = document.getElementById("settings-panel");
const apiKeyInput     = document.getElementById("api-key-input");
const saveKeyBtn      = document.getElementById("save-key-btn");
const formBody        = document.getElementById("form-body");
const userInput       = document.getElementById("user-input");
const charCount       = document.getElementById("char-count");
const contextSelect   = document.getElementById("context-select");
const rewriteBtn      = document.getElementById("rewrite-btn");
const btnLabel        = document.getElementById("btn-label");
const btnSpinner      = document.getElementById("btn-spinner");
const outputSection   = document.getElementById("output-section");
const outputBox       = document.getElementById("output-box");
const copyBtn         = document.getElementById("copy-btn");
const feedbackRow     = document.getElementById("feedback-row");
const feedbackGood    = document.getElementById("feedback-good");
const feedbackBad     = document.getElementById("feedback-bad");
const editArea        = document.getElementById("edit-area");
const userEdit        = document.getElementById("user-edit");
const submitEditBtn   = document.getElementById("submit-edit-btn");
const feedbackDone    = document.getElementById("feedback-done");
const errorBox        = document.getElementById("error-box");

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------
let currentOutput  = "";
let submittedInput = "";
let submittedCtx   = "";

// ---------------------------------------------------------------------------
// Startup — check for stored API key
// ---------------------------------------------------------------------------
chrome.storage.local.get("groqApiKey", ({ groqApiKey }) => {
  if (!groqApiKey) {
    apiBanner.style.display = "flex";
  }
});

// ---------------------------------------------------------------------------
// Settings panel toggle
// ---------------------------------------------------------------------------
function toggleSettings() {
  const open = settingsPanel.style.display !== "none";
  settingsPanel.style.display = open ? "none" : "flex";
  if (!open) {
    chrome.storage.local.get("groqApiKey", ({ groqApiKey }) => {
      if (groqApiKey) apiKeyInput.value = groqApiKey;
    });
  }
}
settingsBtn.addEventListener("click", toggleSettings);
openSettingsLink.addEventListener("click", () => {
  apiBanner.style.display = "none";
  settingsPanel.style.display = "flex";
});

saveKeyBtn.addEventListener("click", () => {
  const key = apiKeyInput.value.trim();
  if (!key) return;
  chrome.storage.local.set({ groqApiKey: key }, () => {
    apiBanner.style.display = "none";
    settingsPanel.style.display = "none";
    showError(""); // clear any errors
  });
});

// ---------------------------------------------------------------------------
// Char counter
// ---------------------------------------------------------------------------
userInput.addEventListener("input", () => {
  charCount.textContent = userInput.value.length;
});

// ---------------------------------------------------------------------------
// Rewrite
// ---------------------------------------------------------------------------
rewriteBtn.addEventListener("click", async () => {
  const text = userInput.value.trim();
  if (!text) {
    showError("Please paste some text before rewriting.");
    return;
  }

  const { groqApiKey } = await getStorage("groqApiKey");
  if (!groqApiKey) {
    showError("No Groq API key found. Click ⚙️ to add your key.");
    return;
  }

  showError("");
  setLoading(true);
  outputSection.style.display = "none";

  const ctxVal      = contextSelect.value;
  const ctxExtra    = CONTEXT_INSTRUCTIONS[ctxVal] || "";
  const systemPrompt = ctxExtra
    ? `${SYSTEM_PROMPT}\n\nAdditional instruction for this rewrite:\n- ${ctxExtra}`
    : SYSTEM_PROMPT;

  try {
    const res = await fetch(GROQ_URL, {
      method: "POST",
      headers: {
        "Content-Type":  "application/json",
        "Authorization": `Bearer ${groqApiKey}`,
      },
      body: JSON.stringify({
        model: GROQ_MODEL,
        messages: [
          { role: "system",  content: systemPrompt },
          { role: "user",    content: `Rewrite this text professionally: ${text}` },
        ],
        temperature: 0.4,
        max_tokens:  1024,
      }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.error?.message || `HTTP ${res.status}`);
    }

    const data     = await res.json();
    currentOutput  = data.choices[0].message.content.trim();
    submittedInput = text;
    submittedCtx   = contextSelect.options[contextSelect.selectedIndex].text;

    renderOutput(currentOutput);
  } catch (e) {
    showError(`Something went wrong: ${e.message}`);
  } finally {
    setLoading(false);
  }
});

// ---------------------------------------------------------------------------
// Output rendering
// ---------------------------------------------------------------------------
function renderOutput(text) {
  outputBox.textContent = text;
  outputSection.style.display = "flex";
  feedbackRow.style.display   = "flex";
  editArea.style.display      = "none";
  feedbackDone.style.display  = "none";
  userEdit.value = text;
  outputSection.scrollIntoView({ behavior: "smooth" });
}

// ---------------------------------------------------------------------------
// Copy
// ---------------------------------------------------------------------------
copyBtn.addEventListener("click", () => {
  navigator.clipboard.writeText(currentOutput).then(() => {
    copyBtn.textContent = "✅ Copied!";
    setTimeout(() => { copyBtn.textContent = "📋 Copy"; }, 2000);
  });
});

// ---------------------------------------------------------------------------
// Feedback
// ---------------------------------------------------------------------------
feedbackGood.addEventListener("click", () => {
  saveToStorage({ rating: "good", edited: "" });
  showFeedbackDone();
});

feedbackBad.addEventListener("click", () => {
  editArea.style.display = "flex";
  feedbackBad.disabled = true;
  feedbackGood.disabled = true;
});

submitEditBtn.addEventListener("click", () => {
  saveToStorage({ rating: "needs_change", edited: userEdit.value });
  showFeedbackDone();
});

function showFeedbackDone() {
  feedbackRow.style.display  = "none";
  editArea.style.display     = "none";
  feedbackDone.style.display = "block";
}

// ---------------------------------------------------------------------------
// Local corpus (stored in chrome.storage.local as JSON array)
// ---------------------------------------------------------------------------
async function saveToStorage({ rating, edited }) {
  const { corpus = [] } = await getStorage("corpus");
  corpus.push({
    timestamp:          new Date().toISOString(),
    original_input:     submittedInput,
    context_selected:   submittedCtx,
    vaani_output:       currentOutput,
    user_rating:        rating,
    user_edited_version: edited,
  });
  chrome.storage.local.set({ corpus });
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function setLoading(on) {
  rewriteBtn.disabled       = on;
  btnLabel.style.display    = on ? "none" : "inline";
  btnSpinner.style.display  = on ? "inline-block" : "none";
}

function showError(msg) {
  errorBox.textContent     = msg;
  errorBox.style.display   = msg ? "block" : "none";
}

function getStorage(key) {
  return new Promise(resolve => chrome.storage.local.get(key, resolve));
}

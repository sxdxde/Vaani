# Vaani — वाणी

**Your professional voice in English.**

Vaani is an AI writing assistant for Indian professionals. It converts Hinglish, code-switched, or vernacular Indian text into polished, natural professional English — preserving the writer's intent and tone instead of stiffly over-formalizing it.

This is an early-stage **Wizard of Oz MVP**: a prototype built to validate the idea and collect a real-world corpus before investing in fine-tuned models. Every rewrite and piece of feedback is saved to help train better Indian-professional AI down the line.

## Features

- ✨ **One-click rewrite** — paste Hinglish/code-switched text, get fluent professional English.
- 🎯 **Context-aware** — tailor the output for emails to managers/HR, LinkedIn posts, WhatsApp to colleagues, job applications, or general use.
- 📋 **Copy to clipboard** — grab the result in one tap.
- 👍 **Feedback loop** — rate a rewrite or submit your own preferred version; both are logged to grow the corpus.
- 🔒 **Admin corpus viewer** — password-protected sidebar to inspect, track metrics, and download collected data.

## Tech stack

- **[Streamlit](https://streamlit.io/)** — UI
- **[Groq API](https://console.groq.com)** — LLM inference (`llama-3.3-70b-versatile`)
- **python-dotenv**, **pandas**

## Getting started

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure your API key

Create a `.env` file in the project root (see `.env.example`):

```
GROQ_API_KEY=your_groq_api_key_here
```

Get a free key at [console.groq.com](https://console.groq.com).

### 3. Run the app

```bash
streamlit run app.py
```

The app opens in your browser at `http://localhost:8501`.

## How it works

1. Paste your Hinglish or code-switched text (up to 1000 characters).
2. Pick a **context** so Vaani knows the tone and audience.
3. Click **Rewrite with Vaani** — the text is sent to the Groq API with a system prompt tuned for fluent Indian professional English.
4. Copy the result, or leave feedback (✅ *Looks good* / ✏️ *I'd change this*).

## Data & corpus collections

Feedback is appended to `vaani_corpus.csv` with these columns:

| Column | Description |
| --- | --- |
| `timestamp` | UTC time of the rewrite |
| `original_input` | The text the user pasted |
| `context_selected` | Context chosen from the dropdown |
| `vaani_output` | The rewrite Vaani produced |
| `user_rating` | `good` or `needs_change` |
| `user_edited_version` | The user's preferred version, if submitted |

Storage is CSV-based for now and is swap-ready for Supabase later. The corpus is meant to feed future fine-tuning.

### Admin access

Open the **Admin** expander in the sidebar and enter the password to view collected data, see metrics (total rewrites, feedback, edits), and download the corpus.

## Roadmap

- [x] **Phase 1** — Core rewrite UI
- [x] **Phase 2** — Context controls
- [x] **Phase 3** — Feedback + corpus collection
- [ ] Migrate storage to Supabase
- [ ] Fine-tune a dedicated model on the collected corpus

---

🇮🇳 Vaani is an early prototype. Your rewrites help build better Indian professional AI. Will be released soon!

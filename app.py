import os
import csv
import html as html_lib
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

GROQ_MODEL = "llama-3.3-70b-versatile"
INPUT_CHAR_LIMIT = 1000
CORPUS_PATH = Path(__file__).parent / "vaani_corpus.csv"
CORPUS_COLUMNS = [
    "timestamp",
    "original_input",
    "context_selected",
    "vaani_output",
    "user_rating",
    "user_edited_version",
]
ADMIN_PASSWORD = "vaani2024"

CONTEXT_INSTRUCTIONS = {
    "General (any text)": "",
    "Email to manager / HR": "This will be used in a formal email to a manager or HR professional.",
    "LinkedIn post or bio": "This will be posted on LinkedIn. Keep it professional but engaging.",
    "WhatsApp to colleague": "This is for a WhatsApp message to a work colleague. Keep it natural but professional.",
    "Job application / cover note": "This is for a job application or cover letter. Make it polished and impressive.",
}

SYSTEM_PROMPT = """You are Vaani, an AI writing assistant built specifically for Indian professionals. Your job is to convert Hinglish, code-switched, or vernacular Indian text into polished, professional English.

Rules:
- Preserve the original intent and meaning completely
- Preserve the writer's tone — if they sound apologetic, keep that; if confident, keep that
- Output must sound like a fluent, professional Indian English speaker — not American or British
- Do not over-formalize. "Please find attached" energy is wrong. Natural professional is right.
- The output should work across contexts — emails to managers, LinkedIn posts, WhatsApp messages to colleagues — without being stiff or overly formal.
- Never translate cultural context away — Indian workplace norms should be reflected
- Output only the rewritten text. No explanations, no preamble, no "Here is the rewritten version:\""""


# ---------------------------------------------------------------------------
# Corpus helpers
# ---------------------------------------------------------------------------

# TODO: replace with Supabase insert later
def save_to_corpus(
    original_input: str,
    context_selected: str,
    vaani_output: str,
    user_rating: str,
    user_edited_version: str = "",
) -> None:
    file_exists = CORPUS_PATH.exists()
    with open(CORPUS_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CORPUS_COLUMNS)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "timestamp": datetime.utcnow().isoformat(),
            "original_input": original_input,
            "context_selected": context_selected,
            "vaani_output": vaani_output,
            "user_rating": user_rating,
            "user_edited_version": user_edited_version,
        })


def load_corpus() -> pd.DataFrame | None:
    if not CORPUS_PATH.exists():
        return None
    try:
        df = pd.read_csv(CORPUS_PATH)
        return df if not df.empty else None
    except Exception:
        return None


def get_metrics() -> tuple[int, int, int]:
    df = load_corpus()
    if df is None:
        return 0, 0, 0
    total = len(df)
    feedback = len(df[df["user_rating"].notna()])
    edits = len(df[df["user_edited_version"].astype(str).str.strip() != ""])
    return total, feedback, edits


# ---------------------------------------------------------------------------
# Output renderer
# ---------------------------------------------------------------------------

def render_output(text: str) -> None:
    line_count = sum(max(1, len(line) // 70 + 1) for line in text.split("\n"))
    box_height = min(400, max(120, line_count * 24 + 32))
    total_height = box_height + 52

    escaped = html_lib.escape(text)
    components.html(
        f"""
        <style>
          * {{ box-sizing: border-box; margin: 0; padding: 0; }}
          body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
          textarea {{
            width: 100%;
            height: {box_height}px;
            padding: 12px 14px;
            font-size: 15px;
            line-height: 1.6;
            color: #1a1a1a;
            background: #fafafa;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            resize: none;
            outline: none;
          }}
          .btn-row {{
            display: flex;
            justify-content: flex-end;
            margin-top: 8px;
          }}
          button {{
            padding: 7px 18px;
            font-size: 14px;
            font-weight: 500;
            color: white;
            background: #FF4B4B;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            transition: background 0.15s;
          }}
          button:hover {{ background: #e03e3e; }}
        </style>
        <textarea id="output" readonly>{escaped}</textarea>
        <div class="btn-row">
          <button id="copy-btn" onclick="copyText()">📋 Copy to clipboard</button>
        </div>
        <script>
          function copyText() {{
            const text = document.getElementById("output").value;
            navigator.clipboard.writeText(text).then(() => {{
              const btn = document.getElementById("copy-btn");
              btn.textContent = "✅ Copied!";
              setTimeout(() => btn.textContent = "📋 Copy to clipboard", 2000);
            }});
          }}
        </script>
        """,
        height=total_height,
    )


# ---------------------------------------------------------------------------
# Main UI — page config must be first Streamlit call
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Vaani — वाणी", page_icon="✨", layout="centered")

# ---------------------------------------------------------------------------
# Admin sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    with st.expander("Admin"):
        pwd = st.text_input("Password", type="password", key="admin_pwd")
        if pwd:
            if pwd == ADMIN_PASSWORD:
                st.session_state["admin_auth"] = True
            else:
                st.session_state["admin_auth"] = False
                st.error("Incorrect password")

    if st.session_state.get("admin_auth"):
        st.sidebar.subheader("Corpus viewer")
        df = load_corpus()
        if df is not None:
            total, feedback, edits = get_metrics()
            st.sidebar.caption(f"{total} rewrites · {feedback} feedback · {edits} edits")
            st.sidebar.dataframe(df, use_container_width=True)
            with open(CORPUS_PATH, "rb") as f:
                st.sidebar.download_button(
                    label="Download vaani_corpus.csv",
                    data=f,
                    file_name="vaani_corpus.csv",
                    mime="text/csv",
                )
        else:
            st.sidebar.info("No corpus data yet.")

st.title("Vaani — वाणी")
st.caption("Your professional voice in English")

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error(
        "**GROQ_API_KEY not found.** "
        "Create a `.env` file in this folder with:\n\n"
        "```\nGROQ_API_KEY=your_key_here\n```\n\n"
        "Get your key at [console.groq.com](https://console.groq.com)."
    )
    st.stop()

client = Groq(api_key=api_key)

st.divider()

user_input = st.text_area(
    "Paste your Hinglish or code-switched text here",
    placeholder="Hi sir, mujhe is project mein thoda aur time chahiye, deadline kal hai but kuch issues aa gaye hain",
    height=160,
    max_chars=INPUT_CHAR_LIMIT,
    key="user_input",
)

char_count = len(user_input)
st.caption(f"{char_count} / {INPUT_CHAR_LIMIT} characters")

context = st.selectbox(
    "Context",
    options=list(CONTEXT_INSTRUCTIONS.keys()),
    key="context",
)

rewrite_clicked = st.button("Rewrite with Vaani ✨", type="primary", use_container_width=True)

if rewrite_clicked:
    if not user_input.strip():
        st.warning("Please paste some text before rewriting.")
    else:
        context_instruction = CONTEXT_INSTRUCTIONS[context]
        system_prompt = SYSTEM_PROMPT
        if context_instruction:
            system_prompt += f"\n\nAdditional instruction for this rewrite:\n- {context_instruction}"

        with st.spinner("Vaani is thinking..."):
            try:
                response = client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Rewrite this text professionally: {user_input}"},
                    ],
                    temperature=0.4,
                    max_tokens=1024,
                )
                st.session_state["vaani_output"] = response.choices[0].message.content.strip()
                # reset feedback state for each new rewrite
                st.session_state["feedback_done"] = False
                st.session_state["show_edit_area"] = False
            except Exception as e:
                st.error(
                    f"Something went wrong while calling the Groq API. "
                    f"Please check your API key and try again.\n\n"
                    f"_(Error: {type(e).__name__}: {e})_"
                )

# ---------------------------------------------------------------------------
# Output + feedback
# ---------------------------------------------------------------------------

if st.session_state.get("vaani_output"):
    st.divider()
    st.subheader("Vaani's rewrite ✨")
    render_output(st.session_state["vaani_output"])

    if not st.session_state.get("feedback_done"):
        st.caption("How did Vaani do?")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ Looks good", use_container_width=True):
                save_to_corpus(
                    original_input=st.session_state.get("user_input", ""),
                    context_selected=st.session_state.get("context", ""),
                    vaani_output=st.session_state["vaani_output"],
                    user_rating="good",
                )
                st.session_state["feedback_done"] = True
                st.session_state["show_edit_area"] = False
                st.toast("Thanks! Saved to corpus ✨")
                st.rerun()

        with col2:
            if st.button("✏️ I'd change this", use_container_width=True):
                st.session_state["show_edit_area"] = True

        if st.session_state.get("show_edit_area"):
            user_edit = st.text_area(
                "Your preferred version",
                value=st.session_state["vaani_output"],
                height=150,
                key="user_edit",
            )
            if st.button("Submit my version ✨", type="primary"):
                save_to_corpus(
                    original_input=st.session_state.get("user_input", ""),
                    context_selected=st.session_state.get("context", ""),
                    vaani_output=st.session_state["vaani_output"],
                    user_rating="needs_change",
                    user_edited_version=user_edit,
                )
                st.session_state["feedback_done"] = True
                st.session_state["show_edit_area"] = False
                st.toast("Your version saved — this makes Vaani smarter 🙏")
                st.rerun()

# ---------------------------------------------------------------------------
# Metrics footer
# ---------------------------------------------------------------------------

st.divider()
total, feedback, edits = get_metrics()
if total == 0:
    st.caption("Be the first to leave feedback ✨")
else:
    st.caption(f"{total} rewrites · {feedback} feedback collected · {edits} edits submitted")
st.caption("Vaani is an early prototype. Your rewrites help us build better Indian professional AI. 🇮🇳")

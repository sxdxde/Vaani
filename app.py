import os
import streamlit as st
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

GROQ_MODEL = "llama-3.3-70b-versatile"
INPUT_CHAR_LIMIT = 1000

SYSTEM_PROMPT = """You are Vaani, an AI writing assistant built specifically for Indian professionals. Your job is to convert Hinglish, code-switched, or vernacular Indian text into polished, professional English.

Rules:
- Preserve the original intent and meaning completely
- Preserve the writer's tone — if they sound apologetic, keep that; if confident, keep that
- Output must sound like a fluent, professional Indian English speaker — not American or British
- Do not over-formalize. "Please find attached" energy is wrong. Natural professional is right.
- Never translate cultural context away — Indian workplace norms should be reflected
- Output only the rewritten text. No explanations, no preamble, no "Here is the rewritten version:\""""

st.set_page_config(page_title="Vaani — वाणी", page_icon="✨", layout="centered")

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

rewrite_clicked = st.button("Rewrite with Vaani ✨", type="primary", use_container_width=True)

if rewrite_clicked:
    if not user_input.strip():
        st.warning("Please paste some text before rewriting.")
    else:
        with st.spinner("Vaani is thinking..."):
            try:
                response = client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"Rewrite this text professionally: {user_input}"},
                    ],
                    temperature=0.4,
                    max_tokens=1024,
                )
                vaani_output = response.choices[0].message.content.strip()
                st.session_state["vaani_output"] = vaani_output
            except Exception as e:
                st.error(
                    f"Something went wrong while calling the Groq API. "
                    f"Please check your API key and try again.\n\n"
                    f"_(Error: {type(e).__name__}: {e})_"
                )

if "vaani_output" in st.session_state and st.session_state["vaani_output"]:
    st.divider()
    st.subheader("Vaani's rewrite")

    st.code(st.session_state["vaani_output"], language=None)

    st.caption("Click the copy icon (top-right of the box above) to copy to clipboard.")

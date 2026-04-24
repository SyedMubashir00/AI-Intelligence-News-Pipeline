import os
import streamlit as st
import requests
import feedparser
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

# ---------------- CONFIG ---------------- #
BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_FEED = "https://techcrunch.com/tag/artificial-intelligence/feed/"
USER_AGENT = "Mozilla/5.0"

# ---------------- STATE ---------------- #
def init_state():
    defaults = {
        "api_key": os.environ.get("OPENAI_API_KEY", ""),
        "articles": [],
        "selected": [],
        "output": "",
        "last_input": None,
        "history": []
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ---------------- LLM ---------------- #
def get_llm():
    if not st.session_state.api_key:
        st.error("Enter API key")
        st.stop()

    return ChatOpenAI(
        model=model,
        temperature=0.7,
        api_key=st.session_state.api_key,
        base_url=BASE_URL,
        streaming=True
    )

def stream_prompt(llm, template, values):
    prompt = PromptTemplate.from_template(template)
    chain = prompt | llm

    container = st.empty()
    output = ""

    for chunk in chain.stream(values):
        token = chunk.content or ""
        output += token
        container.markdown(output)

    return output

# ---------------- DATA ---------------- #
@st.cache_data(ttl=600)
def fetch_news(url, limit):
    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=10)
        r.raise_for_status()
        feed = feedparser.parse(r.content)
        return [e.title for e in feed.entries if e.get("title")][:limit]
    except:
        return []

# ---------------- PROMPTS ---------------- #
WRITE = """Create a {content_type} for {audience} in {tone} tone.

Headlines:
{headlines}

Requirements:
- Strong hook
- Key insight
- Practical takeaway
- CTA
"""

OPTIMIZE = """Rewrite the opening to make it more engaging:

{post}
"""

# ---------------- UI ---------------- #
st.set_page_config(page_title="AI Intelligence News Pipeline", layout="wide")

STYLE = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    :root {
        --bg: #020617;
        --panel: rgba(15, 23, 42, 0.65);
        --panel-strong: rgba(15, 23, 42, 0.82);
        --border: rgba(255,255,255,0.14);
        --text: #E2E8F0;
        --muted: #94A3B8;
        --accent: #60A5FA;
    }

    html, body, .stApp {
        background: radial-gradient(circle at top left, rgba(59, 130, 246, 0.18), transparent 24%),
                    radial-gradient(circle at bottom right, rgba(168, 85, 247, 0.14), transparent 24%),
                    linear-gradient(180deg, #020617 0%, #050B18 100%);
        color: var(--text);
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .stApp {
        min-height: 100vh;
    }

    .glass-card {
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 28px;
        backdrop-filter: blur(20px);
        box-shadow: 0 28px 70px rgba(0,0,0,0.35);
        padding: 1.8rem;
        margin-bottom: 1.5rem;
    }

    .hero-card {
        padding: 2.2rem;
    }

    .main-title {
        font-size: clamp(2.8rem, 4vw, 4rem);
        font-weight: 800;
        margin-bottom: 0.45rem;
        background: linear-gradient(135deg, #60A5FA 0%, #C084FC 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .subtitle {
        color: #94A3B8;
        font-size: 1.05rem;
        max-width: 720px;
        margin-top: 0.25rem;
    }

    .section-label {
        font-size: 1.05rem;
        font-weight: 700;
        margin-bottom: 1rem;
        color: #F8FAFC;
    }

    .stSidebar {
        background: linear-gradient(180deg, rgba(8,13,23,0.98), rgba(10,18,37,0.98));
        border-right: 1px solid rgba(255,255,255,0.08);
    }

    [data-testid="stSidebar"] .css-1d391kg {
        padding-top: 1.5rem;
    }

    .stTextInput>div>div,
    .stTextArea>div>div,
    .stSelectbox>div>div,
    .stSlider>div>div,
    .stNumberInput>div>div {
        border-radius: 16px !important;
        background: rgba(15, 23, 42, 0.48) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        color: white !important;
    }

    .stButton > button {
        border-radius: 22px !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        background: linear-gradient(135deg, rgba(59,130,246,0.96), rgba(192,132,252,0.96)) !important;
        color: #020617 !important;
        box-shadow: 0 22px 60px rgba(59,130,246,0.28) !important;
        transition: transform 0.22s ease, box-shadow 0.22s ease;
        min-width: 170px;
        min-height: 60px !important;
        padding: 1rem 1.8rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.04em !important;
        text-transform: uppercase !important;
        backdrop-filter: blur(16px) !important;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 28px 68px rgba(59,130,246,0.36) !important;
    }

    .button-panel {
        display: flex;
        justify-content: space-between;
        align-items: stretch;
        gap: 1rem;
        flex-wrap: wrap;
        background: rgba(2, 6, 23, 0.6);
        border: 1px solid rgba(255,255,255,0.08);
        box-shadow: 0 22px 42px rgba(0,0,0,0.2);
        padding: 1rem 1.2rem;
    }

    .button-group {
        display: grid;
        gap: 1rem;
        width: 100%;
    }

    .button-panel .stButton {
        width: 100%;
    }

    .output-card {
        background: rgba(15, 23, 42, 0.58);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 24px;
        padding: 1.4rem;
    }

    .output-label {
        font-size: 1rem;
        color: #CBD5E1;
        margin-bottom: 1rem;
    }

    .info-box {
        color: var(--muted);
        line-height: 1.7;
    }

    .footer-note {
        text-align: center;
        color: #94A3B8;
        font-size: 0.95rem;
        letter-spacing: 0.01em;
    }
</style>
"""

st.markdown(STYLE, unsafe_allow_html=True)
st.markdown(
    '<div class="glass-card hero-card"><h1 class="main-title">AI Intelligence News Pipeline</h1><p class="subtitle">Generate polished AI content from live AI news feeds with a premium glass UI workspace.</p></div>',
    unsafe_allow_html=True,
)

col1, col2 = st.columns([1.1, 1], gap="large")

with col1:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Studio Inputs</div>', unsafe_allow_html=True)
    content_type = st.selectbox("Content Format", ["LinkedIn Post", "Twitter Thread"])
    audience = st.selectbox("Target Audience", ["Developers", "Founders"])
    tone = st.selectbox("Tone", ["Professional", "Casual"])
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Feed Controls</div>', unsafe_allow_html=True)
    st.session_state.api_key = st.text_input("API Key", type="password", value=st.session_state.api_key)
    model = st.selectbox("Model", ["openai/gpt-oss-120b:free", "meta-llama/llama-3.3-70b-instruct:free"])
    rss_url = st.text_input("RSS Feed URL", DEFAULT_FEED)
    limit = st.slider("Headline Count", 3, 10, 5)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="glass-card button-panel">', unsafe_allow_html=True)
button_col1, button_col2 = st.columns([1.2, 0.8], gap="large")
with button_col1:
    st.markdown('<div class="button-group">', unsafe_allow_html=True)
    fetch = st.button("Fetch Headlines")
    generate = st.button("Generate")
    st.markdown('</div>', unsafe_allow_html=True)
with button_col2:
    regenerate = st.button("Regenerate")
st.markdown('</div>', unsafe_allow_html=True)

# Select headlines
if st.session_state.articles:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Select Headlines</div>', unsafe_allow_html=True)
    st.session_state.selected = st.multiselect(
        "Pick which headlines to use",
        st.session_state.articles,
        default=st.session_state.articles[:3]
    )
    st.markdown('</div>', unsafe_allow_html=True)

if fetch:
    st.session_state.articles = fetch_news(rss_url, limit)

# ---------------- PIPELINE ---------------- #
if generate or regenerate:
    llm = get_llm()

    # Use previous input if regenerate
    if regenerate and st.session_state.last_input:
        selected = st.session_state.last_input
    else:
        selected = st.session_state.selected

    if not selected:
        st.error("Select at least one headline")
        st.stop()

    st.session_state.last_input = selected

    formatted = "\n".join(f"- {h}" for h in selected)

    st.subheader("Generating...")

    # STREAMING OUTPUT
    post = stream_prompt(llm, WRITE, {
        "content_type": content_type,
        "audience": audience,
        "tone": tone,
        "headlines": formatted
    })

    final = stream_prompt(llm, OPTIMIZE, {"post": post})

    st.session_state.output = final

    st.session_state.history.append({
        "time": datetime.now().strftime("%H:%M"),
        "topic": selected[0][:50]
    })

# ---------------- OUTPUT ---------------- #
if st.session_state.output:
    st.markdown('<div class="glass-card output-card">', unsafe_allow_html=True)
    st.markdown('<div class="output-label">Final Output</div>', unsafe_allow_html=True)
    st.text_area("", st.session_state.output, height=250)
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------- HISTORY ---------------- #
if st.session_state.history:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Recent Runs</div>', unsafe_allow_html=True)
    for h in reversed(st.session_state.history[-5:]):
        st.markdown(f"<div class='info-box'>• {h['time']} — {h['topic']}</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="glass-card" style="text-align:center; padding: 1rem 1.2rem; font-size: 0.95rem; color:#94A3B8;">Created with Streamlit ❤️</div>', unsafe_allow_html=True)
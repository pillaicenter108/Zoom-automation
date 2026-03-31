import re
import streamlit as st

from zoom_automation.agents.agent import run_agent
from zoom_automation.app.scheduler import schedule_meetings


# ─────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="ZoomFlow",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ─────────────────────────────────────────
#  STYLES
# ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=DM+Sans:wght@400;500;600;700&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background: #f4f6fb !important;
    font-family: 'Inter', sans-serif !important;
    color: #1a1d2e !important;
}
[data-testid="stAppViewContainer"] {
    background: linear-gradient(160deg, #eef1f8 0%, #f7f9ff 50%, #edf0fa 100%) !important;
}
#MainMenu, footer, header,
[data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display: none !important; }

.zf-nav {
    display: flex; align-items: center; justify-content: space-between;
    padding: 14px 32px; background: #ffffff;
    border-bottom: 1px solid #e4e8f0;
    box-shadow: 0 1px 8px rgba(0,0,0,0.05);
    margin: -1rem -1rem 2rem -1rem;
}
.zf-logo {
    display: flex; align-items: center; gap: 8px;
    font-family: 'DM Sans', sans-serif;
    font-size: 1.2rem; font-weight: 700; color: #1a1d2e;
}
.zf-logo-icon {
    width: 32px; height: 32px; border-radius: 8px;
    background: linear-gradient(135deg, #2563eb, #06b6d4);
    display: flex; align-items: center; justify-content: center;
    font-size: 15px;
}
.zf-badge {
    font-size: 0.7rem; font-weight: 600; padding: 4px 10px;
    border-radius: 20px; background: #eff6ff;
    border: 1px solid #bfdbfe; color: #2563eb;
}
[data-testid="stTabs"] > div:first-child {
    border-bottom: 2px solid #e4e8f0 !important;
    background: transparent !important;
}
button[data-baseweb="tab"] {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.875rem !important; font-weight: 500 !important;
    color: #6b7280 !important; padding: 10px 22px !important;
    border: none !important; border-bottom: 2px solid transparent !important;
    border-radius: 0 !important; background: transparent !important;
    transition: all 0.2s !important;
}
button[data-baseweb="tab"]:hover { color: #2563eb !important; }
button[aria-selected="true"][data-baseweb="tab"] {
    color: #2563eb !important; border-bottom: 2px solid #2563eb !important;
    font-weight: 600 !important;
}
.page-title {
    font-family: 'DM Sans', sans-serif;
    font-size: 1.6rem; font-weight: 700; color: #1a1d2e; margin-bottom: 4px;
}
.page-sub { font-size: 0.85rem; color: #6b7280; margin-bottom: 28px; }
.info-card {
    background: #ffffff; border: 1px solid #e4e8f0;
    border-radius: 14px; padding: 18px 22px; margin-bottom: 12px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.info-card-title {
    font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.7px; color: #9ca3af; margin-bottom: 10px;
}
[data-testid="stTextInput"] > div > div {
    background: #ffffff !important; border: 1.5px solid #e4e8f0 !important;
    border-radius: 10px !important; color: #1a1d2e !important;
    font-size: 0.875rem !important; transition: border 0.2s, box-shadow 0.2s !important;
}
[data-testid="stTextInput"] > div > div:focus-within {
    border-color: #2563eb !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.10) !important;
}
[data-testid="stTextInput"] input { color: #1a1d2e !important; }
[data-testid="stTextInput"] label {
    font-size: 0.8rem !important; font-weight: 600 !important; color: #374151 !important;
}
[data-testid="stButton"] > button {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important; font-size: 0.875rem !important;
    border-radius: 10px !important; padding: 10px 22px !important;
    background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
    color: #fff !important; border: none !important;
    box-shadow: 0 2px 8px rgba(37,99,235,0.25) !important;
    transition: all 0.2s !important;
}
[data-testid="stButton"] > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 16px rgba(37,99,235,0.35) !important;
}
[data-testid="stAlert"] { border-radius: 10px !important; font-size: 0.875rem !important; }
.chat-header {
    display: flex; align-items: center; gap: 12px;
    padding: 14px 20px; background: #ffffff;
    border: 1px solid #e4e8f0; border-radius: 14px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04); margin-bottom: 12px;
}
.chat-ai-avatar {
    width: 40px; height: 40px; border-radius: 10px;
    background: linear-gradient(135deg, #2563eb, #06b6d4);
    display: flex; align-items: center; justify-content: center;
    font-size: 18px; box-shadow: 0 2px 8px rgba(37,99,235,0.25); flex-shrink: 0;
}
.chat-ai-name { font-family: 'DM Sans', sans-serif; font-weight: 700; font-size: 0.95rem; color: #1a1d2e; }
.chat-ai-status { display: flex; align-items: center; gap: 5px; font-size: 0.72rem; color: #6b7280; margin-top: 2px; }
.online-dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: #10b981; box-shadow: 0 0 5px rgba(16,185,129,0.5);
    animation: blink 2s infinite;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.4} }
.chip-row { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px; }
.chip {
    font-size: 0.74rem; font-weight: 500; padding: 5px 12px;
    border-radius: 20px; background: #eff6ff;
    border: 1px solid #bfdbfe; color: #2563eb; white-space: nowrap;
}
[data-testid="stChatMessage"] {
    background: #ffffff !important; border: 1px solid #e8ecf4 !important;
    border-radius: 14px !important; padding: 12px 16px !important;
    margin-bottom: 8px !important; box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
}
[data-testid="stChatMessage"] p {
    font-size: 0.9rem !important; line-height: 1.6 !important;
    color: #1a1d2e !important; margin: 0 !important;
}
[data-testid="stChatInput"] > div {
    background: #ffffff !important; border: 1.5px solid #e4e8f0 !important;
    border-radius: 12px !important; box-shadow: 0 2px 8px rgba(0,0,0,0.06) !important;
}
[data-testid="stChatInput"] > div:focus-within {
    border-color: #2563eb !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.10), 0 2px 8px rgba(0,0,0,0.06) !important;
}
[data-testid="stChatInput"] textarea {
    color: #1a1d2e !important; font-family: 'Inter', sans-serif !important;
    font-size: 0.9rem !important;
}
.block-container { padding: 1rem 2.5rem 2rem 2.5rem !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
#  NAVBAR
# ─────────────────────────────────────────
st.markdown("""
<div class="zf-nav">
    <div class="zf-logo">
        <div class="zf-logo-icon">⚡</div>
        ZoomFlow
    </div>
    <span class="zf-badge">v2.0 · Live</span>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
#  RENDER HELPER
# ─────────────────────────────────────────

def render_chat_response(content: str, is_meeting_list: bool):
    if not is_meeting_list:
        st.markdown(content)
        return
    for line in content.split("\n"):
        match = re.search(r"\[ID:(\d+)\]", line)
        if match:
            meeting_id   = match.group(1)
            display_line = re.sub(r"\s*·?\s*ID:\s*\[ID:\d+\]", "", line).rstrip(" ·")
            st.markdown(display_line)
            col_label, col_code = st.columns([1, 5])
            with col_label:
                st.caption("Meeting ID")
            with col_code:
                st.code(meeting_id, language=None)
        elif line.strip():
            st.markdown(line)


# ─────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {
            "role": "assistant",
            "content": (
                "👋 Hi! I'm **ZoomFlow AI**.\n\n"
                "I can help you **create**, **list**, or **update** Zoom meetings. "
                "Just tell me what you need!"
            ),
            "is_meeting_list": False,
        }
    ]


# ─────────────────────────────────────────
#  TABS
# ─────────────────────────────────────────
tab1, tab2 = st.tabs(["⚡  AI Assistant", "📊  Sheet Scheduler"])


# ══════════════════════════════════════════
#  TAB 1 — AI ASSISTANT
# ══════════════════════════════════════════
with tab1:
    st.markdown('<div class="page-title">AI Assistant</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-sub">Chat naturally to create, list, or update your Zoom meetings.</div>',
        unsafe_allow_html=True,
    )

    st.markdown("""
    <div class="chat-header">
        <div class="chat-ai-avatar">⚡</div>
        <div>
            <div class="chat-ai-name">ZoomFlow AI</div>
            <div class="chat-ai-status">
                <div class="online-dot"></div>
                Online &nbsp;·&nbsp; llama-3.1-8b-instant
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="chip-row">
        <span class="chip">📋 Show meetings in zoom 1</span>
        <span class="chip">➕ Create a meeting</span>
        <span class="chip">✏️ Reschedule a meeting</span>
        <span class="chip">📅 List upcoming meetings</span>
    </div>
    """, unsafe_allow_html=True)

    for msg in st.session_state.chat_history:
        avatar = "⚡" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            render_chat_response(msg["content"], msg.get("is_meeting_list", False))

    user_input = st.chat_input("Ask me anything about your Zoom meetings...")

    if user_input:
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input,
            "is_meeting_list": False,
        })
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)

        with st.chat_message("assistant", avatar="⚡"):
            with st.spinner("Thinking..."):
                text_reply, is_list, tool_name, pending = run_agent(
                    user_input,
                    st.session_state.chat_history[:-1]
                )
            render_chat_response(text_reply, is_list)

        st.session_state.chat_history.append({
            "role": "assistant",
            "content": text_reply,
            "is_meeting_list": is_list,
            "pending_action": pending,
        })
        st.rerun()


# ══════════════════════════════════════════
#  TAB 2 — SHEET SCHEDULER
# ══════════════════════════════════════════
with tab2:
    col_left, col_right = st.columns([3, 2], gap="large")

    with col_left:
        st.markdown('<div class="page-title">Sheet Scheduler</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="page-sub">Paste a Google Sheet ID to bulk-create all pending Zoom meetings.</div>',
            unsafe_allow_html=True,
        )

        sheet_id = st.text_input(
            "Google Sheet ID",
            placeholder="e.g. 1bBjDqKt-ANr33o4dMug1n9WRgq8McFkony1Tbh0Oobs",
        )

        if st.button("🚀  Schedule Meetings"):
            if not sheet_id.strip():
                st.warning("Please enter a Google Sheet ID to continue.")
            else:
                with st.spinner("Processing sheet..."):
                    schedule_meetings(sheet_id, dry_run=False)

    with col_right:
        st.markdown('<div style="height:72px"></div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="info-card">
            <div class="info-card-title">Required Columns</div>
            <div style="font-size:0.82rem;color:#374151;line-height:2.1">
                Call Title &nbsp;·&nbsp; Duration &nbsp;·&nbsp; Zoom Account<br>
                Status &nbsp;·&nbsp; MeetingID &nbsp;·&nbsp; Passcode &nbsp;·&nbsp; JoinURL<br>
                Date &amp; Time PDT/PST &nbsp;·&nbsp; UTC &nbsp;·&nbsp; IST<br>
                Recurrence &nbsp;·&nbsp; Occurrences
            </div>
        </div>
        <div class="info-card">
            <div class="info-card-title">Row Status Logic</div>
            <div style="font-size:0.82rem;color:#374151;line-height:2.1">
                <span style="color:#10b981;font-weight:700">●</span>&nbsp;
                <b>pending</b> — will be processed<br>
                <span style="color:#d1d5db;font-weight:700">●</span>&nbsp;
                <i>any other value</i> — skipped
            </div>
        </div>
        <div class="info-card">
            <div class="info-card-title">Zoom Accounts</div>
            <div style="font-size:0.82rem;color:#374151">
                Use keys defined in
                <code style="background:#f3f4f6;padding:1px 6px;border-radius:4px;font-size:0.78rem">ZOOM_ACCOUNTS</code>
                — e.g.
                <code style="background:#f3f4f6;padding:1px 6px;border-radius:4px;font-size:0.78rem">zoom 1</code>,
                <code style="background:#f3f4f6;padding:1px 6px;border-radius:4px;font-size:0.78rem">zoom 2</code>
            </div>
        </div>
        """, unsafe_allow_html=True)
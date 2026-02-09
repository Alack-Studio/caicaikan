import streamlit as st
from openai import OpenAI

# 1. 极简精致 UI 配置
st.set_page_config(page_title="AI 猜猜看", layout="centered")

if "theme" not in st.session_state: st.session_state.theme = "白天"
if "msgs" not in st.session_state: st.session_state.msgs = []
if "over" not in st.session_state: st.session_state.over = False
if "count" not in st.session_state: st.session_state.count = 0
if "model" not in st.session_state: st.session_state.model = "gemini-2.0-flash"

# 侧边栏
with st.sidebar:
    st.session_state.theme = st.radio("🌓 风格切换", ["白天", "夜晚"], horizontal=True)
    if st.button("🔄 重置进度", use_container_width=True):
        st.session_state.msgs = []
        st.session_state.over = False
        st.session_state.count = 0
        st.rerun()

# 定义精致主题色调
if st.session_state.theme == "夜晚":
    bg, txt, b_bg, b_txt, b_bd, c_bg = "#121212", "#D1D1D1", "#1E1E1E", "#D1D1D1", "#2D2D2D", "rgba(255,255,255,0.05)"
else:
    bg, txt, b_bg, b_txt, b_bd, c_bg = "#FFFFFF", "#2C3E50", "#FFFFFF", "#34495E", "#F0F0F0", "#F9FBFC"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg}; color: {txt}; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
    /* 精致按钮：缩小高度，添加细微阴影 */
    div.stButton > button {{
        border-radius: 8px; height: 3.0em; font-size: 0.95rem;
        font-weight: 500; border: 1px solid {b_bd};
        background-color: {b_bg}; color: {b_txt}; width: 100%; margin-bottom: 6px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05); transition: all 0.2s;
    }}
    div.stButton > button:hover {{ border-color: #3498DB; color: #3498DB; }}
    div.stButton > button:active {{ transform: translateY(1px); box-shadow: none; }}
    /* 聊天气泡：标准字号，优雅间距 */
    .stChatMessage p, .stMarkdown h3 {{ font-size: 1.05rem; color: {txt}; line-height: 1.6; font-weight: 400; }}
    .stChatMessage {{ background-color: {c_bg}; border-radius: 10px; padding: 12px 18px; margin-bottom: 12px; border: 1px solid {b_bd}; }}
    header {{visibility: hidden;}}
    /* 单选框间距优化 */
    div[data-testid="stMarkdownContainer"] p {{ font-size: 0.9rem; color: {txt}; opacity: 0.8; }}
    </style>
    """, unsafe_allow_html=True)

st.title("🕵️ AI 猜猜看")

# 2. API 逻辑
if "API_KEY" not in st.secrets:
    st.error("🔑 请在 Secrets 中配置 API_KEY")
    st.stop()

client = OpenAI(api_key=st.secrets["API_KEY"], base_url="https://api.gptsapi.net/v1")

def ask_ai(user_inp=None):
    if user_inp:
        st.session_state.msgs.append({"role": "user", "content": user_inp})
    
    sys_prompt = "你是一个顶级读心者。我心里想一个人物，你通过是非题来猜。严禁前5轮询问性别或国籍。一次一问且带问号。确定后以'答案是：[人名]'开头。"
    
    try:
        res = client.chat.completions.create(
            model=st.session_state.model, 
            messages=[{"role": "system", "content": sys_prompt}] + st.session_state.msgs,
            temperature=0.8
        )
        reply = res.choices[0].message.content
        st.session_state.msgs.append({"role": "assistant", "content": reply})
        if st.session_state.count > 0:
            if "?" not in reply and "？" not in reply or "答案是" in reply:
                st.session_state.over = True
    except Exception as e:
        st.error(f"📡 连接稍有延迟，请点

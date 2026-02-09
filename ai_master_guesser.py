import streamlit as st
from openai import OpenAI

# 1. UI 动态主题与手机适配
st.set_page_config(page_title="AI 猜猜看", layout="centered")

if "theme" not in st.session_state: st.session_state.theme = "白天"

with st.sidebar:
    st.session_state.theme = st.radio("🌓 主题", ["白天", "夜晚"], horizontal=True)
    if st.button("🔄 重新开始", use_container_width=True):
        for k in ["msgs", "over", "count"]: 
            if k in st.session_state: del st.session_state[k]
        st.rerun()

# 定义主题颜色
if st.session_state.theme == "夜晚":
    bg, txt, b_bg, b_txt, b_bd, c_bg = "#121212", "#E0E0E0", "#1E1E1E", "#E0E0E0", "#333333", "#1E1E1E"
else:
    bg, txt, b_bg, b_txt, b_bd, c_bg = "#FFFFFF", "#1F1F1F", "#FFFFFF", "#31333F", "#E0E0E0", "#F8F9FA"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg}; color: {txt}; }}
    div.stButton > button {{
        border-radius: 10px; height: 3.2em; font-size: 1.25rem !important;
        font-weight: 600; border: 1px solid {b_bd};
        background-color: {b_bg}; color: {b_txt}; width: 100%; margin-bottom: 8px;
    }}
    .stChatMessage p, .stMarkdown h3 {{ font-size: 1.35rem !important; color: {txt}; line-height: 1.5; }}
    .stChatMessage {{ background-color: {c_bg}; border-radius: 12px; padding: 10px 15px; margin-bottom: 10px; }}
    header {{visibility: hidden;}}
    div[data-testid="stMarkdownContainer"] p {{ font-size: 1.1rem; color: {txt}; }}
    </style>
    """, unsafe_allow_html=True)

st.title("🕵️ AI 猜猜看")

# 2. 状态初始化
ks = ["msgs", "over", "count", "model"]
for k in ks:
    if k not in st.session_state: 
        st.session_state[k] = [] if k=="msgs" else ("gemini-2.0-flash" if k=="model" else 0 if k=="count" else False)

# 3. API 逻辑
if "API_KEY" not in st.secrets:
    st.error("🔑 请配置 API_KEY"); st.stop()

client = OpenAI(api_key=st.secrets["API_KEY"], base_url="https://api.gptsapi.net/v1")

def ask_ai(inp=None):
    if inp: st.session_state.msgs.append({"role": "user", "content": inp})
    sys = "你是一个顶级读心者。我心里想一个著名人物，你通过是非题来猜。严禁前5轮询问性别或国籍。一次一问且带问号。确定后以'答案是：[人名]'开头。"
    try:
        res = client.chat.completions.create(
            model=st.session_state.model, 
            messages=[{"role":"system","content":sys}] + st.session_state.msgs, 
            temperature=0.8
        )
        reply = res.choices[0].message.content
        st.session_state.msgs.append({"role": "assistant", "content": reply})
        if st.session_state.count > 0 and ("?" not in reply and "？" not in reply or "答案是" in reply):
            st.session_state.over = True
    except: st.error("📡 信号波动，请点击重试")

# 4. 界面渲染 (修复缩进)
if not st.session_state.msgs:
    st.write("---")
    st.session_state.model = st.radio("🔮 选择挑战对象：", ["gemini-2.0-flash", "gemini-1.5-pro", "gpt-4o"], captions=["⚡ 极速", "🧠 深度", "⚖️ 稳健"])
    if st.button("🚀 开始游戏", use_container_width=True, type="primary"):
        with st.spinner("🕵️ AI 思考中..."):
            ask_ai(); st.rerun()

elif not st.session_state.over:
    st.chat_message("assistant", avatar="🕵️").markdown(f"### {st.session_state.msgs[-1]['content']}")
    
    def btn_click(a):
        st.session_state.count += 1
        ask_ai(a)
    
    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1: st.button("✅ 是", on_click=btn_click, args=("是的",), use_container_width=True, type="primary")
    with c2: st.button("❌ 否", on_click=btn_click, args=("不是",), use_container_width=True)
    with c3: st.button("❔ 模糊", on_click=btn_click, args=("不确定",), use_container_width=True)

else:
    st.balloons()
    st.chat_message("assistant", avatar="🎯").markdown(f"### {st.session_state.msgs[-1]['content']}")
    if st.button("🎮 再玩一局", use_container_width=True, type="primary"):
        for k in ["msgs", "over", "count"]: 
            if k in st.session_state: del st.session_state[k]
        st.rerun()

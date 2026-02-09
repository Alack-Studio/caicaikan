import streamlit as st
from openai import OpenAI

# 1. 精致 UI 配置：标准字号、柔和投影
st.set_page_config(page_title="AI 猜猜看", layout="centered")

if "theme" not in st.session_state: st.session_state.theme = "白天"
if "msgs" not in st.session_state: st.session_state.msgs = []
if "over" not in st.session_state: st.session_state.over = False
if "count" not in st.session_state: st.session_state.count = 0
# 默认使用你列表中选中的那个
if "model" not in st.session_state: st.session_state.model = "gemini-2.5-flash-lite"

with st.sidebar:
    st.session_state.theme = st.radio("🌓 风格", ["白天", "夜晚"], horizontal=True)
    if st.button("🔄 重置进度", use_container_width=True):
        st.session_state.msgs, st.session_state.over, st.session_state.count = [], False, 0
        st.rerun()

# 定义精致主题色调
if st.session_state.theme == "夜晚":
    bg, txt, b_bg, b_txt, b_bd, c_bg = "#121212", "#D1D1D1", "#1E1E1E", "#D1D1D1", "#2D2D2D", "rgba(255,255,255,0.05)"
else:
    bg, txt, b_bg, b_txt, b_bd, c_bg = "#FFFFFF", "#2C3E50", "#FFFFFF", "#34495E", "#F0F0F0", "#F9FBFC"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg}; color: {txt}; font-family: -apple-system, sans-serif; }}
    /* 精致按钮：0.95rem 字体 */
    div.stButton > button {{
        border-radius: 8px; height: 3.0em; font-size: 0.95rem; font-weight: 500;
        border: 1px solid {b_bd}; background-color: {b_bg}; color: {b_txt};
        width: 100%; margin-bottom: 6px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }}
    div.stButton > button:active {{ transform: translateY(1px); }}
    /* 精致气泡：1.05rem 字体 */
    .stChatMessage p, .stMarkdown h3 {{ font-size: 1.05rem; color: {txt}; line-height: 1.6; }}
    .stChatMessage {{ background-color: {c_bg}; border-radius: 10px; padding: 12px; border: 1px solid {b_bd}; }}
    header {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

st.title("🕵️ AI 猜猜看")

# 2. 核心 API 逻辑
if "API_KEY" not in st.secrets:
    st.error("🔑 请配置 API_KEY"); st.stop()

client = OpenAI(api_key=st.secrets["API_KEY"], base_url="https://api.gptsapi.net/v1")

def ask_ai(inp=None):
    if inp: st.session_state.msgs.append({"role": "user", "content": inp})
    sys = "你是一个顶级读心者。我心里想一个人物，你通过是非题来猜。一次一问带问号。确定后以'答案是：[人名]'开头。"
    
    try:
        res = client.chat.completions.create(
            model=st.session_state.model, 
            messages=[{"role": "system", "content": sys}] + st.session_state.msgs,
            temperature=0.8
        )
        reply = res.choices[0].message.content
        st.session_state.msgs.append({"role": "assistant", "content": reply})
        # 判定结束：无问号或包含答案前缀
        if st.session_state.count > 0 and ("?" not in reply and "？" not in reply or "答案是" in reply):
            st.session_state.over = True
    except Exception as e:
        st.error(f"📡 API 访问异常 ({st.session_state.model}): {str(e)}")

# 3. 游戏交互流程
if not st.session_state.msgs:
    st.write("---")
    # 更新为你截图中的可用模型 ID
    st.session_state.model = st.radio(
        "🔮 选择挑战对象", 
        ["gemini-2.5-flash-lite", "gemini-2.5-pro", "gemini-3-pro-preview"], 
        captions=["⚡ 极速对弈", "🧠 深度推理", "🔥 终极智商 (预览版)"],
        index=0
    )
    if st.button("🚀 开始游戏", use_container_width=True, type="primary"):
        with st.spinner("AI 正在同步思维..."):
            ask_ai()
            if st.session_state.msgs: st.rerun()

elif not st.session_state.over:
    st.chat_message("assistant", avatar="🕵️").markdown(f"### {st.session_state.msgs[-1]['content']}")
    def h_click(a):
        st.session_state.count += 1
        ask_ai(a)
    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1: st.button("✅ 是", on_click=h_click, args=("是的",), use_container_width=True, type="primary")
    with c2: st.button("❌ 否", on_click=h_click, args=("不是",), use_container_width=True)
    with c3: st.button("❔ 模糊", on_click=h_click, args=("不确定",), use_container_width=True)

else:
    st.balloons()
    st.chat_message("assistant", avatar="🎯").markdown(f"### {st.session_state.msgs[-1]['content']}")
    st.success("🎯 游戏结束，真相大白！")
    if st.button("🎮 再玩一局", use_container_width=True, type="primary"):
        st.session_state.msgs, st.session_state.over, st.session_state.count = [], False, 0
        st.rerun()


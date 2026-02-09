import streamlit as st
import google.generativeai as genai

# ==========================================
# 1. 页面配置与样式
# ==========================================
st.set_page_config(page_title="AI 读心神算子", page_icon="🔮", layout="centered")

st.markdown("""
    <style>
    div.stButton > button {
        border-radius: 10px;
        height: 3.5em;
        font-weight: bold;
    }
    .stChatMessage {
        background-color: #f0f2f6;
        border-radius: 15px;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. API 安全配置
# ==========================================
if "GEMINI_API_KEY" not in st.secrets:
    st.error("🔑 请在 Streamlit 控制台配置 GEMINI_API_KEY")
    st.stop()

API_KEY = "".join(st.secrets["GEMINI_API_KEY"].split())
genai.configure(api_key=API_KEY)

# 使用你列表中最稳的别名
model = genai.GenerativeModel('models/gemini-flash-latest')

def safe_send(chat, msg):
    try:
        response = chat.send_message(msg)
        return response.text, None
    except Exception as e:
        err_msg = str(e)
        if "429" in err_msg: return None, "LIMIT"
        return None, err_msg

# ==========================================
# 3. 核心逻辑处理 (无 rerun 版)
# ==========================================

# 按钮点击后的处理函数
def handle_user_choice(ans_text):
    # 增加计数
    st.session_state.question_count += 1
    
    # 调用 AI
    res, err = safe_send(st.session_state.chat_session, ans_text)
    
    if err == "LIMIT":
        st.session_state.question_count -= 1
        st.session_state.error_msg = "⏰ 频率太快，请等 10 秒再点。"
    elif err:
        st.session_state.error_msg = f"❌ 错误: {err}"
    else:
        st.session_state.current_question = res
        st.session_state.error_msg = None
        
        # 判定结束逻辑
        has_q = "?" in res or "？" in res
        is_guess = any(w in res for w in ["猜", "名字是", "他是", "我想到了"])
        
        if not has_q or is_guess:
            st.session_state.game_over = True

# 初始化会话
if "chat_session" not in st.session_state:
    st.session_state.chat_session = model.start_chat(history=[])
    st.session_state.game_over = False
    st.session_state.question_count = 0
    st.session_state.error_msg = None
    
    with st.spinner("🔮 正在连接 AI 大脑..."):
        prompt = "你现在是一个读心神算子。我心里想一个著名人物。你问是非题猜他是谁。请开始第一问。"
        res, err = safe_send(st.session_state.chat_session, prompt)
        if res:
            st.session_state.current_question = res
        else:
            st.error(f"启动失败: {err}")
            st.stop()

# ==========================================
# 4. 界面渲染
# ==========================================
st.title("🕵️ AI 读心神算子")

with st.sidebar:
    st.header("📊 战况")
    st.write(f"步数：{st.session_state.question_count}")
    if st.button("🔄 重新开始", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun() # 这里的 rerun 是允许的，因为不在回调函数里

# 错误提示
if st.session_state.error_msg:
    st.warning(st.session_state.error_msg)

if not st.session_state.game_over:
    # 展示 AI 问题
    st.chat_message("assistant", avatar="🔮").write(st.session_state.current_question)
    
    st.divider()
    
    # 交互按钮 (注意：不再需要 st.rerun()，回调结束后会自动刷新)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.button("✅ 是的", on_click=handle_user_choice, args=("是的",), use_container_width=True, type="primary")
    with c2:
        st.button("❌ 不是", on_click=handle_user_choice, args=("不是",), use_container_width=True)
    with c3:
        st.button("❔ 不确定", on_click=handle_user_choice, args=("不确定",), use_container_width=True)

else:
    st.balloons()
    st.success("🎯 AI 锁定了答案！")
    st.chat_message("assistant", avatar="🎯").write(st.session_state.current_question)
    
    if st.button("🎮 挑战下一局", use_container_width=True, type="primary"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

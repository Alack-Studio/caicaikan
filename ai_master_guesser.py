import streamlit as st
import google.generativeai as genai
import time

# ==========================================
# 1. 页面配置
# ==========================================
st.set_page_config(page_title="AI 读心神算子", page_icon="🔮", layout="centered")

# ==========================================
# 2. 状态全局初始化
# ==========================================
init_values = {
    "chat_session": None,
    "game_over": False,
    "question_count": 0,
    "error_msg": None,
    "current_question": None
}

for key, value in init_values.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ==========================================
# 3. API 配置与安全发送
# ==========================================
if "GEMINI_API_KEY" not in st.secrets:
    st.error("🔑 请在 Streamlit 控制台配置 GEMINI_API_KEY")
    st.stop()

API_KEY = "".join(st.secrets["GEMINI_API_KEY"].split())
genai.configure(api_key=API_KEY)

# 尝试使用最稳定的别名
MODEL_NAME = 'models/gemini-flash-latest'
model = genai.GenerativeModel(MODEL_NAME)

def safe_send(chat, msg):
    try:
        response = chat.send_message(msg)
        return response.text, None
    except Exception as e:
        err_msg = str(e)
        if "429" in err_msg: return None, "LIMIT"
        return None, err_msg

# ==========================================
# 4. 核心逻辑处理
# ==========================================
def handle_user_choice(ans_text):
    st.session_state.question_count += 1
    res, err = safe_send(st.session_state.chat_session, ans_text)
    
    if err == "LIMIT":
        st.session_state.question_count -= 1
        st.session_state.error_msg = "⏰ AI 思考过度，请等待 15 秒再点击。"
    elif err:
        st.session_state.error_msg = f"❌ 逻辑中断: {err}"
    else:
        st.session_state.current_question = res
        st.session_state.error_msg = None
        # 结束判定
        has_q = "?" in res or "？" in res
        is_guess = any(w in res for w in ["猜", "名字是", "答案是", "他是"])
        if not has_q or is_guess:
            st.session_state.game_over = True

# ==========================================
# 5. 界面渲染
# ==========================================
st.title("🕵️ AI 读心神算子")

# 侧边栏
with st.sidebar:
    st.header("📊 实时状态")
    st.write(f"步数：{st.session_state.question_count}")
    if st.button("🔄 强制重置游戏", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

# --- 关键修复：处理启动时的连接 ---
if st.session_state.chat_session is None or st.session_state.current_question is None:
    st.info("🔮 正在尝试唤醒 AI 大脑...")
    if st.button("🚀 点击开始连接"):
        with st.spinner("正在穿越时空..."):
            st.session_state.chat_session = model.start_chat(history=[])
            prompt = "你现在是一个读心神算子。我心里想一个著名人物。你问是非题猜他是谁。请开始第一问。"
            res, err = safe_send(st.session_state.chat_session, prompt)
            if err == "LIMIT":
                st.error("⚠️ 启动失败：API 频率限制。请等待 60 秒后再试。")
            elif err:
                st.error(f"⚠️ 连接失败：{err}")
            else:
                st.session_state.current_question = res
                st.rerun()
    st.stop()

# 正常游戏界面
if st.session_state.error_msg:
    st.warning(st.session_state.error_msg)

if not st.session_state.game_over:
    st.chat_message("assistant", avatar="🔮").write(st.session_state.current_question)
    st.divider()
    
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

import streamlit as st
import google.generativeai as genai

# ==========================================
# 1. 视觉装饰与页面配置
# ==========================================
st.set_page_config(page_title="AI 读心神算子", page_icon="🔮", layout="centered")

# 更加稳健的 CSS
st.markdown("""
    <style>
    .stApp {
        background-color: #f8f9fa;
    }
    div.stButton > button {
        background-color: #ffffff;
        color: #31333F;
        border: 1px solid #d1d3d8;
        border-radius: 10px;
        padding: 10px;
        font-weight: bold;
        transition: all 0.2s ease;
    }
    div.stButton > button:hover {
        border-color: #ff4b4b;
        color: #ff4b4b;
        background-color: #fffafa;
    }
    .status-box {
        padding: 15px;
        border-radius: 10px;
        background-color: #ffffff;
        border-left: 5px solid #ff4b4b;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. API 安全初始化
# ==========================================
if "GEMINI_API_KEY" not in st.secrets:
    st.error("🔑 请在 Streamlit Secrets 中配置 API Key")
    st.stop()

API_KEY = "".join(st.secrets["GEMINI_API_KEY"].split())
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('models/gemini-flash-latest')

def safe_send(chat, msg):
    try:
        response = chat.send_message(msg)
        return response.text, None
    except Exception as e:
        err = str(e)
        if "429" in err: return None, "LIMIT"
        return None, err

# ==========================================
# 3. 游戏核心逻辑
# ==========================================
if "chat_session" not in st.session_state:
    st.session_state.chat_session = model.start_chat(history=[])
    st.session_state.game_over = False
    st.session_state.question_count = 0
    
    with st.spinner("🔮 正在连接 AI 大脑..."):
        prompt = "你现在是一个读心神算子。我心里想一个著名人物。你问是非题猜他是谁。请开始第一问。"
        res, err = safe_send(st.session_state.chat_session, prompt)
        if res:
            st.session_state.current_question = res
        else:
            st.error(f"启动失败: {err}")
            st.stop()

# ==========================================
# 4. 侧边栏：规则与重置
# ==========================================
with st.sidebar:
    st.header("🕵️ 读心屋说明")
    st.markdown("1. 心里想一个著名人物\n2. 回答 AI 的是非题\n3. 看看多少步能被猜中")
    st.divider()
    st.write(f"📊 当前进度：第 **{st.session_state.question_count + 1}** 步")
    if st.button("🔄 重新开始", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

# ==========================================
# 5. 主交互界面
# ==========================================
st.title("🕵️ AI 读心神算子")

if not st.session_state.game_over:
    # 气泡展示 AI 的提问
    st.chat_message("assistant", avatar="🔮").write(st.session_state.current_question)
    
    st.write("---")
    st.caption("👇 请告诉 AI 你的答案：")

    # 定义按钮点击后的逻辑
    def on_answer(ans_text):
        st.session_state.question_count += 1
        with st.spinner("🧠 AI 正在排查线索..."):
            res, err = safe_send(st.session_state.chat_session, ans_text)
            if err == "LIMIT":
                st.session_state.question_count -= 1
                st.warning("⏰ 别点太快，AI 正在擦汗。请等 10 秒再试。")
            elif err:
                st.error(f"意外错误: {err}")
            else:
                st.session_state.current_question = res
                
                # --- 强化版判定逻辑 ---
                has_q = "?" in res or "？" in res
                # 只有当 AI 没问问题（没问号），且包含猜测关键词时，才判定为游戏结束
                is_guess = any(w in res for w in ["我猜", "答案是", "他是", "我想到了"])
                if not has_q and is_guess:
                    st.session_state.game_over = True
                elif not has_q: # 没有任何问号，通常也是给结果了
                    st.session_state.game_over = True
        st.rerun()

    # 渲染按钮
    c1, c2, c3 = st.columns(3)
    with c1:
        st.button("✅ 是的", on_click=on_answer, args=("是的",), use_container_width=True)
    with c2:
        st.button("❌ 不是", on_click=on_answer, args=("不是",), use_container_width=True)
    with c3:
        st.button("❔ 不确定", on_click=on_answer, args=("不确定",), use_container_width=True)

# 游戏结束展示
else:
    st.balloons()
    st.success("🎯 AI 已经锁定了答案！")
    st.chat_message("assistant", avatar="🎯").write(st.session_state.current_question)
    
    st.write("---")
    if st.button("🎮 挑战下一局", type="primary", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

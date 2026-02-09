import streamlit as st
import google.generativeai as genai
import time

# ==========================================
# 1. 安全配置 (已针对云端优化)
# ==========================================
if "GEMINI_API_KEY" not in st.secrets:
    st.error("❌ 未在 Secrets 中找到 GEMINI_API_KEY")
    st.stop()

# 自动清洗 Key 格式
API_KEY = "".join(st.secrets["GEMINI_API_KEY"].split())

try:
    genai.configure(api_key=API_KEY)
    # 使用你可用列表中最稳定的“最新版”别名
    MODEL_NAME = 'models/gemini-flash-latest'
    model = genai.GenerativeModel(MODEL_NAME)
except Exception as e:
    st.error(f"初始化失败: {e}")
    st.stop()

# ==========================================
# 2. 页面设置
# ==========================================
st.set_page_config(page_title="AI 读心神算子", page_icon="🕵️")
st.title("🕵️ AI 读心神算子：稳定分发版")

# ==========================================
# 3. 核心函数：带频率保护的发送
# ==========================================
def safe_send_message(chat, message):
    try:
        response = chat.send_message(message)
        return response.text, None
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg:
            return None, "QUOTA_EXCEEDED"
        return None, error_msg

# ==========================================
# 4. 游戏状态初始化
# ==========================================
if "chat_session" not in st.session_state:
    st.session_state.chat_session = model.start_chat(history=[])
    st.session_state.game_over = False
    st.session_state.question_count = 0
    st.session_state.current_question = ""
    
    with st.spinner("🕵️ AI 正在构思线索..."):
        prompt = (
            "我们玩猜人物游戏。我心里想一个著名人物，你作为猜题者。 "
            "规则：1. 只能问‘是/否’类问题。 2. 一次一个问题。 "
            "3. 当你确定答案时，直接给出名字。请开始你的第一问。"
        )
        res_text, err = safe_send_message(st.session_state.chat_session, prompt)
        
        if err == "QUOTA_EXCEEDED":
            st.warning("⏰ 访问太频繁啦！请等待 30 秒后刷新网页。")
            st.stop()
        elif err:
            st.error(f"启动失败: {err}")
            st.stop()
        else:
            st.session_state.current_question = res_text

# ==========================================
# 5. 界面交互
# ==========================================
with st.sidebar:
    st.success(f"运行状态：已连接")
    st.info(f"驱动引擎：{MODEL_NAME}")
    if st.button("🔄 重新开始游戏"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

if not st.session_state.get("game_over", False):
    st.write(f"### 第 {st.session_state.question_count + 1} 问：")
    st.info(st.session_state.current_question)

    def on_click(ans):
        st.session_state.question_count += 1
        with st.spinner("AI 正在思考..."):
            res_text, err = safe_send_message(st.session_state.chat_session, ans)
            
            if err == "QUOTA_EXCEEDED":
                st.session_state.question_count -= 1
                st.error("⚠️ 刚才那下‘超速’了。请等待 10 秒再点一次。")
            elif err:
                st.error(f"出错啦: {err}")
            else:
                st.session_state.current_question = res_text
                # 判定结束逻辑：兼容中英文问号
                has_q = "?" in res_text or "？" in res_text
                if not has_q or any(w in res_text for w in ["猜", "名字是", "他是"]):
                    st.session_state.game_over = True
        st.rerun()

    c1, c2, c3 = st.columns(3)
    with c1: st.button("✅ 是的", use_container_width=True, type="primary", on_click=on_click, args=("是的",))
    with c2: st.button("❌ 不是", use_container_width=True, on_click=on_click, args=("不是",))
    with c3: st.button("❔ 不确定", use_container_width=True, on_click=on_click, args=("不确定",))

else:
    st.balloons()
    st.success("🎯 **AI 锁定了最终答案！**")
    st.markdown(f"### {st.session_state.current_question}")
    if st.button("🎮 再玩一局", type="primary", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

import streamlit as st
import google.generativeai as genai

# ==========================================
# 1. 云端安全配置 (自动清洗 Key)
# ==========================================
if "GEMINI_API_KEY" not in st.secrets:
    st.error("❌ 未在 Secrets 中找到 GEMINI_API_KEY，请检查 Streamlit 后台设置。")
    st.stop()

# 获取并强制清洗 Key
RAW_KEY = st.secrets["GEMINI_API_KEY"]
API_KEY = "".join(RAW_KEY.split())

# 配置 Google AI
try:
    genai.configure(api_key=API_KEY)
    # 使用你诊断列表里确认可用的 2.0 版本，它是目前云端最稳定的
    model = genai.GenerativeModel('gemini-2.0-flash')
except Exception as e:
    st.error(f"❌ 初始化失败: {e}")
    st.stop()

# ==========================================
# 2. 页面设置
# ==========================================
st.set_page_config(page_title="AI 读心神算子", page_icon="🕵️")
st.title("🕵️ AI 读心神算子：云端稳定版")

# ==========================================
# 3. 核心游戏状态初始化
# ==========================================
if "chat_session" not in st.session_state:
    st.session_state.chat_session = model.start_chat(history=[])
    st.session_state.game_over = False
    st.session_state.question_count = 0
    st.session_state.current_question = "正在连接 AI 大脑..."
    
    with st.spinner("🕵️ AI 正在构思线索..."):
        try:
            prompt = (
                "我们玩猜人物游戏。我心里想一个著名人物，你作为猜题者。 "
                "规则：1. 只能问‘是/否’类问题。 2. 一次一个问题。 "
                "3. 当你确定答案时，直接给出名字。请开始你的第一问。"
            )
            response = st.session_state.chat_session.send_message(prompt)
            st.session_state.current_question = response.text
        except Exception as e:
            # 这里会把隐藏的 ClientError 详情直接显示出来
            st.error(f"⚠️ AI 响应失败。详情: {e}")
            st.stop()

# ==========================================
# 4. 游戏界面展示
# ==========================================
if not st.session_state.game_over:
    st.write(f"### 第 {st.session_state.question_count + 1} 问：")
    st.info(st.session_state.current_question)

    def on_click(ans):
        st.session_state.question_count += 1
        with st.spinner("AI 正在深度思考..."):
            try:
                res = st.session_state.chat_session.send_message(ans)
                reply = res.text
                st.session_state.current_question = reply
                
                # --- 判定逻辑修复版 ---
                # 同时检测中英文问号，并确保不是在猜测
                has_q = "?" in reply or "？" in reply
                if not has_q or any(word in reply for word in ["我猜", "答案是", "他是"]):
                    st.session_state.game_over = True
            except Exception as e:
                st.error(f"请求失败: {e}")
        st.rerun()

    c1, c2, c3 = st.columns(3)
    with c1:
        st.button("✅ 是的", use_container_width=True, on_click=on_click, args=("是的",), type="primary")
    with c2:
        st.button("❌ 不是", use_container_width=True, on_click=on_click, args=("不是",))
    with c3:
        st.button("❔ 不确定", use_container_width=True, on_click=on_click, args=("不确定",))

# 游戏结算页面
else:
    st.balloons()
    st.success("🎯 **AI 锁定了最终答案！**")
    st.markdown(f"### {st.session_state.current_question}")
    
    if st.button("🎮 再来一局", type="primary", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

with st.sidebar:
    st.write(f"当前提问次数: {st.session_state.question_count}")
    if st.button("强制重启游戏"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

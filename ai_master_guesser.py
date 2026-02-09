import streamlit as st
import google.generativeai as genai

# ==========================================
# 1. 安全配置 (已针对云端优化)
# ==========================================
if "GEMINI_API_KEY" not in st.secrets:
    st.error("❌ 未在 Secrets 中找到 GEMINI_API_KEY")
    st.stop()

# 自动清洗 Key，防止云端读取异常
API_KEY = "".join(st.secrets["GEMINI_API_KEY"].split())

try:
    genai.configure(api_key=API_KEY)
    # 锁定你本地运行成功的 3.0 预览版模型
    MODEL_NAME = 'models/gemini-3-flash-preview'
    model = genai.GenerativeModel(MODEL_NAME)
except Exception as e:
    st.error(f"初始化失败: {e}")
    st.stop()

# ==========================================
# 2. 页面设置
# ==========================================
st.set_page_config(page_title="AI 读心神算子", page_icon="🕵️")
st.title("🕵️ AI 读心神算子：Gemini 3 驱动")

# ==========================================
# 3. 核心游戏逻辑
# ==========================================
if "chat_session" not in st.session_state:
    st.session_state.chat_session = model.start_chat(history=[])
    st.session_state.game_over = False
    st.session_state.question_count = 0
    
    with st.spinner("🕵️ Gemini 3 正在扫描线索..."):
        try:
            prompt = (
                "我们玩猜人物游戏。我心里想一个著名人物，你作为猜题者。 "
                "规则：1. 只能问‘是/否’类问题。 2. 一次一个问题。 "
                "3. 当你确定答案时，直接给出名字。请开始第一问。"
            )
            response = st.session_state.chat_session.send_message(prompt)
            st.session_state.current_question = response.text
        except Exception as e:
            if "429" in str(e):
                st.error("⚠️ Gemini 3 此时访问量过大（配额限制）。请稍等 1 分钟再刷新重试，或尝试切换至 2.0 版本。")
            else:
                st.error(f"无法启动 AI: {e}")
            st.stop()

# ==========================================
# 4. 界面交互
# ==========================================
if not st.session_state.get("game_over", False):
    st.write(f"### 第 {st.session_state.question_count + 1} 问：")
    st.info(st.session_state.current_question)

    def handle_click(ans):
        st.session_state.question_count += 1
        with st.spinner("AI 正在深度思考..."):
            try:
                res = st.session_state.chat_session.send_message(ans)
                reply = res.text
                st.session_state.current_question = reply
                
                # --- 判定逻辑：兼容中英文问号 ---
                has_q = "?" in reply or "？" in reply
                # 判定结束：没有问号，或者包含特定的猜测词
                if not has_q or any(w in reply for w in ["猜", "名字是", "答案是"]):
                    st.session_state.game_over = True
            except Exception as e:
                st.error(f"请求失败: {e}")
        st.rerun()

    c1, c2, c3 = st.columns(3)
    with c1: st.button("✅ 是的", use_container_width=True, type="primary", on_click=handle_click, args=("是的",))
    with c2: st.button("❌ 不是", use_container_width=True, on_click=handle_click, args=("不是",))
    with c3: st.button("❔ 不确定", use_container_width=True, on_click=handle_click, args=("不确定",))

# 结算界面
else:
    st.balloons()
    st.success("🎯 **AI 锁定了答案！**")
    st.markdown(f"### {st.session_state.current_question}")
    if st.button("🎮 再玩一局", type="primary", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

import streamlit as st
import google.generativeai as genai

# ==========================================
# 1. 安全配置 (适配 Streamlit Cloud)
# ==========================================
if "GEMINI_API_KEY" not in st.secrets:
    st.error("❌ 未在 Secrets 中找到 GEMINI_API_KEY，请在 Streamlit 控制台配置。")
    st.stop()

# 自动清洗 Key 格式
API_KEY = "".join(st.secrets["GEMINI_API_KEY"].split())

try:
    genai.configure(api_key=API_KEY)
    # 切换为最稳定的 1.5 Flash 模型
    MODEL_NAME = 'gemini-1.5-flash'
    model = genai.GenerativeModel(MODEL_NAME)
except Exception as e:
    st.error(f"初始化失败: {e}")
    st.stop()

# ==========================================
# 2. 页面设置
# ==========================================
st.set_page_config(page_title="AI 读心神算子", page_icon="🕵️")
st.title("🕵️ AI 读心神算子：1.5 稳定版")

# ==========================================
# 3. 核心游戏状态初始化
# ==========================================
if "chat_session" not in st.session_state:
    st.session_state.chat_session = model.start_chat(history=[])
    st.session_state.game_over = False
    st.session_state.question_count = 0
    st.session_state.current_question = ""
    
    with st.spinner("🕵️ AI 正在构思线索..."):
        try:
            prompt = (
                "我们玩猜人物游戏。我心里想一个著名人物，你作为猜题者。 "
                "规则：1. 只能问‘是/否’类问题。 2. 一次一个问题。 "
                "3. 当你确定答案时，直接给出猜测。请开始第一问。"
            )
            response = st.session_state.chat_session.send_message(prompt)
            st.session_state.current_question = response.text
        except Exception as e:
            if "429" in str(e):
                st.error("⚠️ 访问频率过快，请等待 1 分钟后再刷新页面。")
            else:
                st.error(f"AI 启动失败: {e}")
            st.stop()

# ==========================================
# 4. 游戏互动区
# ==========================================

# 侧边栏状态
with st.sidebar:
    st.header("📊 战况")
    st.metric("已提问次数", st.session_state.question_count)
    if st.button("🔄 重新开始游戏", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

# 主界面逻辑
if not st.session_state.get("game_over", False):
    st.write(f"### 第 {st.session_state.question_count + 1} 问：")
    st.info(st.session_state.current_question)

    def handle_click(user_ans):
        st.session_state.question_count += 1
        with st.spinner("AI 正在深度思考..."):
            try:
                res = st.session_state.chat_session.send_message(user_ans)
                reply = res.text
                st.session_state.current_question = reply
                
                # --- 判定逻辑：兼容中英文问号 ---
                has_q = "?" in reply or "？" in reply
                # 判定结束：如果没有问号，或者回复中包含“猜测”类关键词
                if not has_q or any(w in reply for w in ["猜", "名字是", "答案是", "他是"]):
                    st.session_state.game_over = True
            except Exception as e:
                if "429" in str(e):
                    st.warning("⏰ 别点太快，AI 喘不过气了（频率限制）。请等几秒再点。")
                    st.session_state.question_count -= 1
                else:
                    st.error(f"请求失败: {e}")
        st.rerun()

    c1, c2, c3 = st.columns(3)
    with c1: st.button("✅ 是的", use_container_width=True, type="primary", on_click=handle_click, args=("是的",))
    with c2: st.button("❌ 不是", use_container_width=True, on_click=handle_click, args=("不是",))
    with c3: st.button("❔ 不确定", use_container_width=True, on_click=handle_click, args=("不确定",))

# 游戏结束展示
else:
    st.balloons()
    st.success("🎯 **AI 锁定了最终答案！**")
    st.markdown(f"### {st.session_state.current_question}")
    
    if st.button("🎮 再玩一局", type="primary", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

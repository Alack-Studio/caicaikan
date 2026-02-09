import streamlit as st
import google.generativeai as genai

# ==========================================
# 1. 安全配置与环境初始化
# ==========================================
if "GEMINI_API_KEY" not in st.secrets:
    st.error("❌ 未在 Secrets 中找到 GEMINI_API_KEY")
    st.stop()

API_KEY = "".join(st.secrets["GEMINI_API_KEY"].split())

try:
    # 强制指定不使用 v1beta，直接走稳定版 v1
    genai.configure(api_key=API_KEY)
    
    # 【核心修复】：尝试使用带 models/ 前缀的完整路径
    # 如果 1.5-flash 报错，我们会自动捕获并列出可用模型
    MODEL_NAME = 'models/gemini-1.5-flash' 
    model = genai.GenerativeModel(MODEL_NAME)
except Exception as e:
    st.error(f"初始化配置失败: {e}")
    st.stop()

# ==========================================
# 2. 页面设置
# ==========================================
st.set_page_config(page_title="AI 读心神算子", page_icon="🕵️")
st.title("🕵️ AI 读心神算子：1.5 稳定版")

# ==========================================
# 3. 核心游戏逻辑
# ==========================================
if "chat_session" not in st.session_state:
    with st.spinner("🕵️ AI 正在连接大脑..."):
        try:
            # 建立会话
            st.session_state.chat_session = model.start_chat(history=[])
            st.session_state.game_over = False
            st.session_state.question_count = 0
            
            prompt = (
                "我们玩猜人物游戏。我心里想一个著名人物，你作为猜题者。 "
                "规则：1. 只能问‘是/否’类问题。 2. 一次一个问题。 "
                "3. 当你确定答案时，直接给出名字。请开始你的第一问。"
            )
            response = st.session_state.chat_session.send_message(prompt)
            st.session_state.current_question = response.text
        except Exception as e:
            # 如果还是 404，这里会打印出你的 Key 实际支持的所有模型名称
            if "404" in str(e):
                st.error("❌ 模型路径错误 (404)。正在尝试自动诊断可用模型...")
                try:
                    available = [m.name for m in genai.list_models()]
                    st.write(f"你的 API Key 可用的模型清单：{available}")
                    st.info("请根据上面的列表，修改代码中的 MODEL_NAME。")
                except:
                    st.error("无法获取模型列表，请检查 API Key 是否有效。")
            elif "429" in str(e):
                st.warning("⚠️ 频率过高，请等 1 分钟再试。")
            else:
                st.error(f"AI 启动失败: {e}")
            st.stop()

# ==========================================
# 4. 界面交互
# ==========================================
if not st.session_state.get("game_over", False):
    st.write(f"### 第 {st.session_state.question_count + 1} 问：")
    st.info(st.session_state.current_question)

    def handle_click(ans):
        st.session_state.question_count += 1
        with st.spinner("AI 正在思考..."):
            try:
                res = st.session_state.chat_session.send_message(ans)
                reply = res.text
                st.session_state.current_question = reply
                
                # 判定逻辑：兼容中英文问号
                has_q = "?" in reply or "？" in reply
                if not has_q or any(w in reply for w in ["猜", "答案是", "名字是"]):
                    st.session_state.game_over = True
            except Exception as e:
                st.error(f"请求失败: {e}")
        st.rerun()

    c1, c2, c3 = st.columns(3)
    with c1: st.button("✅ 是的", use_container_width=True, type="primary", on_click=handle_click, args=("是的",))
    with c2: st.button("❌ 不是", use_container_width=True, on_click=handle_click, args=("不是",))
    with c3: st.button("❔ 不确定", use_container_width=True, on_click=handle_click, args=("不确定",))

else:
    st.balloons()
    st.success("🎯 AI 锁定了答案！")
    st.markdown(f"### {st.session_state.current_question}")
    if st.button("🎮 再来一局", type="primary", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

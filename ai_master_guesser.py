import streamlit as st
import google.generativeai as genai

# ==========================================
# 1. 安全配置与动态模型匹配
# ==========================================
if "GEMINI_API_KEY" not in st.secrets:
    st.error("❌ 未在 Secrets 中找到 GEMINI_API_KEY")
    st.stop()

API_KEY = "".join(st.secrets["GEMINI_API_KEY"].split())

@st.cache_resource
def init_ai_model():
    try:
        genai.configure(api_key=API_KEY)
        # 自动获取你列表中的模型
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 优先级排序：尝试从你的列表里选一个最稳的
        preference = [
            'models/gemini-2.0-flash', 
            'models/gemini-flash-latest',
            'models/gemini-2.5-flash',
            'models/gemini-pro-latest'
        ]
        
        target = None
        for p in preference:
            if p in available_models:
                target = p
                break
        
        if not target:
            target = available_models[0] # 如果都没中，就用第一个
            
        return genai.GenerativeModel(target), target
    except Exception as e:
        st.error(f"初始化诊断失败: {e}")
        return None, None

model, active_model_name = init_ai_model()

# ==========================================
# 2. 页面设置
# ==========================================
st.set_page_config(page_title="AI 读心神算子", page_icon="🕵️")
st.title("🕵️ AI 读心神算子")

with st.sidebar:
    st.success(f"当前驱动引擎：\n{active_model_name}")
    if st.button("🔄 强制重置游戏", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

# ==========================================
# 3. 游戏核心逻辑
# ==========================================
if "chat_session" not in st.session_state:
    with st.spinner("🕵️ AI 正在连接大脑..."):
        try:
            st.session_state.chat_session = model.start_chat(history=[])
            st.session_state.game_over = False
            st.session_state.question_count = 0
            
            prompt = (
                "我们玩猜人物游戏。我心里想一个著名人物，你问是非题。一次一个。 "
                "确定了直接猜。不要带问号。请开始第一问。"
            )
            response = st.session_state.chat_session.send_message(prompt)
            st.session_state.current_question = response.text
        except Exception as e:
            if "429" in str(e):
                st.error("⚠️ 配额已满 (429)。由于你使用的是高性能预览模型，请等待 60 秒后再刷新。")
            else:
                st.error(f"启动失败: {e}")
            st.stop()

# 游戏界面
if not st.session_state.get("game_over", False):
    st.write(f"### 第 {st.session_state.question_count + 1} 问：")
    st.info(st.session_state.current_question)

    def on_click(ans):
        st.session_state.question_count += 1
        with st.spinner("AI 正在思考..."):
            try:
                res = st.session_state.chat_session.send_message(ans)
                reply = res.text
                st.session_state.current_question = reply
                # 判定结束：无问号或包含猜测词
                if ("?" not in reply and "？" not in reply) or "猜" in reply:
                    st.session_state.game_over = True
            except Exception as e:
                st.error(f"思考中断: {e}")
        st.rerun()

    c1, c2, c3 = st.columns(3)
    with c1: st.button("✅ 是的", use_container_width=True, on_click=on_click, args=("是的",), type="primary")
    with c2: st.button("❌ 不是", use_container_width=True, on_click=on_click, args=("不是",))
    with c3: st.button("❔ 不确定", use_container_width=True, on_click=on_click, args=("不确定",))

else:
    st.balloons()
    st.success("🎯 AI 给出了答案！")
    st.markdown(f"### {st.session_state.current_question}")
    if st.button("🎮 再来一局", type="primary", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

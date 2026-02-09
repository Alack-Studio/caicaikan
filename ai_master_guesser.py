import streamlit as st
from google import genai  # 注意：这里改成了新的导入方式
from google.genai import types
import os

# ==========================================
# 1. 云端安全配置 (无需代理)
# ==========================================
if "GEMINI_API_KEY" not in st.secrets:
    st.error("请在 Streamlit 控制台设置 GEMINI_API_KEY")
    st.stop()

API_KEY = st.secrets["GEMINI_API_KEY"]

# 初始化新版客户端
client = genai.Client(api_key=API_KEY)
# 使用你之前诊断出的最强模型
MODEL_ID = "gemini-2.0-flash" 

# ==========================================
# 2. 页面设置
# ==========================================
st.set_page_config(page_title="AI 读心神算子", page_icon="🕵️")
st.title("🕵️ AI 读心神算子：2.0 时代版")

# ==========================================
# 3. 游戏逻辑
# ==========================================
if "chat_session" not in st.session_state:
    st.session_state.chat_session = client.chats.create(model=MODEL_ID)
    st.session_state.game_over = False
    st.session_state.question_count = 0
    
    with st.spinner("AI 正在构思线索..."):
        prompt = "我们玩猜人物游戏。我心里想一个著名人物，你问是非题。一次一个，确定了直接猜名字。请开始。"
        response = st.session_state.chat_session.send_message(prompt)
        st.session_state.current_question = response.text

# 界面展示
if not st.session_state.game_over:
    st.write(f"### 第 {st.session_state.question_count + 1} 问：")
    st.info(st.session_state.current_question)

    def on_click(ans):
        st.session_state.question_count += 1
        with st.spinner("AI 思考中..."):
            res = st.session_state.chat_session.send_message(ans)
            st.session_state.current_question = res.text
            # 判定是否结束
            if "?" not in res.text and "？" not in res.text or "猜" in res.text:
                st.session_state.game_over = True
        st.rerun()

    c1, c2, c3 = st.columns(3)
    with c1: st.button("✅ 是的", use_container_width=True, on_click=on_click, args=("是的",), type="primary")
    with c2: st.button("❌ 不是", use_container_width=True, on_click=on_click, args=("不是",))
    with c3: st.button("❔ 不确定", use_container_width=True, on_click=on_click, args=("不确定",))

else:
    st.balloons()
    st.success("🎯 AI 锁定了答案！")
    st.markdown(f"### {st.session_state.current_question}")
    if st.button("🎮 再来一局", type="primary"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

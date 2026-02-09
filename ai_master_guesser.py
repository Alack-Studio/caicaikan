import streamlit as st
from openai import OpenAI

# ==========================================
# 1. 页面配置与状态初始化
# ==========================================
st.set_page_config(page_title="AI 读心神算子", page_icon="🔮", layout="centered")

if "messages" not in st.session_state:
    st.session_state.messages = [] # 存储对话历史
if "game_over" not in st.session_state:
    st.session_state.game_over = False
if "question_count" not in st.session_state:
    st.session_state.question_count = 0

# ==========================================
# 2. WildCard API 配置
# ==========================================
if "API_KEY" not in st.secrets:
    st.error("🔑 请在 Streamlit Secrets 中配置 API_KEY")
    st.stop()

# WildCard 默认中转地址通常是 https://api.gptsapi.net/v1
client = OpenAI(
    api_key=st.secrets["API_KEY"],
    base_url="https://api.gptsapi.net/v1" 
)

# 使用 WildCard 支持的模型，建议用 gpt-4o-mini，速度极快且聪明
MODEL_NAME = "gpt-4o-mini"

# ==========================================
# 3. 核心交互函数
# ==========================================
def get_ai_response(user_input=None):
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
    
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "你是一个专业的读心神算子。我心里想一个著名人物，你只能问是非题（是/否/不确定）来猜他是谁。一次只问一个问题。当你确定答案时，请直接给出结果。"},
                *st.session_state.messages
            ],
            temperature=0.7
        )
        ai_reply = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": ai_reply})
        
        # 判定逻辑
        has_q = "?" in ai_reply or "？" in ai_reply
        if not has_q or any(w in ai_reply for w in ["猜到了", "答案是", "他是"]):
            st.session_state.game_over = True
            
    except Exception as e:
        st.error(f"❌ API 调用失败: {e}")

# ==========================================
# 4. 界面渲染
# ==========================================
st.title("🕵️ AI 读心神算子 (WildCard 版)")

# 侧边栏
with st.sidebar:
    st.write(f"当前进度：第 {st.session_state.question_count + 1} 步")
    if st.button("🔄 重新开始"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

# 首次启动
if not st.session_state.messages:
    with st.spinner("🔮 正在连接 WildCard 节点..."):
        get_ai_response()

# 游戏进行中
if not st.session_state.game_over:
    # 显示 AI 的最新提问
    last_ai_msg = [m for m in st.session_state.messages if m["role"] == "assistant"][-1]["content"]
    st.chat_message("assistant", avatar="🔮").write(last_ai_msg)
    
    st.divider()
    
    def on_click(ans):
        st.session_state.question_count += 1
        get_ai_response(ans)

    c1, c2, c3 = st.columns(3)
    with c1: st.button("✅ 是的", on_click=on_click, args=("是的",), use_container_width=True, type="primary")
    with c2: st.button("❌ 不是", on_click=on_click, args=("不是",), use_container_width=True)
    with c3: st.button("❔ 不确定", on_click=on_click, args=("不确定",), use_container_width=True)

# 游戏结束
else:
    st.balloons()
    final_reply = st.session_state.messages[-1]["content"]
    st.success("🎯 AI 已经给出了最终答案！")
    st.chat_message("assistant", avatar="🎯").write(final_reply)
    
    if st.button("🎮 挑战下一局", use_container_width=True, type="primary"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

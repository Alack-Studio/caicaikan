import streamlit as st
from openai import OpenAI

# ==========================================
# 1. 页面配置与精致样式
# ==========================================
st.set_page_config(page_title="顶级读心神算子", page_icon="🕵️", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    div.stButton > button {
        border-radius: 12px;
        height: 3.5em;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(118, 75, 162, 0.4); }
    .stChatMessage { border-radius: 15px; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 状态初始化
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "game_over" not in st.session_state:
    st.session_state.game_over = False
if "question_count" not in st.session_state:
    st.session_state.question_count = 0

# ==========================================
# 3. WildCard API 配置
# ==========================================
if "API_KEY" not in st.secrets:
    st.error("🔑 请在 Secrets 中配置 API_KEY")
    st.stop()

client = OpenAI(
    api_key=st.secrets["API_KEY"],
    base_url="https://api.gptsapi.net/v1" 
)

MODEL_NAME = "gpt-4o-mini"

# ==========================================
# 4. 深度博弈逻辑 (核心优化点)
# ==========================================
SYSTEM_PROMPT = """你现在是一位享誉全球的读心大师、顶级侦探。
你的目标：在 20 个是非题内猜出用户心中的著名人物（古今中外均可）。

你的提问策略：
1. **禁止机械排查**：不要只问“是男的吗？”这种低效率问题。
2. **分类突击**：通过职业、时代或影响力范围进行跳跃式提问。例如：“这位人物的作品是否改变了人类对宇宙或自然的认知？”
3. **侧写推演**：根据用户的回答，在脑中构建该人物的雏形。如果有强烈预感，可以尝试问一些针对性极强的问题（例如：“他是否常年穿着黑色高领毛衣？”）。
4. **揭晓时刻**：当你确定程度超过 85% 时，请停止提问，用极具戏剧性的语气揭晓答案。

提问规则：一次只问一个问题。语气要自信、神秘、略带挑衅。"""

def get_smart_response(user_input=None):
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
    
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                *st.session_state.messages
            ],
            temperature=0.8 # 提高随机性，让问题更具跳跃性
        )
        ai_reply = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": ai_reply})
        
        # 判定逻辑：更智能地识别答案揭晓
        # 如果回答中不包含问号，或者明确说出猜测，则结束
        if ("?" not in ai_reply and "？" not in ai_reply) or any(w in ai_reply for w in ["猜到了", "答案是", "他是", "你是想说"]):
            st.session_state.game_over = True
            
    except Exception as e:
        st.error(f"🔮 占卜球暂时的失去了光芒: {e}")

# ==========================================
# 5. 交互界面
# ==========================================
st.title("🕵️ 顶级读心神算子")
st.caption("基于 WildCard API 与 GPT-4o 引擎")

with st.sidebar:
    st.markdown("### 📊 挑战进度")
    st.write(f"已提问：**{st.session_state.question_count}** 次")
    if st.button("🔄 强制重置"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

# 首次启动
if not st.session_state.messages:
    with st.spinner("🔮 大师正在窥探你的思绪..."):
        get_smart_response()

if not st.session_state.game_over:
    # 找到 AI 的最后一个问题
    last_ai_msg = [m for m in st.session_state.messages if m["role"] == "assistant"][-1]["content"]
    
    with st.chat_message("assistant", avatar="🔮"):
        st.markdown(f"#### {last_ai_msg}")
    
    st.write("---")
    
    def on_click(ans):
        st.session_state.question_count += 1
        get_smart_response(ans)

    c1, c2, c3 = st.columns(3)
    with c1: st.button("✅ 是的", on_click=on_click, args=("是的",), use_container_width=True)
    with c2: st.button("❌ 不是", on_click=on_click, args=("不是",), use_container_width=True)
    with c3: st.button("❔ 不确定", on_click=on_click, args=("不确定",), use_container_width=True)

else:
    st.balloons()
    final_reply = st.session_state.messages[-1]["content"]
    st.success("🎯 大师已经看穿了一切！")
    with st.chat_message("assistant", avatar="🎯"):
        st.markdown(f"### {final_reply}")
    
    if st.button("🎮 再次挑战", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

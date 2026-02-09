import streamlit as st
from openai import OpenAI

# 1. 手机端适配：高对比度纯白 UI
st.set_page_config(page_title="AI 猜猜看", layout="centered")
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1F1F1F; }
    /* 手机端大按键优化 */
    div.stButton > button {
        border-radius: 12px; height: 4.8em; font-size: 1.1em;
        font-weight: bold; border: 1px solid #E0E0E0;
        background-color: #FFFFFF; color: #31333F; width: 100%;
        margin-bottom: 12px; transition: 0.2s;
    }
    div.stButton > button:active { transform: scale(0.96); background-color: #F8F9FA; }
    .stChatMessage { background-color: #FFFFFF; border: none; padding: 0px; }
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

st.title("🕵️ AI 猜猜看")

# 2. 状态初始化
ks = ["msgs", "over", "count"]
for k in ks:
    if k not in st.session_state: 
        st.session_state[k] = [] if k=="msgs" else (0 if k=="count" else False)

# 3. API 配置 (WildCard)
if "API_KEY" not in st.secrets:
    st.error("🔑 请配置 API_KEY"); st.stop()

client = OpenAI(api_key=st.secrets["API_KEY"], base_url="https://api.gptsapi.net/v1")
# 切换至旗舰级模型 GPT-4o
MODEL = "gpt-4o"

# 4. 核心逻辑 (旗舰级逻辑注入)
def ask_ai(inp=None):
    if inp: st.session_state.msgs.append({"role": "user", "content": inp})
    
    # 强化逻辑提示词：利用 4o 的推理深度
    sys = """你现在是全球顶尖的读心专家，拥有恐怖的逻辑推理和常识直觉。
    你的目标：用最少、最精准的提问识破用户心中的著名人物。
    
    战略要求：
    1. **禁止平庸**：严禁询问性别、国籍、是否健在等低级排查问题。
    2. **灵魂侧写**：从领域影响力、性格标签、标志性视觉符号、或历史转折点切入。
    3. **直觉博弈**：根据细微线索大胆假设。如果你怀疑是某人，直接询问该人特有的细节。
    
    一次一问带问号。确定答案后以'答案是：[人名]'开头。语气专业且自信。"""
    
    try:
        res = client.chat.completions.create(
            model=MODEL, 
            messages=[{"role":"system","content":sys}] + st.session_state.msgs, 
            temperature=0.8
        )
        reply = res.choices[0].message.content
        st.session_state.msgs.append({"role": "assistant", "content": reply})
        # 判定结束
        if st.

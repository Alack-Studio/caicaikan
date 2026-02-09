import streamlit as st
from openai import OpenAI
import random

# ==============================================================================
# 1. iOS Safari 专属配置与 UI (CSS)
# ==============================================================================
st.set_page_config(page_title="AI 猜猜看", layout="centered", initial_sidebar_state="collapsed")
st.markdown("<style>[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)

# iPhone 15 Pro OLED 纯黑方案
bg, txt, glow_c = "#000000", "#F2F2F7", "10, 132, 255"

st.markdown(f"""
    <style>
    /* iOS 全局字体与重置 */
    .stApp {{ 
        background-color: {bg}; 
        color: {txt} !important; 
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
        -webkit-font-smoothing: antialiased;
    }}
    
    /* 适配灵动岛与安全区域 */
    .block-container {{
        padding-top: max(1.2rem, env(safe-area-inset-top)) !important;
        padding-bottom: 10rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
    }}
    
    header {{ display: none !important; }}
    
    /* iOS 风格输入框 (磨砂玻璃) */
    .stChatInput {{
        position: fixed !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        padding-bottom: calc(12px + env(safe-area-inset-bottom)) !important;
        padding-top: 12px !important;
        background: rgba(20, 20, 20, 0.85) !important;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-top: 0.5px solid rgba(255,255,255,0.15);
        z-index: 999;
    }}
    
    .stChatInput textarea {{
        background-color: #1C1C1E !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 20px !important;
        padding: 10px 15px !important;
        font-size: 16px !important; 
    }}
    
    /* 聊天气泡文字高亮 */
    div[data-testid="stMarkdownContainer"] p {{
        color: #FFFFFF !important;
        font-size: 16px !important;
        line-height: 1.4 !important;
    }}
    
    .stChatMessage {{ 
        background-color: #1C1C1E !important; 
        border-radius: 18px !important; 
        padding: 12px 16px !important;
        border: none !important;
        margin-bottom: 8px !important;
    }}
    
    /* 按钮组适配 */
    div.stButton > button {{
        background-color: #2C2C2E !important;
        color: #0A84FF !important;
        border: none !important;
        border-radius: 12px !important;
        height: 44px !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        width: 100% !important;
        white-space: nowrap !important;
    }}
    
    div.stButton > button[kind="primary"] {{
        background-color: #0A84FF !important;
        color: #FFFFFF !important;
    }}
    
    .model-desc {{ font-size: 0.75rem; color: #8E8E93; text-align: center; margin-top: -5px; margin-bottom: 10px; }}

    /* 强制横排布局 */
    @media only screen and (max-width: 600px) {{
        [data-testid="stHorizontalBlock"] {{ gap: 6px !important; }}
        [data-testid="column"] {{ flex: 1 !important; min-width: 0 !important; }}
        div.stButton > button {{ font-size: 12px !important; padding: 0 !important; }}
    }}
    </style>
    """, unsafe_allow_html=True)

st.title("🕵️ AI 猜猜看")

# ==============================================================================
# 2. 状态管理
# ==============================================================================
default_states = {
    "msgs": [], "role": "AI 猜", "started": False, "over": False, 
    "win": False, "model": "gemini-2.5-flash-lite", "count": 0, 
    "pending": None, "seed_category": ""
}
for k, v in default_states.items():
    if k not in st.session_state: st.session_state[k] = v

# ==============================================================================
# 3. 核心逻辑引擎
# ==============================================================================
client = OpenAI(api_key=st.secrets["API_KEY"], base_url="https://api.gptsapi.net/v1")

def ask_ai(inp=None, hidden_trigger=False):
    if inp:
        st.session_state.msgs.append({"role": "user", "content": inp, "hidden": hidden_trigger})
        if not hidden_trigger: st.session_state.count += 1
    
    if st.session_state.role == "AI 猜":
        sys_prompt = "你是一个侦探。目标是猜出用户想的名人。第一句话直接问问题，严禁废话。确定答案回复：答案是：[人名]。"
    else:
        # 优化提示词：彻底解决“只发一个‘是’”的问题
        if not st.session_state.seed_category:
            st.session_state.seed_category = random.choice(["好莱坞明星", "动漫主角", "历史伟人", "超级英雄", "顶流歌手"])
        sys_prompt = (
            f"身份：金牌游戏主持人。你已选定：【{st.session_state.seed_category}】。\n"
            "【强制规则】当收到“请直接给我第一个提示。”时，你必须给出一个充满悬念的描述性句子，**绝对禁止回答‘是’或‘否’**。\n"
            "后续用户提问，你只答'是/否/模糊'。用户猜中回复：🎉 恭喜你，答对了！真相是：[人名]。"
        )

    with st.spinner("..."):
        try:
            api_msgs = [{"role": m["role"], "content": m["content"]} for m in st.session_state.msgs]
            res = client.chat.completions.create(model=st.session_state.model, messages=[{"role":"system","content":sys_prompt}] + api_msgs, temperature=0.7)
            reply = res.choices[0].message.content
            st.session_state.msgs.append({"role":"assistant", "content":reply})
            
            if any(k in reply for k in ["答案是", "恭喜", "真相是"]): st.session_state.over, st.session_state.win = True, True
            elif inp and "认输" in str(inp): st.session_state.over, st.session_state.win = True, False
        except Exception as e: st.error(f"Error: {str(e)}")

# 处理按钮点击
if st.session_state.pending:
    payload = st.session_state.pending; st.session_state.pending = None
    ask_ai(payload, hidden_trigger=(payload == "请直接给我第一个提示。")); st.rerun()

# ==============================================================================
# 4. 界面渲染 (还原经典文案)
# ==============================================================================
if not st.session_state.started:
    st.markdown("### 🎭 模式选择")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🤖 AI 猜 (它问我答)", use_container_width=True, type="primary" if st.session_state.role=="AI 猜" else "secondary"):
            st.session_state.role = "AI 猜"; st.rerun()
    with c2:
        if st.button("🕵️ 我猜 (我问它答)", use_container_width=True, type="primary" if st.session_state.role=="我猜" else "secondary"):
            st.session_state.role = "我猜"; st.rerun()
            
    st.markdown("### 🔮 挑战对象")
    models_info = {"gemini-2.5-flash-lite": "⚡ 极速响应", "gemini-2.5-pro": "🧠 逻辑专家", "gemini-3-pro-preview": "🔥 究极核心"}
    m_cols = st.columns(3)
    for i, (m_key, m_desc) in enumerate(models_info.items()):
        with m_cols[i]:
            if st.button(m_key.replace("gemini-",""), use_container_width=True, type="primary" if st.session_state.model == m_key else "secondary"):
                st.session_state.model = m_key; st.rerun()
            st.markdown(f'<p class="model-desc">{m_desc}</p>', unsafe_allow_html=True)
            
    st.write("---")
    if st.button("🚀 开始推理", use_container_width=True, type="primary"):
        st.session_state.started = True
        if st.session_state.role == "我猜": ask_ai("请直接给我第一个提示。", hidden_trigger=True)
        else: ask_ai()
        st.rerun()

else:
    for m in st.session_state.msgs:
        if m.get("hidden", False): continue 
        with st.chat_message(m["role"], avatar="🤖" if m["role"]=="assistant" else "👤"):
            st.markdown(m["content"])

    if not st.session_state.over:
        if st.session_state.role == "AI 猜":
            c1, c2, c3 = st.columns(3)
            if c1.button("✅ 是"): ask_ai("是"); st.rerun()
            if c2.button("❌ 否"): ask_ai("否"); st.rerun()
            if c3.button("❔ 模糊"): ask_ai("不确定"); st.rerun()
        else:
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                if st.button("💡 提示"): st.session_state.pending = "请给我新线索，别废话。"; st.rerun()
            with c2:
                if st.button("🙅 猜不到"): st.session_state.pending = "我认输，揭晓答案。"; st.rerun()
            with c3:
                if st.button("🔄 换个人"):
                    st.session_state.msgs, st.session_state.count, st.session_state.seed_category = [], 0, ""
                    if st.session_state.role == "我猜": st.session_state.pending = "请直接给我第一个提示。"
                    else: ask_ai()
                    st.rerun()
            with c4:
                if st.button("🏠 菜单"): st.session_state.started, st.session_state.msgs, st.session_state.over = False, [], False; st.rerun()
            user_input = st.chat_input("输入推理...")
            if user_input: ask_ai(user_input); st.rerun()
    else:
        if st.session_state.win: st.balloons(); st.success(f"🎯 胜利！耗时 {st.session_state.count} 轮")
        else: st.snow(); st.error("❄️ 推理结束")
        b1, b2 = st.columns(2)
        with b1:
            if st.button("🎮 换个人重新猜", use_container_width=True, type="primary"):
                st.session_state.msgs, st.session_state.over, st.session_state.win, st.session_state.count, st.session_state.seed_category = [], False, False, 0, ""
                if st.session_state.role == "我猜": ask_ai("请直接给我第一个提示。", hidden_trigger=True)
                else: ask_ai()
                st.rerun()
        with b2:
            if st.button("🏠 返回选关画面", use_container_width=True): st.session_state.started, st.session_state.msgs, st.session_state.over = False, [], False; st.rerun()

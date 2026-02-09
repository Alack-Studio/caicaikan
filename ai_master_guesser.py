import streamlit as st
from openai import OpenAI
import random

# ==============================================================================
# 1. 响应式 UI 架构：PC 与 iPhone 双端深度适配
# ==============================================================================
st.set_page_config(page_title="AI 猜猜看", layout="centered", initial_sidebar_state="collapsed")
st.markdown("<style>[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)

bg, txt, glow_c = "#000000", "#F2F2F7", "10, 132, 255"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg}; color: {txt} !important; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }}
    .block-container {{
        padding-top: max(1.2rem, env(safe-area-inset-top)) !important;
        padding-bottom: 11rem !important;
        max-width: 800px !important;
    }}
    header {{ display: none !important; }}
    
    /* 聊天气泡文字颜色加亮 */
    div[data-testid="stMarkdownContainer"] p {{ color: #FFFFFF !important; font-size: 16px !important; }}
    .stChatMessage {{ background-color: #1C1C1E !important; border-radius: 18px !important; margin-bottom: 8px !important; }}
    
    /* 输入框适配 */
    .stChatInput {{
        position: fixed !important;
        bottom: 0 !important;
        padding-bottom: calc(15px + env(safe-area-inset-bottom)) !important;
        background: rgba(10, 10, 10, 0.85) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        z-index: 999;
    }}

    /* 手机端按钮横排适配 */
    @media only screen and (max-width: 600px) {{
        [data-testid="stHorizontalBlock"] {{ flex-wrap: nowrap !important; gap: 5px !important; }}
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

def ask_ai(inp=None, is_hidden=False):
    if inp:
        # 将消息存入列表，并打上 hidden 标签
        st.session_state.msgs.append({"role": "user", "content": inp, "hidden": is_hidden})
        if not is_hidden: st.session_state.count += 1
    
    if st.session_state.role == "AI 猜":
        sys_prompt = "侦探身份。直接问第一个是非题，严禁废话。确定答案回复：答案是：[人名]。"
    else:
        if not st.session_state.seed_category:
            st.session_state.seed_category = random.choice(["好莱坞巨星", "动漫主角", "历史伟人", "超级英雄", "顶流歌手"])
        sys_prompt = (
            f"主持身份。目标：【{st.session_state.seed_category}】。\n"
            "指令：收到‘提示’或‘线索’词时，直接给具体描述，禁止回‘是/否’。猜中回复：🎉 恭喜你，答对了！真相是：[人名]。"
        )

    with st.spinner("..."):
        try:
            api_msgs = [{"role": m["role"], "content": m["content"]} for m in st.session_state.msgs]
            res = client.chat.completions.create(model=st.session_state.model, messages=[{"role":"system","content":sys_prompt}] + api_msgs, temperature=0.7)
            reply = res.choices[0].message.content
            st.session_state.msgs.append({"role":"assistant", "content":reply, "hidden": False})
            
            if any(k in reply for k in ["答案是", "恭喜", "真相是"]): st.session_state.over, st.session_state.win = True, True
            elif inp and "认输" in str(inp): st.session_state.over, st.session_state.win = True, False
        except Exception as e: st.error(f"Error: {str(e)}")

# 处理 Pending
if st.session_state.pending:
    payload = st.session_state.pending; st.session_state.pending = None
    # 点击提示或开局指令时，设置 is_hidden=True
    hide_it = "提示" in payload or "线索" in payload or "第一个提示" in payload
    ask_ai(payload, is_hidden=hide_it); st.rerun()

# ==============================================================================
# 4. 界面渲染
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
    models_info = {"gemini-2.5-flash-lite": "⚡ 极速响应", "gemini-2.5-pro": "🧠 专家模式", "gemini-3-pro-preview": "🔥 究极核心"}
    m_cols = st.columns(3)
    for i, (m_key, m_desc) in enumerate(models_info.items()):
        with m_cols[i]:
            if st.button(m_key.replace("gemini-",""), use_container_width=True, type="primary" if st.session_state.model == m_key else "secondary"):
                st.session_state.model = m_key; st.rerun()
            st.markdown(f'<p style="font-size:0.7rem; color:#8E8E93; text-align:center;">{m_desc}</p>', unsafe_allow_html=True)
            
    st.write("---")
    if st.button("🚀 开始推理", use_container_width=True, type="primary"):
        st.session_state.started = True
        if st.session_state.role == "我猜": ask_ai("请直接给我第一个提示。", is_hidden=True)
        else: ask_ai()
        st.rerun()

else:
    # --- 核心改进：渲染时检查 hidden 标记 ---
    for m in st.session_state.msgs:
        if m.get("hidden", False): continue  # 如果是隐藏消息，直接跳过不显示
        
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
                if st.button("💡 提示"): 
                    st.session_state.pending = "请给我新线索，别废话。"; st.rerun()
            with c2:
                if st.button("🙅 猜不到"): 
                    st.session_state.pending = "我认输，揭晓答案。"; st.rerun()
            with c3:
                if st.button("🔄 换个人"):
                    st.session_state.msgs, st.session_state.count, st.session_state.seed_category = [], 0, ""
                    if st.session_state.role == "我猜": st.session_state.pending = "请直接给我第一个提示。"
                    else: ask_ai()
                    st.rerun()
            with c4:
                if st.button("🏠 菜单"): 
                    st.session_state.started, st.session_state.msgs, st.session_state.over = False, [], False; st.rerun()
            
            user_input = st.chat_input("输入推理提问...")
            if user_input: ask_ai(user_input); st.rerun()
    else:
        if st.session_state.win: st.balloons(); st.success(f"🎯 成功！消耗 {st.session_state.count} 轮")
        else: st.snow(); st.error("❄️ 推理结束")
        b1, b2 = st.columns(2)
        with b1:
            if st.button("🎮 换个人重新猜", use_container_width=True, type="primary"):
                st.session_state.msgs, st.session_state.over, st.session_state.win, st.session_state.count, st.session_state.seed_category = [], False, False, 0, ""
                if st.session_state.role == "我猜": ask_ai("请直接给我第一个提示。", is_hidden=True)
                else: ask_ai()
                st.rerun()
        with b2:
            if st.button("🏠 返回选关画面", use_container_width=True): 
                st.session_state.started, st.session_state.msgs, st.session_state.over = False, [], False; st.rerun()

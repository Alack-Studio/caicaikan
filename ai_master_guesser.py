import streamlit as st
from openai import OpenAI
import random

# ==============================================================================
# 1. PC & iPhone 15 Pro 双端适配 UI
# ==============================================================================
st.set_page_config(page_title="AI 猜猜看", layout="centered", initial_sidebar_state="collapsed")
st.markdown("<style>[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)

bg, txt, glow_c = "#000000", "#F2F2F7", "10, 132, 255"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg} !important; color: {txt} !important; font-family: -apple-system, sans-serif; }}
    
    /* 适配灵动岛与底部 Home 条 */
    .block-container {{
        padding-top: max(1.2rem, env(safe-area-inset-top)) !important;
        padding-bottom: 11rem !important;
        max-width: 800px !important;
    }}
    header {{ display: none !important; }}
    
    /* 赛博蓝呼吸灯按钮 */
    div.stButton > button {{
        background-color: rgba(28, 28, 30, 0.8) !important;
        color: #00D2FF !important; border: 1px solid rgba(0, 210, 255, 0.3) !important;
        border-radius: 12px !important; height: 44px !important; font-weight: 600 !important;
    }}
    div.stButton > button[kind="primary"] {{
        background-color: rgba(0, 210, 255, 0.15) !important; border: 2px solid #00D2FF !important;
        box-shadow: 0 0 15px rgba(0, 210, 255, 0.4) !important; color: #FFFFFF !important;
    }}

    /* 修复文字看不清与输入框适配 */
    div[data-testid="stMarkdownContainer"] p {{ color: #FFFFFF !important; font-size: 16px !important; }}
    .stChatMessage {{ background-color: #1C1C1E !important; border-radius: 18px !important; border: 0.5px solid rgba(0, 210, 255, 0.2) !important; }}
    .stChatInput {{ 
        background: rgba(10, 10, 10, 0.85) !important; backdrop-filter: blur(20px) !important; 
        -webkit-backdrop-filter: blur(20px) !important; 
        padding-bottom: calc(15px + env(safe-area-inset-bottom)) !important;
    }}

    /* 手机端横排 4 按钮强制适配 */
    @media only screen and (max-width: 600px) {{
        [data-testid="stHorizontalBlock"] {{ flex-wrap: nowrap !important; gap: 5px !important; }}
        [data-testid="column"] {{ flex: 1 !important; min-width: 0 !important; }}
        div.stButton > button {{ font-size: 12px !important; padding: 0 !important; }}
    }}
    </style>
    """, unsafe_allow_html=True)

st.title("🕵️ AI 猜猜看")

# ==============================================================================
# 2. 状态初始化与逻辑引擎
# ==============================================================================
if "msgs" not in st.session_state:
    st.session_state.update({"msgs":[], "role":"AI 猜", "started":False, "over":False, "win":False, "model":"gemini-2.5-flash-lite", "count":0, "pending":None, "seed_category":""})

client = OpenAI(api_key=st.secrets["API_KEY"], base_url="https://api.gptsapi.net/v1")

def ask_ai(inp=None, is_hidden=False):
    if inp:
        st.session_state.msgs.append({"role": "user", "content": inp, "hidden": is_hidden})
        if not is_hidden: st.session_state.count += 1
    
    if st.session_state.role == "AI 猜":
        sys_prompt = "侦探身份。直接问第一个是非题，严禁废话。确定答案回复：答案是：[人名]。"
    else:
        # 加固指令：解决开局只答“是”的 Bug
        if not st.session_state.seed_category:
            st.session_state.seed_category = random.choice(["超级英雄", "好莱坞明星", "动漫主角", "历史伟人", "流行歌手"])
        sys_prompt = (
            f"主持身份。你已选定：【{st.session_state.seed_category}】。\n"
            "【逻辑锁定】若收到唤醒词'第一个提示'，必须给出具体描述，禁止只回'是/否'。\n"
            "后续用户提问，你只答'是/否/模糊'。猜中回复：🎉 恭喜你，答对了！真相是：[人名]。"
        )

    with st.spinner("..."):
        try:
            api_msgs = [{"role": m["role"], "content": m["content"]} for m in st.session_state.msgs]
            res = client.chat.completions.create(model=st.session_state.model, messages=[{"role":"system","content":sys_prompt}] + api_msgs, temperature=0.7)
            reply = res.choices[0].message.content
            st.session_state.msgs.append({"role":"assistant", "content":reply, "hidden": False})
            
            if any(k in reply for k in ["答案是", "恭喜", "真相是"]):
                st.session_state.over = True
                st.session_state.win = not (inp and "认输" in str(inp))
        except Exception as e: st.error(f"Error: {str(e)}")

# 处理按钮点击与隐藏对话框
if st.session_state.pending:
    payload = st.session_state.pending; st.session_state.pending = None
    hide_it = any(x in payload for x in ["提示", "线索", "第一个提示"])
    ask_ai(payload, is_hidden=hide_it); st.rerun()

# ==============================================================================
# 3. 界面渲染 (锁定经典文案)
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
        st.session_state.seed_category = "" 
        if st.session_state.role == "我猜": ask_ai("请直接给我第一个提示。", is_hidden=True)
        else: ask_ai()
        st.rerun()

else:
    for m in st.session_state.msgs:
        if not m.get("hidden", False):
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
                if st.button("💡 提示"): st.session_state.pending = "请给我新线索。"; st.rerun()
            with c2:
                if st.button("🙅 猜不到"): st.session_state.pending = "我认输，揭晓答案。"; st.rerun()
            with c3:
                if st.button("🔄 换个人"):
                    st.session_state.update({"msgs":[], "count":0, "seed_category":""})
                    if st.session_state.role == "我猜": st.session_state.pending = "请直接给我第一个提示。"
                    else: ask_ai()
                    st.rerun()
            with c4:
                if st.button("🏠 菜单"): st.session_state.update({"started":False, "msgs":[], "over":False}); st.rerun()
            user_input = st.chat_input("输入推理提问...")
            if user_input: ask_ai(user_input); st.rerun()
    else:
        if st.session_state.win: st.balloons(); st.success(f"🎯 成功！消耗 {st.session_state.count} 轮")
        else: st.snow(); st.error("❄️ 推理结束")
        b1, b2 = st.columns(2)
        with b1:
            if st.button("🎮 换个人重新猜", use_container_width=True, type="primary"):
                st.session_state.update({"msgs":[], "over":False, "win":False, "count":0, "seed_category":""})
                if st.session_state.role == "我猜": ask_ai("请直接给我第一个提示。", is_hidden=True)
                else: ask_ai()
                st.rerun()
        with b2:
            if st.button("🏠 返回选关画面", use_container_width=True): 
                st.session_state.update({"started":False, "msgs":[], "over":False}); st.rerun()

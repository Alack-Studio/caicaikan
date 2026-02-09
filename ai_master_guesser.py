import streamlit as st
from openai import OpenAI
import random

# ==============================================================================
# 1. iOS Safari 专属配置与 UI (CSS)
# ==============================================================================
st.set_page_config(page_title="赛博侦探", layout="centered", initial_sidebar_state="collapsed")
st.markdown("<style>[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)

# iPhone 15 Pro OLED 纯黑方案
bg, txt, glow_c = "#000000", "#F2F2F7", "10, 132, 255"

st.markdown(f"""
    <style>
    /* === iOS 全局字体与重置 === */
    .stApp {{ 
        background-color: {bg}; 
        color: {txt} !important; 
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        -webkit-font-smoothing: antialiased;
    }}
    
    /* === 1. 适配灵动岛与安全区域 === */
    .block-container {{
        padding-top: max(1rem, env(safe-area-inset-top)) !important;
        padding-bottom: 10rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
    }}
    
    header {{ display: none !important; }}
    
    /* === 2. iOS 风格输入框 (磨砂玻璃) === */
    .stChatInput {{
        position: fixed !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        padding-bottom: calc(10px + env(safe-area-inset-bottom)) !important;
        padding-top: 10px !important;
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
        border-radius: 18px !important;
        padding: 10px 15px !important;
        font-size: 16px !important; 
    }}
    
    /* === 3. 聊天气泡 (iMessage 风格) === */
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
    
    .stChatMessage .st-emotion-cache-1p1m4ay {{ width: 36px; height: 36px; }}
    
    /* === 4. 按钮组 (iOS Segmented Control 风格) === */
    div.stButton > button {{
        background-color: #2C2C2E !important;
        color: #0A84FF !important;
        border: none !important;
        border-radius: 12px !important;
        height: 44px !important;
        font-size: 14px !important; /* 稍微调小以容纳长文案 */
        font-weight: 600 !important;
        width: 100% !important;
        white-space: nowrap !important; /* 防止文字换行 */
        padding: 0 5px !important;
    }}
    
    div.stButton > button:active {{
        transform: scale(0.96);
        background-color: #3A3A3C !important;
    }}
    
    div.stButton > button[kind="primary"] {{
        background-color: #0A84FF !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 12px rgba(10, 132, 255, 0.4);
    }}
    
    .model-desc {{ font-size: 0.75rem; color: #8E8E93; text-align: center; margin-top: -5px; margin-bottom: 10px; }}

    /* === 5. 强制横排布局 (针对 iPhone) === */
    @media only screen and (max-width: 600px) {{
        [data-testid="stHorizontalBlock"] {{
            gap: 8px !important;
            padding: 0 2px;
        }}
        [data-testid="column"] {{
            flex: 1 !important;
            min-width: 0 !important;
        }}
        /* 针对底部4个功能键的特殊优化 */
        div.stButton > button {{
            padding: 0 !important;
            font-size: 13px !important; 
        }}
    }}
    </style>
    """, unsafe_allow_html=True)

st.title("🕵️ 赛博侦探")

# ==============================================================================
# 2. 状态管理
# ==============================================================================
default_states = {
    "msgs": [], 
    "role": "AI 猜",      
    "started": False,     
    "over": False,        
    "win": False,         
    "model": "gemini-2.5-flash-lite", 
    "count": 0,           
    "pending": None,      
    "seed_category": ""   
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
        if not hidden_trigger: 
            st.session_state.count += 1
    
    # Prompt 逻辑保持防泄露的高强度版本
    if st.session_state.role == "AI 猜":
        sys_prompt = (
            "指令：你是一个侦探。目标是猜出用户想的名人。\n"
            "1. 第一句话必须直接问问题（如：'是虚拟人物吗？'）。严禁开场白。\n"
            "2. 只能根据用户的'是/否'推理。\n"
            "3. 确定答案时，回复：'答案是：[人名]'。"
        )
    else:
        if not st.session_state.seed_category:
            categories = ["好莱坞巨星", "历史领袖", "知名动漫主角", "漫威/DC英雄", "流行歌手", "著名科学家"]
            st.session_state.seed_category = random.choice(categories)
            
        sys_prompt = (
            f"身份：金牌游戏主持人。目标：【{st.session_state.seed_category}】。\n"
            "1. 必须选**大众熟知**的角色。\n"
            "2. 开局提示要**画面感强**，严禁只回一个词，严禁说客套话。\n"
            "3. 用户提问只答：'是'、'否' 或 '模糊'。\n"
            "4. 用户点'提示'时，给新线索（外貌/成就），不复读。\n"
            "5. 用户猜中时，热情回复：'🎉 恭喜你，答对了！真相是：[人名]。'\n"
            "6. 用户认输时，回复：'很遗憾...其实是：[人名]。'"
        )

    with st.spinner("..."):
        try:
            api_msgs = [{"role": m["role"], "content": m["content"]} for m in st.session_state.msgs]
            res = client.chat.completions.create(
                model=st.session_state.model, 
                messages=[{"role":"system","content":sys_prompt}] + api_msgs, 
                temperature=0.7 
            )
            reply = res.choices[0].message.content
            st.session_state.msgs.append({"role":"assistant", "content":reply})
            
            user_surrender = inp and any(k in str(inp) for k in ["想不出来", "揭晓答案", "认输"])
            if user_surrender:
                st.session_state.over, st.session_state.win = True, False 
            elif st.session_state.role == "AI 猜":
                 if "答案是：" in reply: st.session_state.over, st.session_state.win = True, True
            elif any(x in reply for x in ["恭喜", "答对了", "正确", "真相是"]):
                st.session_state.over, st.session_state.win = True, True 

        except Exception as e:
            st.error(f"Error: {str(e)}")

# 处理按钮点击
if st.session_state.pending:
    payload = st.session_state.pending
    st.session_state.pending = None
    is_hidden = (payload == "请直接给我第一个提示。" or "我需要一个新的线索" in payload)
    ask_ai(payload, hidden_trigger=is_hidden)
    st.rerun()

# ==============================================================================
# 4. 界面渲染
# ==============================================================================

if not st.session_state.started:
    # 选关界面 - 文案还原
    st.markdown("### 🎭 模式选择")
    c1, c2 = st.columns(2)
    with c1:
        # 还原文案：AI 猜 (它问我答)
        if st.button("🤖 AI 猜 (它问我答)", use_container_width=True, type="primary" if st.session_state.role=="AI 猜" else "secondary"):
            st.session_state.role = "AI 猜"; st.rerun()
    with c2:
        # 还原文案：我猜 (我问它答)
        if st.button("🕵️ 我猜 (我问它答)", use_container_width=True, type="primary" if st.session_state.role=="我猜" else "secondary"):
            st.session_state.role = "我猜"; st.rerun()
            
    st.markdown("### 🔮 挑战对象") # 还原标题
    
    # 还原经典模型描述文案
    models_info = {
        "gemini-2.5-flash-lite": "⚡ 极速响应",
        "gemini-2.5-pro": "🧠 逻辑专家",
        "gemini-3-pro-preview": "🔥 究极核心"
    }
    
    m_cols = st.columns(3)
    for i, (m_key, m_desc) in enumerate(models_info.items()):
        with m_cols[i]:
            if st.button(m_key.replace("gemini-",""), use_container_width=True, type="primary" if st.session_state.model == m_key else "secondary"):
                st.session_state.model = m_key; st.rerun()
            st.markdown(f'<p class="model-desc">{m_desc}</p>', unsafe_allow_html=True)
            
    st.write("---")
    # 还原经典启动按钮
    if st.button("🚀 开始推理", use_container_width=True, type="primary"):
        st.session_state.started = True
        st.session_state.seed_category = "" 
        if st.session_state.role == "我猜": ask_ai("请直接给我第一个提示。", hidden_trigger=True)
        else: ask_ai() 
        st.rerun()

else:
    # 游戏界面
    for m in st.session_state.msgs:
        if m.get("hidden", False): continue 
        with st.chat_message(m["role"], avatar="🤖" if m["role"]=="assistant" else "👤"):
            st.markdown(m["content"])

    if not st.session_state.over:
        st.write("") 
        
        # 按钮区 - 强制横排
        if st.session_state.role == "AI 猜":
            c1, c2, c3 = st.columns(3)
            if c1.button("✅ 是"): ask_ai("是"); st.rerun()
            if c2.button("❌ 否"): ask_ai("否"); st.rerun()
            if c3.button("❔ 模糊"): ask_ai("不确定"); st.rerun()
        else:
            # 还原经典功能键文案
            c1, c2, c3, c4 = st.columns(4)
            
            with c1:
                if st.button("💡 提示"): 
                    st.session_state.pending = f"我需要线索（外貌/成就），别说废话。（第{st.session_state.count}次）"
                    st.rerun()
            with c2:
                if st.button("🙅 猜不到"): # 还原文案：猜不到
                    st.session_state.pending = "我认输，揭晓答案。"
                    st.rerun()
            with c3:
                if st.button("🔄 换个人"):
                    st.session_state.msgs, st.session_state.count, st.session_state.seed_category = [], 0, ""
                    if st.session_state.role == "我猜": st.session_state.pending = "请直接给我第一个提示。"
                    else: ask_ai()
                    st.rerun()
            with c4:
                if st.button("🏠 菜单"):
                    st.session_state.started, st.session_state.msgs, st.session_state.over = False, [], False
                    st.rerun()

            user_input = st.chat_input("输入推理...")
            if user_input: ask_ai(user_input); st.rerun()

    else:
        # 结算
        if st.session_state.win:
            st.balloons()
            st.success(f"🎯 胜利！耗时 {st.session_state.count} 轮")
        else:
            st.snow()
            st.error(f"❄️ 结束。耗时 {st.session_state.count} 轮")

        b1, b2 = st.columns(2)
        with b1:
            if st.button("🎮 换个人重新猜", use_container_width=True, type="primary"): # 还原文案
                st.session_state.msgs, st.session_state.over, st.session_state.win, st.session_state.count, st.session_state.seed_category = [], False, False, 0, ""
                if st.session_state.role == "我猜": ask_ai("请直接给我第一个提示。", hidden_trigger=True)
                else: ask_ai()
                st.rerun()
        with b2:
            if st.button("🏠 返回选关画面", use_container_width=True): # 还原文案
                st.session_state.started, st.session_state.msgs, st.session_state.over = False, [], False
                st.rerun()

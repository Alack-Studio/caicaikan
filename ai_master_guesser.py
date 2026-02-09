import streamlit as st
from openai import OpenAI
import random

# ==============================================================================
# 1. 核心配置与移动端重构 UI (CSS)
# ==============================================================================
st.set_page_config(page_title="赛博侦探", layout="centered")
st.markdown("<style>[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)

bg, txt, glow_c = "#121212", "#E0E0E0", "0, 210, 255"

st.markdown(f"""
    <style>
    /* === 全局基础样式 === */
    .stApp {{ background-color: {bg}; color: {txt} !important; font-family: -apple-system, sans-serif; }}
    
    /* 1. 聊天气泡文字高亮修复 */
    div[data-testid="stMarkdownContainer"] p {{
        color: #F0F0F0 !important; /* 强制亮白字 */
        line-height: 1.5 !important;
        font-size: 16px !important;
    }}
    
    /* 2. 输入框暗黑化重做 */
    .stChatInput {{
        bottom: 20px !important; /*稍微上移 */
    }}
    .stChatInput textarea {{
        background-color: #1E1E1E !important; /* 深灰背景 */
        color: #FFFFFF !important; /* 白字 */
        border: 1px solid rgba({glow_c}, 0.3) !important; /* 蓝光边框 */
        border-radius: 20px !important;
    }}
    .stChatInput ::placeholder {{ color: rgba(255,255,255,0.4) !important; }}
    
    /* 3. 按钮基础样式 */
    div.stButton > button {{
        background: rgba(255,255,255,0.05);
        color: {txt} !important;
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 8px;
        transition: 0.2s;
    }}
    
    /* 4. 选中/高亮按钮 */
    div.stButton > button[kind="primary"] {{
        background: rgba({glow_c}, 0.15) !important;
        border: 1px solid #00D2FF !important;
        color: #00D2FF !important;
        box-shadow: 0 0 10px rgba({glow_c}, 0.3);
    }}

    /* === 📱 移动端强制布局重做 (核心 Hack) === */
    @media only screen and (max-width: 600px) {{
        /* 隐藏顶部留白 */
        .block-container {{ padding-top: 1rem !important; padding-bottom: 5rem !important; }}
        header {{ display: none !important; }}
        
        /* 标题适配 */
        h1 {{ font-size: 1.5rem !important; text-align: center; margin-bottom: 0.5rem; }}
        
        /* === 核心：强制按钮横向排列 === */
        /* 强制 Streamlit 的水平块不换行 */
        [data-testid="stHorizontalBlock"] {{
            flex-wrap: nowrap !important;
            gap: 6px !important; /* 按钮间距 */
            overflow-x: auto !important; /* 防止溢出 */
        }}
        
        /* 强制每个列容器最小宽度为0，允许压缩 */
        [data-testid="column"] {{
            min-width: 0 !important;
            flex: 1 !important;
        }}
        
        /* 按钮样式微调 */
        div.stButton > button {{
            width: 100% !important;
            padding: 0px !important;
            height: 40px !important;
            font-size: 13px !important;
            white-space: nowrap !important; /* 文字不换行 */
            display: flex;
            align-items: center;
            justify_content: center;
        }}
        
        /* 聊天气泡紧凑化 */
        .stChatMessage {{ 
            padding: 10px !important; 
            margin-bottom: 5px !important;
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.05);
        }}
        
        /* 头像大小微调 */
        .stChatMessage .st-emotion-cache-1p1m4ay {{ width: 30px; height: 30px; }}
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
    
    # System Prompt
    if st.session_state.role == "AI 猜":
        sys_prompt = (
            "指令：你是一个玩'20个问题'游戏的侦探。目标是猜出用户想的名人。\n"
            "规则：\n"
            "1. 第一句话必须直接问第一个问题（如：'是虚拟人物吗？'）。严禁任何开场白。\n"
            "2. 只能根据用户的'是/否'进行推理。\n"
            "3. 确定答案时，回复：'答案是：[人名]'。"
        )
    else:
        # 我猜模式
        if not st.session_state.seed_category:
            categories = ["好莱坞巨星", "历史领袖", "知名动漫主角", "漫威/DC英雄", "流行歌手", "著名科学家"]
            st.session_state.seed_category = random.choice(categories)
            
        sys_prompt = (
            f"身份：金牌游戏主持人。目标：【{st.session_state.seed_category}】。\n"
            "规则：\n"
            "1. 必须选**大众熟知**的角色。\n"
            "2. 开局提示要**画面感强**，严禁只回一个词，严禁说客套话。\n"
            "3. 用户提问只答：'是'、'否' 或 '模糊'。\n"
            "4. 用户点'提示'时，给新线索（外貌/成就），不复读。\n"
            "5. 用户猜中时，热情回复：'🎉 恭喜你，答对了！真相是：[人名]。'"
        )

    with st.spinner("信号传输..."):
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
    st.markdown("### 🎭 选择模式")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🤖 AI 猜", use_container_width=True, type="primary" if st.session_state.role=="AI 猜" else "secondary"):
            st.session_state.role = "AI 猜"; st.rerun()
    with c2:
        if st.button("🕵️ 我猜", use_container_width=True, type="primary" if st.session_state.role=="我猜" else "secondary"):
            st.session_state.role = "我猜"; st.rerun()
            
    st.markdown("### 🧠 选择核心")
    models = ["gemini-2.5-flash-lite", "gemini-2.5-pro", "gemini-3-pro-preview"]
    names = ["⚡ 极速", "🧠 专家", "🔥 究极"]
    m_cols = st.columns(3)
    for i, m_key in enumerate(models):
        with m_cols[i]:
            if st.button(names[i], use_container_width=True, type="primary" if st.session_state.model == m_key else "secondary"):
                st.session_state.model = m_key; st.rerun()
            
    st.write("---")
    if st.button("🚀 开始游戏", use_container_width=True, type="primary"):
        st.session_state.started = True
        st.session_state.seed_category = "" 
        if st.session_state.role == "我猜": ask_ai("请直接给我第一个提示。", hidden_trigger=True)
        else: ask_ai() 
        st.rerun()

else:
    for m in st.session_state.msgs:
        if m.get("hidden", False): continue 
        with st.chat_message(m["role"], avatar="🤖" if m["role"]=="assistant" else "👤"):
            st.markdown(m["content"])

    if not st.session_state.over:
        st.write("") # Spacer
        
        # 核心修改点：强制横排布局
        # 在手机端 CSS 的加持下，这4列会被强制压缩在同一行
        if st.session_state.role == "AI 猜":
            c1, c2, c3 = st.columns(3)
            if c1.button("✅ 是"): ask_ai("是"); st.rerun()
            if c2.button("❌ 否"): ask_ai("否"); st.rerun()
            if c3.button("❔ 模糊"): ask_ai("不确定"); st.rerun()
        else:
            # 定义4个功能键
            c1, c2, c3, c4 = st.columns(4) # 平均分配空间
            
            with c1:
                if st.button("💡 提示"): 
                    st.session_state.pending = f"我需要线索（外貌/成就），别说废话。（第{st.session_state.count}次）"
                    st.rerun()
            with c2:
                if st.button("🙅 认输"): 
                    st.session_state.pending = "我认输，揭晓答案。"
                    st.rerun()
            with c3:
                if st.button("🔄 换人"):
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
        if st.session_state.win:
            st.balloons()
            st.success(f"🎯 胜利！耗时 {st.session_state.count} 轮")
        else:
            st.snow()
            st.error(f"❄️ 结束。耗时 {st.session_state.count} 轮")

        b1, b2 = st.columns(2)
        with b1:
            if st.button("🎮 再来一局", use_container_width=True, type="primary"):
                st.session_state.msgs, st.session_state.over, st.session_state.win, st.session_state.count, st.session_state.seed_category = [], False, False, 0, ""
                if st.session_state.role == "我猜": ask_ai("请直接给我第一个提示。", hidden_trigger=True)
                else: ask_ai()
                st.rerun()
        with b2:
            if st.button("🏠 回主页", use_container_width=True):
                st.session_state.started, st.session_state.msgs, st.session_state.over = False, [], False
                st.rerun()

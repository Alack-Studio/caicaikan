import streamlit as st
from openai import OpenAI
import random

# ==============================================================================
# 1. 核心配置与赛博 UI (CSS)
# ==============================================================================
st.set_page_config(page_title="赛博侦探", layout="centered")
st.markdown("<style>[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)

bg, txt, glow_c = "#121212", "#D1D1D1", "0, 210, 255"

st.markdown(f"""
    <style>
    @keyframes breathe {{
        0% {{ box-shadow: 0 0 4px rgba({glow_c}, 0.15); border-color: rgba({glow_c}, 0.3); }}
        50% {{ box-shadow: 0 0 12px rgba({glow_c}, 0.45); border-color: rgba({glow_c}, 0.6); }}
        100% {{ box-shadow: 0 0 4px rgba({glow_c}, 0.15); border-color: rgba({glow_c}, 0.3); }}
    }}

    .stApp {{ background-color: {bg}; color: {txt} !important; font-family: -apple-system, sans-serif; }}
    
    div.stButton > button {{
        border-radius: 12px; height: 3.2em; font-size: 0.95rem !important;
        background-color: transparent; color: {txt} !important;
        border: 1px solid rgba({glow_c}, 0.2); transition: 0.3s all;
    }}
    
    div.stButton > button[kind="primary"] {{
        background-color: rgba({glow_c}, 0.1) !important;
        border: 2px solid #00D2FF !important;
        box-shadow: 0 0 15px rgba({glow_c}, 0.6) !important;
        animation: breathe 2.5s infinite ease-in-out;
        color: #00D2FF !important; font-weight: bold;
    }}

    .stChatMessage {{ 
        background-color: rgba(255,255,255,0.03) !important; border-radius: 10px; padding: 12px; 
        border: 0.6px solid rgba({glow_c}, 0.3); margin-bottom: 10px; 
        animation: breathe 4s infinite ease-in-out;
    }}
    
    .model-desc {{ font-size: 0.8rem; color: {txt}; opacity: 0.6; text-align: center; margin-top: -8px; margin-bottom: 15px; }}
    header {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

st.title("🕵️ 赛博侦探事务所")

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
    
    # ---------------------------------------------------------
    # System Prompt 深度优化区
    # ---------------------------------------------------------
    if st.session_state.role == "AI 猜":
        sys_prompt = (
            "你是一个敏锐的侦探。目标是猜出用户想的一个名人。\n"
            "规则：\n"
            "1. 直接开始提问，不要废话。\n"
            "2. 只能问是非题。\n"
            "3. 确认答案时，必须回复：'答案是：[人名]'。"
        )
    else:
        # 我猜模式 (User Guesses)
        # 优化1：调整种子库，去除冷门，确保大众化
        if not st.session_state.seed_category:
            categories = [
                "全球知名的好莱坞电影主角", 
                "改变世界的历史领袖", 
                "家喻户晓的动漫主角", 
                "漫威/DC超级英雄", 
                "世界级流行歌手", 
                "教科书里的科学家",
                "中国古代著名诗人/将领"
            ]
            st.session_state.seed_category = random.choice(categories)
            
        sys_prompt = (
            f"身份：你是一位幽默且神秘的金牌游戏主持人。你已选定一个目标：【{st.session_state.seed_category}】。\n"
            "核心指令：\n"
            "1. 【选人标准】必须选择**全球知名度极高**或**中国家喻户晓**的人物。严禁选择冷门配角、生僻历史人物。目标必须是大众耳熟能详的。\n"
            "2. 【开局提示】当用户索要第一个提示时，用一句**富有画面感**的话描述他/她，制造悬念。例如：'他常年穿着红金战甲，在纽约上空飞行。'\n"
            "   - 严禁回复'好的'、'这是线索'、'没问题'等客套话。直接说线索！\n"
            "   - 严禁只蹦出一个词（如'电影'），必须是完整的句子。\n"
            "3. 【交互规则】用户提问，你只答：'是'、'否' 或 '模糊'。\n"
            "4. 【线索递进】当用户点'提示'时，提供之前没说过的特征（成就 -> 标志性外貌 -> 经典台词）。不要复述用户的指令。\n"
            "5. 【胜利判定】当用户猜中名字时，必须热情回复：'🎉 恭喜你，答对了！真相是：[人名]。' 并附带一句幽默的评价。\n"
            "6. 【认输】用户认输时，回复：'很遗憾，没能瞒住你太久...其实是：[人名]。' (不要说恭喜)。"
        )

    with st.spinner("正在检索全网数据..."):
        try:
            # 过滤掉 hidden 消息
            api_msgs = [{"role": m["role"], "content": m["content"]} for m in st.session_state.msgs]
            
            res = client.chat.completions.create(
                model=st.session_state.model, 
                messages=[{"role":"system","content":sys_prompt}] + api_msgs, 
                temperature=0.8 #稍微降低随机性，避免太偏
            )
            reply = res.choices[0].message.content
            st.session_state.msgs.append({"role":"assistant", "content":reply})
            
            # 结果判定
            user_surrender = inp and any(k in str(inp) for k in ["想不出来", "揭晓答案", "认输", "猜不到"])
            
            if user_surrender:
                st.session_state.over = True
                st.session_state.win = False 
            elif any(x in reply for x in ["恭喜", "答对了", "正确", "答案是", "真相是"]):
                st.session_state.over = True
                st.session_state.win = True 

        except Exception as e:
            st.error(f"📡 信号中断: {str(e)}")

# 处理 Pending 事件
if st.session_state.pending:
    payload = st.session_state.pending
    st.session_state.pending = None
    
    is_hidden = False
    if payload == "请直接给我第一个提示。":
        is_hidden = True
    elif "我需要一个新的线索" in payload:
        is_hidden = True
        
    ask_ai(payload, hidden_trigger=is_hidden)
    st.rerun()

# ==============================================================================
# 4. 路由与界面渲染
# ==============================================================================

# 场景一：选关画面
if not st.session_state.started:
    st.write("---")
    st.markdown("### 🎭 选择任务模式")
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🤖 AI 猜 (它问我答)", use_container_width=True, type="primary" if st.session_state.role=="AI 猜" else "secondary"):
            st.session_state.role = "AI 猜"
            st.rerun()
    with c2:
        if st.button("🕵️ 我猜 (我问它答)", use_container_width=True, type="primary" if st.session_state.role=="我猜" else "secondary"):
            st.session_state.role = "我猜"
            st.rerun()
            
    st.write("")
    st.markdown("### 🧠 接入逻辑核心")
    
    models_info = {
        "gemini-2.5-flash-lite": "⚡ 极速响应<br>适合快速连续对弈", 
        "gemini-2.5-pro": "🧠 逻辑专家<br>擅长复杂推理与陷阱", 
        "gemini-3-pro-preview": "🔥 究极算力<br>拥有顶级拟人直觉"
    }
    m_cols = st.columns(3)
    for idx, (m_key, m_desc) in enumerate(models_info.items()):
        with m_cols[idx]:
            if st.button(m_key.replace("gemini-",""), use_container_width=True, type="primary" if st.session_state.model == m_key else "secondary"):
                st.session_state.model = m_key
                st.rerun()
            st.markdown(f'<p class="model-desc">{m_desc}</p>', unsafe_allow_html=True)
            
    st.write("---")
    if st.button("⚡ 建立神经链接 (START)", use_container_width=True, type="primary"):
        st.session_state.started = True
        st.session_state.seed_category = "" 
        
        if st.session_state.role == "我猜":
            ask_ai("请直接给我第一个提示。", hidden_trigger=True)
        else:
            ask_ai() 
        st.rerun()

# 场景二：游戏进行中
else:
    # 渲染历史消息
    for m in st.session_state.msgs:
        if m.get("hidden", False): continue 
        
        avatar = "🤖" if m["role"] == "assistant" else "👤"
        if st.session_state.role == "AI 猜" and m["role"] == "assistant": avatar = "🕵️"
        
        with st.chat_message(m["role"], avatar=avatar):
            st.markdown(m["content"])

    if not st.session_state.over:
        st.write("") 
        
        if st.session_state.role == "AI 猜":
            col1, col2, col3 = st.columns(3)
            if col1.button("✅ 是", use_container_width=True): st.session_state.pending = "是的"; st.rerun()
            if col2.button("❌ 否", use_container_width=True): st.session_state.pending = "不是"; st.rerun()
            if col3.button("❔ 模糊", use_container_width=True): st.session_state.pending = "不确定"; st.rerun()
            
        else:
            c1, c2, c3, c4 = st.columns([0.18, 0.22, 0.22, 0.38])
            
            with c1:
                # 提示按钮
                if st.button("💡 提示"): 
                    st.session_state.pending = f"我需要一个新的线索（外貌/成就/秘密），请用自然的语言直接告诉我，不要复述我的请求。（第{st.session_state.count}次提问）"
                    st.rerun()
            with c2:
                if st.button("🙅 猜不到"): 
                    st.session_state.pending = "我想不出来了，请直接揭晓答案。"
                    st.rerun()
            with c3:
                if st.button("🔄 换个人"):
                    st.session_state.msgs = []
                    st.session_state.count = 0
                    st.session_state.seed_category = "" 
                    if st.session_state.role == "我猜":
                        st.session_state.pending = "请直接给我第一个提示。"
                    else:
                        ask_ai()
                    st.rerun()
            with c4:
                if st.button("🏠 菜单"):
                    st.session_state.started = False
                    st.session_state.msgs = []
                    st.session_state.over = False
                    st.rerun()

            user_input = st.chat_input("在此输入你的推理...")
            if user_input:
                ask_ai(user_input)
                st.rerun()

    else:
        if st.session_state.win:
            st.balloons()
            title_text = "🎯 推理成功！"
            color_style = "border:1px solid #00D2FF; background:rgba(0,210,255,0.05);"
        else:
            st.snow()
            title_text = "❄️ 推理结束"
            color_style = "border:1px solid #FF4B4B; background:rgba(255,75,75,0.05);"

        st.markdown(f"""
            <div style="text-align:center; padding:20px; border-radius:15px; margin:20px 0; {color_style}">
                <h2 style="margin:0;">{title_text}</h2>
                <p style="opacity:0.7; margin-top:10px;">本次耗时: {st.session_state.count} 轮交互</p>
            </div>
        """, unsafe_allow_html=True)

        b1, b2 = st.columns(2)
        with b1:
            if st.button("🎮 再来一局 (换人)", use_container_width=True, type="primary"):
                st.session_state.msgs = []
                st.session_state.over = False
                st.session_state.win = False
                st.session_state.count = 0
                st.session_state.seed_category = "" 
                
                if st.session_state.role == "我猜":
                    ask_ai("请直接给我第一个提示。", hidden_trigger=True)
                else:
                    ask_ai()
                st.rerun()
        with b2:
            if st.button("🏠 返回大厅", use_container_width=True):
                st.session_state.started = False
                st.session_state.msgs = []
                st.session_state.over = False
                st.rerun()

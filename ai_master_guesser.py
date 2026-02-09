import streamlit as st
from openai import OpenAI
import random

# ==============================================================================
# 1. 核心配置与赛博 UI (CSS)
# ==============================================================================
st.set_page_config(page_title="赛博侦探", layout="centered")
st.markdown("<style>[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)

# 赛博蓝光色系
bg, txt, glow_c = "#121212", "#D1D1D1", "0, 210, 255"

st.markdown(f"""
    <style>
    /* 呼吸灯动画 */
    @keyframes breathe {{
        0% {{ box-shadow: 0 0 4px rgba({glow_c}, 0.15); border-color: rgba({glow_c}, 0.3); }}
        50% {{ box-shadow: 0 0 12px rgba({glow_c}, 0.45); border-color: rgba({glow_c}, 0.6); }}
        100% {{ box-shadow: 0 0 4px rgba({glow_c}, 0.15); border-color: rgba({glow_c}, 0.3); }}
    }}

    .stApp {{ background-color: {bg}; color: {txt} !important; font-family: -apple-system, sans-serif; }}
    
    /* 按钮通用样式 */
    div.stButton > button {{
        border-radius: 12px; height: 3.2em; font-size: 0.95rem !important;
        background-color: transparent; color: {txt} !important;
        border: 1px solid rgba({glow_c}, 0.2); transition: 0.3s all;
    }}
    
    /* 选中/主要按钮高亮 */
    div.stButton > button[kind="primary"] {{
        background-color: rgba({glow_c}, 0.1) !important;
        border: 2px solid #00D2FF !important;
        box-shadow: 0 0 15px rgba({glow_c}, 0.6) !important;
        animation: breathe 2.5s infinite ease-in-out;
        color: #00D2FF !important; font-weight: bold;
    }}

    /* 对话气泡 */
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
# 2. 状态管理 (State Management)
# ==============================================================================
default_states = {
    "msgs": [], 
    "role": "AI 猜",      # 当前模式
    "started": False,     # 是否进入游戏画面
    "over": False,        # 游戏是否结束
    "win": False,         # 玩家(或AI)是否胜利
    "model": "gemini-2.5-flash-lite", 
    "count": 0,           # 轮数统计
    "pending": None,      # 按钮点击挂起操作
    "seed_category": ""   # 随机种子，防止AI选人重复
}

for k, v in default_states.items():
    if k not in st.session_state: st.session_state[k] = v

# ==============================================================================
# 3. 核心逻辑引擎 (The Brain)
# ==============================================================================
client = OpenAI(api_key=st.secrets["API_KEY"], base_url="https://api.gptsapi.net/v1")

def ask_ai(inp=None, hidden_trigger=False):
    """
    处理对话逻辑。
    inp: 用户输入内容 (或按钮触发的指令)
    hidden_trigger: 是否为隐藏指令（如开局提示，不显示在界面上）
    """
    # 1. 处理用户输入
    if inp:
        st.session_state.msgs.append({"role": "user", "content": inp, "hidden": hidden_trigger})
        if not hidden_trigger: 
            st.session_state.count += 1
    
    # 2. 动态生成 System Prompt (核心修复点)
    
    if st.session_state.role == "AI 猜":
        # AI 是侦探，用户是证人
        sys_prompt = (
            "你是一个敏锐的赛博侦探。你的目标是猜出用户心中想的一个著名人物。\n"
            "规则：\n"
            "1. 你必须通过问'是非题'来缩小范围。\n"
            "2. 请直接开始第一个问题，不要说'准备好了吗'之类的废话。\n"
            "3. 【强制结算】如果你问'是XXX吗？'且用户回答'是'，或者你已经确定了答案，"
            "你必须严格回复：'答案是：[人名]' 来宣告胜利。不要只说'哈哈我猜到了'。"
        )
    else:
        # AI 是出题者(Keeper)，用户是侦探
        # 随机种子注入：强制多样性
        if not st.session_state.seed_category:
            categories = ["冷门历史人物", "经典反派角色", "非人类角色(机器人/怪兽)", "古代思想家", "当代科技大亨", "体育传奇", "神话传说"]
            st.session_state.seed_category = random.choice(categories)
            
        sys_prompt = (
            f"身份：你是一台全知全能的超级计算机。你已锁定目标：【{st.session_state.seed_category}】。\n"
            "规则：\n"
            "1. 用户是侦探。你只答：'是'、'否' 或 '模糊'。\n"
            "2. 【反大众化】严禁连续选择爱因斯坦、马斯克等过于热门的角色。\n"
            "3. 【开局】收到'请直接给我第一个提示'时，给出一个充满神秘感的身世描述（如'他诞生于黑暗的哥谭'），严禁只给分类名。\n"
            "4. 【提示】收到'我需要新线索'时，必须提供之前未提及的新维度（从外貌->成就->秘密），严禁复读。\n"
            "5. 【最高优先级】当用户猜中名字（或极其接近）时，严禁只回'是'！你必须立即回复：'🎉 恭喜你，答对了！真相是：[人名]。'并附带简介。\n"
            "6. 【认输】用户认输时，回复：'很遗憾。真相是：[人名]。' (不要说恭喜)。"
        )

    with st.spinner("正在连接神经元网络..."):
        try:
            # 提高 temperature 以增加随机性和创造性
            res = client.chat.completions.create(
                model=st.session_state.model, 
                messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.msgs], # 过滤掉 hidden 标记
                temperature=0.9 
            )
            reply = res.choices[0].message.content
            st.session_state.msgs.append({"role":"assistant", "content":reply})
            
            # 3. 结果判定逻辑 (Regex-like check)
            
            # 情况A: 用户认输 (优先级最高)
            # 检查 inp 是否包含认输关键词
            user_surrender = inp and any(k in str(inp) for k in ["想不出来", "揭晓答案", "认输", "猜不到"])
            
            if user_surrender:
                st.session_state.over = True
                st.session_state.win = False # 强制判负
            
            # 情况B: AI 判定胜利
            elif any(x in reply for x in ["恭喜", "答对了", "正确", "答案是", "真相是"]):
                st.session_state.over = True
                # AI 猜模式下，AI 说出“答案是”即为游戏正常结束（AI赢了，也算一局完整游戏）
                # 我猜模式下，AI 说“恭喜”才是玩家赢
                st.session_state.win = True 

        except Exception as e:
            st.error(f"📡 信号中断: {str(e)}")

# 处理 Pending 按钮事件
if st.session_state.pending:
    payload = st.session_state.pending
    st.session_state.pending = None
    
    # 判断是否为隐藏指令
    is_hidden = False
    if payload == "请直接给我第一个提示。" or "我需要一个新的线索" in payload:
        is_hidden = True
        
    ask_ai(payload, hidden_trigger=is_hidden)
    st.rerun()

# ==============================================================================
# 4. 路由与界面渲染
# ==============================================================================

# 场景一：选关画面 (Start Screen)
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
        st.session_state.seed_category = "" # 重置种子
        
        # 自动触发开局
        if st.session_state.role == "我猜":
            ask_ai("请直接给我第一个提示。", hidden_trigger=True)
        else:
            ask_ai() 
        st.rerun()

# 场景二：游戏进行中 (Game Screen)
else:
    # 渲染历史消息 (过滤 hidden 消息)
    for m in st.session_state.msgs:
        if m.get("hidden", False): continue 
        
        avatar = "🤖" if m["role"] == "assistant" else "👤"
        if st.session_state.role == "AI 猜" and m["role"] == "assistant": avatar = "🕵️"
        
        with st.chat_message(m["role"], avatar=avatar):
            st.markdown(m["content"])

    # 游戏未结束时的操作区
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
                # 提示：使用隐藏指令，避免视觉污染
                if st.button("💡 提示"): 
                    st.session_state.pending = f"我需要一个关于【外貌/成就/秘密】的新线索，不要重复。（第{st.session_state.count}次提问）"
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

    # 游戏结束结算区
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

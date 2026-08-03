import streamlit as st
import os
from openai import OpenAI
import datetime
import json

from dotenv import load_dotenv
load_dotenv()

# 访问密码校验
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("AI智能伴侣 - 访问验证")
    input_pwd = st.text_input("请输入访问密码", type="password")
    # 密码从云端Secrets读取，本地调试可以临时写死测试
    correct_pwd = os.environ.get("APP_PASSWORD", "123456")
    if input_pwd == correct_pwd:
        st.session_state.auth = True
        st.rerun()
    st.stop()

# 创建与AI大模型交互的客户端对象(DEEPSEEK_API_KEY 环境变量的名字，值就是DeepSeek的API_KEY的)
client = OpenAI(
    api_key=os.environ.get('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com")

# 设置页面的配置项
st.set_page_config(
    page_title="AI智能伴侣",
    page_icon="🤗",
    # 布局
    layout="wide",
    # 控制的是侧边栏的状态
    initial_sidebar_state="expanded",
    menu_items={}
)

#生成会话标识函数
def generate_session_name():
    return datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# 初始化用户唯一ID（每个浏览器单独一套会话，互不干扰）
if "user_id" not in st.session_state:
    import secrets
    st.session_state.user_id = secrets.token_urlsafe(16)

# 保存会话信息函数
def save_session():
    if st.session_state.current_session:
        session_data = {
            "nick_name": st.session_state.nick_name,
            "nature": st.session_state.nature,
            "current_session": st.session_state.current_session,
            "messages": st.session_state.messages
        }
        # 按用户ID分文件夹隔离数据
        user_dir = os.path.join("sessions", st.session_state.user_id)
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
        save_path = os.path.join(user_dir, f"{st.session_state.current_session}.json")
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)

# 加载当前用户自己的会话列表
def load_sessions():
    session_list = []
    user_dir = os.path.join("sessions", st.session_state.user_id)
    if os.path.exists(user_dir):
        file_list = os.listdir(user_dir)
        for filename in file_list:
            if filename.endswith(".json"):
                session_list.append(filename[:-5])
    session_list.sort(reverse=True)
    return session_list

# 加载指定会话信息函数
def load_session(session_name):
    try:
        user_dir = os.path.join("sessions", st.session_state.user_id)
        load_path = os.path.join(user_dir, f"{session_name}.json")
        if os.path.exists(load_path):
            with open(load_path, "r", encoding="utf-8") as f:
                session_data = json.load(f)
                st.session_state.messages = session_data["messages"]
                st.session_state.nick_name = session_data["nick_name"]
                st.session_state.nature = session_data["nature"]
                st.session_state.current_session = session_name
    except Exception:
        st.error(f"加载会话时出错!")

# 删除指定会话信息函数
def delete_session(session_name):
    try:
        user_dir = os.path.join("sessions", st.session_state.user_id)
        del_path = os.path.join(user_dir, f"{session_name}.json")
        if os.path.exists(del_path):
            os.remove(del_path)
            if session_name == st.session_state.current_session:
                st.session_state.messages = []
                st.session_state.current_session = generate_session_name()
    except Exception:
        st.error(f"删除会话时出错!")

# 大标题
st.title("AI智能伴侣")

# Logo
st.logo("resources/logo.png")

# 系统提示词
system_prompt = """
        你叫%s，现在是用户的真实伴侣，请完全代入伴侣角色。：
        规则：
            1. 每次只回1条消息
            2. 禁止任何场景或状态描述性文字
            3. 匹配用户的语言
            4. 回复简短，像微信聊天一样
            5. 有需要的话可以用❤️🌸等emoji表情
            6. 用符合伴侣性格的方式对话
            7. 回复的内容, 要充分体现伴侣的性格特征
        伴侣性格：
            - %s
        你必须严格遵守上述规则来回复用户。
    """

# 初始化聊天信息
if "messages" not in st.session_state:
    st.session_state.messages = []
# 昵称
if "nick_name" not in st.session_state:
    st.session_state.nick_name = "小甜甜"
# 性格
if "nature" not in st.session_state:
    st.session_state.nature = "活泼开朗的东北姑娘"
#会话标识
if "current_session" not in st.session_state:
    st.session_state.current_session = generate_session_name()

# 展示聊天信息
st.subheader(f"会话名称: {st.session_state.current_session}")
for message in st.session_state.messages:
    st.chat_message(message["role"]).write(message["content"])
    # if message["role"] == "user":
    #     st.chat_message("user").write(message["content"])
    # else:
    #     st.chat_message("assistant").write(message["content"])

# 左侧侧边栏: with: streamlit 中上下文管理器
# st.sidebar.subheader("伴侣信息")
# nickname = st.sidebar.text_input("昵称")
with st.sidebar:
    st.subheader("AI控制面板")

    #新建会话按钮
    if st.button("新建会话", icon="➕", width="stretch"):
        # 1.保存当前会话数据
        save_session()

        # 2.创建新的会话
        if st.session_state.messages: # 如果聊天记录不为空,则清空聊天记录,并创建新的会话
            st.session_state.messages = []
            st.session_state.current_session = generate_session_name()
            save_session()
            st.rerun()  # 重新运行当前页面，刷新数据

    # 会话历史
    st.text("会话历史")
    session_list = load_sessions()
    for session in session_list:
        col1, col2 = st.columns([4,1])
        with col1:
            # 加载会话信息
            # 三元运算符：如果条件为真,则返回第一个值,否则返回第二个值 --> 值1 if 条件 else 值2
            if st.button(session, icon = "📄", width = "stretch", key = f"load_{session}", type = "primary" if session == st.session_state.current_session else "secondary"):
                load_session(session)
                st.rerun()  # 重新运行当前页面，刷新数据
        with col2:
            # 删除会话信息
            if st.button("", icon = "❌️", width = "stretch", key = f"delete_{session}"):
                delete_session(session)
                st.rerun()  # 重新运行当前页面，刷新数据

    # 分割线
    st.divider()

    # 昵称输入框
    nick_name = st.text_input("昵称", placeholder= "请输入伴侣的昵称", value= st.session_state.nick_name)
    if nick_name:
        st.session_state.nick_name = nick_name
    # 性格输入框
    nature = st.text_area("性格", placeholder= "请输入伴侣的性格", value= st.session_state.nature)
    if nature:
        st.session_state.nature = nature

# 消息输入框
prompt = st.chat_input("请输入您要问的问题")
if prompt: # 字符串会自动转换为Boolean值,如果字符串不为空,则为True,否则为False
    st.chat_message("user").write(prompt)
    print("-------> 调用AI大模型，提示词:", prompt)
    # 保存用户输入的提示词
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 与AI大模型进行交互
    response = client.chat.completions.create(
        model="deepseek-v4-pro",
        messages=[
            {"role": "system", "content": system_prompt % (st.session_state.nick_name, st.session_state.nature)},
            *st.session_state.messages
        ],
        stream=True,
        reasoning_effort="medium",
        extra_body={"thinking": {"type": "disabled"}}
    )

    # 输出大模型返回的结果(非流式输出的解析方式)
    # print("<------- 大模型返回的结果:", response.choices[0].message.content)
    # st.chat_message("assistant").write(response.choices[0].message.content)

    # 输出大模型返回的结果(流式输出的解析方式)
    response_message = st.empty() # 创建一个空的组件，用于展示大模型返回的结果

    full_response = ""
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            full_response += content
            response_message.chat_message("assistant").write(full_response)

    # 保存大模型返回的结果
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    # 保存当前会话数据
    save_session()


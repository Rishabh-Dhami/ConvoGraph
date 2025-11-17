import streamlit as st
from app import chat
from utils import new_thread_id, retrival_all_threads, load_chats

user_input = st.chat_input("Type here:")



if "history_chats" not in st.session_state:
    st.session_state.history_chats = []

if "thread_id" not in st.session_state:
    st.session_state.thread_id = new_thread_id()


for mssg in st.session_state.history_chats:
    with st.chat_message(mssg["role"]):
        st.write(mssg["content"])

CONFIG = {"configurable": {"thread_id" : st.session_state["thread_id"]}}

#sidebar
with st.sidebar:
    st.markdown(
        """
        <h1 style='color:#4CAF50; font-size:32px; 
        font-weight:900; margin-bottom:10px;'>Convo Graph</h1>
        """,
        unsafe_allow_html=True
    )
    st.markdown("### 💬 Chat History")    
    if st.button("## ➕ New Chat"):
        st.write("hello")

    list = retrival_all_threads()

    for tid in list:
        if st.button(tid):
            load_chats(tid)

# chat ui
if user_input:
    st.session_state.history_chats.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    response = chat.invoke({"messages": user_input}, config=CONFIG)

    st.session_state.history_chats.append({"role": "assistant", "content": response["messages"][-1].content})
    with st.chat_message("assistant"):
        st.write(response["messages"][-1].content)     

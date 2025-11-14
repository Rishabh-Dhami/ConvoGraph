import streamlit as st
from app import chat

user_input = st.chat_input("Type here:")

CONFIG = {"configurable": {"thread_id" : 1}}


if "history_chats" not in st.session_state:
    st.session_state.history_chats = []


for mssg in st.session_state.history_chats:
    with st.chat_message(mssg["role"]):
        st.write(mssg["content"])

# chat ui
if user_input:
    st.session_state.history_chats.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    response = chat.invoke({"messages": user_input}, config=CONFIG)

    st.session_state.history_chats.append({"role": "assistant", "content": response["messages"][-1].content})
    with st.chat_message("assistant"):
        st.write(response["messages"][-1].content)     

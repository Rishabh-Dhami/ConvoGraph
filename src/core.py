import streamlit as st
from app import chat
from utils import new_thread_id, retrival_all_threads, load_chats, generate_title, save_title, get_title


def switch_thread(thread_id):
    st.session_state.thread_id = thread_id
    st.session_state.history_chats = load_chats(thread_id=thread_id)
    st.rerun()


def start_new_chat():
    st.session_state.thread_id = new_thread_id()
    st.session_state.history_chats = []
    st.rerun()


if "history_chats" not in st.session_state:
    st.session_state.history_chats = []

if "thread_id" not in st.session_state:
    st.session_state.thread_id = new_thread_id()



for mssg in st.session_state.history_chats:
    with st.chat_message(mssg["role"]):
        st.write(mssg["content"])

CONFIG = {"configurable": {"thread_id": st.session_state["thread_id"]}}

# sidebar
with st.sidebar:
    st.markdown(
        """
        <h1 style='color:#4CAF50; font-size:32px; 
        font-weight:900; margin-bottom:10px;'>Convo Graph</h1>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("### 💬 Chat History")
    if st.button("## ➕ New Chat", use_container_width=True):
        start_new_chat()

    thread_list = retrival_all_threads()

    for tid in thread_list:
        if st.button(get_title(tid)[:30]+"....", key=f"btn-{tid}", use_container_width=True):
            switch_thread(thread_id=tid)


# chat ui
user_input = st.chat_input("Type here:")
if user_input:
    
    st.session_state.history_chats.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    
    with st.chat_message("assistant"):
        response = st.write_stream(
            chunk.content
            for chunk, meta in chat.stream(
                {"messages": user_input},
                config=CONFIG,
                stream_mode="messages",
            )
        )
        st.session_state.history_chats.append(
        {"role": "assistant", "content": response})


    # If this is the first chat in the thread, update sidebar
    if get_title(st.session_state.thread_id) == "New Chat":
        new_title = generate_title(user_input)
        save_title(st.session_state.thread_id, new_title)
        st.rerun()





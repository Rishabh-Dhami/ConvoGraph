import streamlit as st
from app import chat, ingest_pdf
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from utils import (
    new_thread_id,
    retrieve_all_threads,
    load_chats,
    generate_title,
    save_title,
    delete_all_chats,
    get_title,
    thread_document_metadata
)




def switch_thread(thread_id):
    # Switch the active thread in session state and reload its messages
    st.session_state.thread_id = thread_id
    st.session_state.history_chats = load_chats(thread_id=thread_id)
    st.session_state["ingested_docs"].setdefault(str(thread_id), {})
    st.rerun()

def add_thread(thread_id):
    if thread_id not in st.session_state["chat_threads"]:
        st.session_state["chat_threads"].append(thread_id)    


def start_new_chat():
    # Create a new thread id, clear current history, and refresh the UI
    st.session_state.thread_id = new_thread_id()
    st.session_state.history_chats = []
    st.rerun()


if "history_chats" not in st.session_state:
    st.session_state.history_chats = []

if "thread_id" not in st.session_state:
    st.session_state.thread_id = new_thread_id()

if "chat_threads" not in st.session_state:
    st.session_state["chat_threads"] = retrieve_all_threads()    

if "ingested_docs" not in st.session_state:
    st.session_state["ingested_docs"] = {}

for mssg in st.session_state.history_chats:
    with st.chat_message(mssg["role"]):
        st.write(mssg["content"])

CONFIG = {"configurable": {"thread_id": st.session_state["thread_id"]}}

add_thread(thread_id=st.session_state["thread_id"])

# sidebar
with st.sidebar:
    st.markdown(
        """
        <h1 style='color:#4CAF50; font-size:32px; 
        font-weight:900; margin-bottom:10px;'>Convo Graph</h1>
        """,
        unsafe_allow_html=True,
    )
    if st.button("## ➕ New Chat", use_container_width=True):
        start_new_chat()

    thread_key = st.session_state["thread_id"]    
    thread_list = st.session_state["chat_threads"][::-1]
    thread_docs = st.session_state["ingested_docs"].setdefault(thread_key, {})

    if thread_docs:
        latest_doc = list(thread_docs.values())[-1]
        st.success(
            f"Using `{latest_doc.get('filename')}` "
            f"({latest_doc.get('chunks')} chunks from {latest_doc.get('documents')} pages)"
        )
    else:
        st.info("No file indexed yet...")    
        

    uploaded_pdf = st.file_uploader("Upload a PDF for the chat", type=["pdf"])  
    if uploaded_pdf:
        if uploaded_pdf.name in thread_docs:
            st.info(f"`{uploaded_pdf.name}` already processed for this chat.")
        else:
            with st.sidebar.status("Indexing PDF…", expanded=True) as status_box:
                summary = ingest_pdf(
                    uploaded_pdf.getvalue(),
                    thread_id=thread_key,
                    filename=uploaded_pdf.name,
                    )
                thread_docs[uploaded_pdf.name] = summary
                status_box.update(label="✅ PDF indexed", state="complete", expanded=False)

    st.subheader("### 💬 Chat History")            
    if not thread_list:
        st.write("No past conversations yet.")
    else:                
        for tid in thread_list:
            if st.button(
            get_title(tid)[:30] + "....", key=f"btn-{tid}", use_container_width=True
            ):
                switch_thread(thread_id=tid)


# chat ui
user_input = st.chat_input("Type here:")
if user_input:

    st.session_state.history_chats.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        status_holder = {"box": None}

        def ai_only_stream():
            for message_chunk, _ in chat.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode="messages",
            ):
                if isinstance(message_chunk, ToolMessage):
                    tool_name = getattr(message_chunk, "name", "tool")
                    if status_holder["box"] is None:
                        status_holder["box"] = st.status(
                            f"🔧 Using `{tool_name}` …", expanded=True
                        )
                    else:
                        status_holder["box"].update(
                            label=f"🔧 Using `{tool_name}` …",
                            state="running",
                            expanded=True,
                        )

                if isinstance(message_chunk, AIMessage):
                    yield message_chunk.content

        ai_message = st.write_stream(ai_only_stream())

        if status_holder["box"] is not None:
            status_holder["box"].update(
                label="✅ Tool finished", state="complete", expanded=False
            )
        st.session_state.history_chats.append(
            {"role": "assistant", "content": ai_message}
        )

        doc_meta = thread_document_metadata(thread_key)
        if doc_meta:
            st.caption(
            f"Document indexed: {doc_meta.get('filename')} "
            f"(chunks: {doc_meta.get('chunks')}, pages: {doc_meta.get('documents')})"
        )

    # If this is the first chat in the thread, update sidebar
    if get_title(st.session_state.thread_id) == "New Chat":
        new_title = generate_title(user_input)
        save_title(st.session_state.thread_id, new_title)
        st.rerun()

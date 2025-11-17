import uuid
from app import checkpointer, chat
from langchain_core.messages import HumanMessage

def new_thread_id():
    return str(uuid.uuid4())


def retrival_all_threads():
    threads = []
    for thread  in checkpointer.list(None):
        threads.append(thread.config["configurable"]["thread_id"])
    return list(dict.fromkeys(threads))    

retrival_all_threads()

def load_chats(thread_id):
    result = chat.get_state(config={"configurable": {"thread_id": thread_id}})
    if result and "messages" in result.values:
        msgs = result.values["messages"]
        return [{"role": "user" if isinstance(m, HumanMessage) else "assistant", "content": m.content} for m in msgs]
    return []
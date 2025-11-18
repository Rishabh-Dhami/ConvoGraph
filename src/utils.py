import uuid
from app import checkpointer, chat, llm
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from prompts import title_generator_system_prompt


def new_thread_id() -> str:
    return str(uuid.uuid4())


def retrival_all_threads() -> list:
    threads = []
    for thread  in checkpointer.list(None):
        threads.append(thread.config["configurable"]["thread_id"])
    return list(dict.fromkeys(threads))    


def load_chats(thread_id) -> list:
    result = chat.get_state(config={"configurable": {"thread_id": thread_id}})
    if result and "messages" in result.values:
        msgs = result.values["messages"]
        return [{"role": "user" if isinstance(m, HumanMessage) else "assistant", "content": m.content} for m in msgs]
    return []

def generate_title(input) -> str:
    prompt = ChatPromptTemplate.from_messages([
        ("system", title_generator_system_prompt),
        ("user", "{input}")
    ])

    chain = prompt | llm | StrOutputParser()
    res = chain.invoke({"input": input})
    return res



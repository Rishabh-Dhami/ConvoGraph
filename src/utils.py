import uuid
from app import (
    checkpointer,
    chat,
    llm,
    cursor,
    conn,
    _THREAD_METADATA,
    _THREAD_RETRIEVERS,
)
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from prompts import title_generator_system_prompt


def new_thread_id() -> str:
    # Return a new UUID string to use as a thread identifier
    return str(uuid.uuid4())


def retrieve_all_threads() -> list:
    # Return a list of unique thread IDs available in the checkpointer
    all_threads = set()
    for thread in checkpointer.list(None):
        all_threads.add(thread.config["configurable"]["thread_id"])
    return list(all_threads)


def load_chats(thread_id) -> list:
    # Load chat messages for the provided thread_id from the compiled chat state
    result = chat.get_state(config={"configurable": {"thread_id": thread_id}})
    if result and "messages" in result.values:
        msgs = result.values["messages"]
        return [
            {
                "role": "user" if isinstance(m, HumanMessage) else "assistant",
                "content": m.content,
            }
            for m in msgs
        ]
    return []


def thread_has_document(thread_id: str) -> bool:
    return str(thread_id) in _THREAD_RETRIEVERS


def thread_document_metadata(thread_id: str) -> dict:
    return _THREAD_METADATA.get(str(thread_id), {})


def generate_title(input) -> str:
    # Generate a short, descriptive title for the given input using the LLM
    prompt = ChatPromptTemplate.from_messages(
        [("system", title_generator_system_prompt), ("user", "{input}")]
    )

    chain = prompt | llm | StrOutputParser()
    res = chain.invoke({"input": input})
    return res


def save_title(thread_id, title):
    # Save or update a thread title in the local SQLite chat_titles table
    cursor.execute(
        """
        INSERT OR REPLACE INTO chat_titles (thread_id, title)
        VALUES (?, ?)
    """,
        (thread_id, title),
    )
    conn.commit()


def get_title(thread_id):
    # Retrieve a stored title for a thread id or return the default "New Chat"
    cursor.execute("SELECT title FROM chat_titles WHERE thread_id = ?", (thread_id,))
    row = cursor.fetchone()
    return row[0] if row else "New Chat"


def delete_all_chats():
    """
    Delete all chat history from the database.
    """

    try:
        cursor = conn.cursor()

        cursor.execute("DELETE FROM checkpoints")
        cursor.execute("DELETE FROM chat_titles")

        conn.commit()

        # Clear memory caches
        _THREAD_RETRIEVERS.clear()
        _THREAD_METADATA.clear()

        return {"status": "success", "message": "All chats deleted"}

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
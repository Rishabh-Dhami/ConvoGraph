import uuid
from app import checkpointer, chat, llm, cursor, conn
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from prompts import title_generator_system_prompt


def new_thread_id() -> str:
    # Return a new UUID string to use as a thread identifier
    return str(uuid.uuid4())


def retrival_all_threads() -> list:
    # Return a list of unique thread IDs available in the checkpointer
    threads = []
    for thread in checkpointer.list(None):
        threads.append(thread.config["configurable"]["thread_id"])
    return list(dict.fromkeys(threads))


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


def delete_all_threads() -> dict:
    # Delete all threads from the checkpointer and remove titles from the local DB
    threads = retrival_all_threads()
    removed = 0

    # Try to delete from the checkpointer if it exposes a delete/remove API
    for tid in threads:
        try:
            # common method names that checkpointers might implement
            if hasattr(checkpointer, "delete"):
                checkpointer.delete(tid)
                removed += 1
                continue
            if hasattr(checkpointer, "remove"):
                checkpointer.remove(tid)
                removed += 1
                continue
            if hasattr(checkpointer, "clear"):
                # some implementations accept a key or config
                try:
                    checkpointer.clear(tid)
                    removed += 1
                    continue
                except Exception:
                    pass
        except Exception as e:
            print(f"Warning: failed to remove thread {tid} from checkpointer: {e}")

    # Remove titles from the local SQLite table
    try:
        cursor.execute("DELETE FROM chat_titles")
        conn.commit()
    except Exception as e:
        print(f"Warning: failed to clear chat_titles table: {e}")

    return {"threads_found": len(threads), "threads_removed_via_checkpointer": removed}


delete_all_threads()
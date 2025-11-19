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



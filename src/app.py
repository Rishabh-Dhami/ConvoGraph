from langchain_core.messages import  BaseMessage
from langgraph.graph import StateGraph, START, END
from langchain_core.runnables import RunnableConfig
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
import requests
from typing import TypedDict, Annotated, Dict, Optional, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.tools import tool
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.prebuilt import ToolNode, tools_condition
import sqlite3
import tempfile
from langchain_community.vectorstores import FAISS
from pathlib import Path
from langchain_community.tools import DuckDuckGoSearchRun
import os

from prompts import chat_prompt

load_dotenv()


llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

_THREAD_RETRIEVERS: Dict[str, Any] = {}
_THREAD_METADATA: Dict[str, dict] = {}

embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def _get_retriever(thread_id: Optional[str]):
    """Fetch the retriever for a thread if available."""
    if thread_id and str(thread_id) in _THREAD_RETRIEVERS:
        return _THREAD_RETRIEVERS[str(thread_id)]
    return None


def ingest_pdf(file_bytes: bytes, thread_id: str, filename: Optional[str] = None) -> dict:
    """
        Process an uploaded PDF and create a FAISS-based retriever for it.
        The PDF is loaded, split into smaller text chunks, converted into vector
        embeddings, and stored in a FAISS vector store. A retriever is then created
        and associated with the given thread so the chat system can search the
        document during conversations.
        
        Returns a summary dictionary containing basic information about the
        processed file (such as filename, number of pages, and number of chunks)
        that can be displayed in the UI.
    """   

    if not file_bytes:
        raise ValueError("No bytes received for ingestion.")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(file_bytes)
        temp_path = temp_file.name

    try:
        loader = PyPDFLoader(temp_path)
        docs = loader.load()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200,  separators=["\n\n", "\n", " ", ""]
        )

        chunks = splitter.split_documents(docs)

        vector_store = FAISS.from_documents(chunks, embedding=embedding_model)

        retriever = vector_store.as_retriever(
            search_type="similarity", search_kwargs={"k": 4}
        )

        _THREAD_RETRIEVERS[str(thread_id)] = retriever
        _THREAD_METADATA[str(thread_id)] = {
            "filename" : filename or os.path.basename(temp_path),
            "documents" : len(docs),
            "chunks" : len(chunks)
        }

        return {
            "filename" : filename or os.path.basename(temp_path),
            "documents" : len(docs),
            "chunks" : len(chunks)
        }
    finally:
        # The FAISS store keeps copies of the text, so the temp file is safe to remove.
        try:
            os.remove(temp_path)
        except OSError:
            pass

@tool
def rag_tool(query: str, config: RunnableConfig):
    """
    Retrieve relevant information from the PDF associated with a chat thread.

    This tool searches the document index created for the provided `thread_id`
    and returns the most relevant text chunks related to the user's query.

    Args:
        thread_id: Unique identifier of the chat thread.
        query: User question used to search the indexed document.

    Returns:
        A dictionary containing the query, retrieved context chunks,
        metadata, and source file information.

    Raises:
        ValueError: If thread_id is missing or no document is indexed.
    """

    thread_id = config["configurable"].get("thread_id")

    if not thread_id:
        return {
            "error" : "thread id is required to retriever documents context",
            "query" : query
        }

    retriever = _THREAD_RETRIEVERS.get(str(thread_id))

    if retriever is None:
        return {
            "error": "No document indexed for this chat. Upload a PDF first.",
            "query": query,
        }

    try:
        result = retriever.invoke(query)

        context = []
        metadata = []

        for doc in result:
            context.append(doc.page_content)
            metadata.append(doc.metadata if doc.metadata else {})

        return {
            "query" : query,
            "context": context,

        }    
    except Exception as e:
        return {
            "error": "Failed to retrieve document context.",
            "details": str(e),
            "query": query,
        }


search_tool = DuckDuckGoSearchRun(region="us-en")


@tool
def get_stock_price(symbol: str) -> dict:
    """
    Fetch latest stock price for a given symbol (e.g. 'AAPL', 'TSLA')
    using Alpha Vantage with API key in the URL.
    """
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={os.getenv('ALPHAVANTAGE_API_KEY')}"
    r = requests.get(url)
    return r.json()


tools = [search_tool, get_stock_price, rag_tool]

llm_with_tools = llm.bind_tools(tools)


def chat_assistant(state: ChatState) -> dict:
    # Build the chat prompt from state and invoke the LLM assistant node
    prompt = ChatPromptTemplate.from_messages(
        [("system", chat_prompt),
        ("placeholder", "{messages}")
    ])

    chat_chain = prompt | llm_with_tools

    result = chat_chain.invoke({"messages": state["messages"]})

    return {"messages": [result]}


tool_node = ToolNode(tools)

def tool_node_fn(state: ChatState, config=None):
    return tool_node.invoke(state, config=config)

graph = StateGraph(ChatState)

graph.add_node("chat_assistant", chat_assistant)
graph.add_node("tools", tool_node_fn)

graph.add_edge(START, "chat_assistant")
graph.add_conditional_edges("chat_assistant", tools_condition)
graph.add_edge("tools", "chat_assistant")


db_dir = Path(__file__).resolve().parent / "database"
db_dir.mkdir(parents=True, exist_ok=True)
db_path = db_dir / "convo_graph.db"

conn = sqlite3.connect(str(db_path), check_same_thread=False)

checkpointer = SqliteSaver(conn=conn)


# Create titles table
cursor = conn.cursor()
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS chat_titles (
    thread_id TEXT PRIMARY KEY,
    title TEXT
)
"""
)
conn.commit()

chat = graph.compile(checkpointer=checkpointer)


from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from typing import TypedDict, Annotated
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.memory import InMemorySaver
import sqlite3

from prompts import chat_prompt

load_dotenv()


llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0
)

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def chat_assistant(state: ChatState) -> dict:
    prompt = ChatPromptTemplate.from_messages({
        ("system", chat_prompt),
        ("user", "{messages}")
    })

    chat_chain = prompt | llm

    result = chat_chain.invoke({"messages" : state["messages"]})

    return {"messages" : [result]}



graph = StateGraph(ChatState)

graph.add_node("chat_assistant", chat_assistant)

graph.add_edge(START, "chat_assistant")
graph.add_edge("chat_assistant", END)

# conn = sqlite3.connect("database/convo_graph.db", check_same_thread=False)

checkpointer = InMemorySaver()

chat = graph.compile(checkpointer=checkpointer)




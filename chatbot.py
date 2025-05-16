from pydantic import BaseModel
from typing import Optional, List
import langgraph
import re
import ast
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda
# from langchain_core.pydantic_v1 import BaseModel, Field
from pydantic import BaseModel,Field
from langchain.utilities import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM
from langchain_community.chat_models import ChatOllama
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
import pandas as pd
import json
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema import AIMessage, HumanMessage
from states.agent_state import AgentState
from config import llm
from nodes.generate_sql_query import generate_sql_node
from nodes.run_query import run_query_and_handle_error_node
from nodes.respond_to_user import respond_to_user
from nodes.analyze_query import analyze_query_node
from nodes.analyze_schema import analyze_schema_node

#  Use `add_conditional_edges()` Instead of `condition
def check_success(state: AgentState) -> str:
    """Validates the SQL query using sql_db_query_checker before execution."""
    if not state.query_result:
        print(f"Error Encountered: {state.error}")
        if state.loop_count >= 5:
            return "respond"  # Stop execution once limit is reached
        return "analyze_query"
    else:  
        return "respond"
    

# Build Graph
graph = StateGraph(AgentState)
graph.add_node("analyze_query", analyze_query_node)
graph.add_node("analyze_schema", analyze_schema_node)
graph.add_node("generate_sql", generate_sql_node)
graph.add_node("run_query_and_handle_error", run_query_and_handle_error_node)
graph.add_node("respond", respond_to_user)



graph.add_edge(START, "analyze_query")
graph.add_edge("analyze_query","analyze_schema")
graph.add_edge("analyze_schema","generate_sql")
graph.add_edge("generate_sql", "run_query_and_handle_error")
graph.add_conditional_edges(
    "run_query_and_handle_error",
    check_success,
    {
        "analyze_query": "analyze_query",
        "respond": "respond"
    }
)

graph.add_edge("respond", END)

# Compile Graph
custom_sql_agent = graph.compile()

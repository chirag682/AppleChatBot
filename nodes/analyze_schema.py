from langchain_neo4j import GraphCypherQAChain
from prompt_templates import get_analyze_query_prompt, get_cypher_generation_prompt, get_qa_prompt
from states.agent_state import AgentState
from config import llm, graph
import re
from init_db import schema

def analyze_schema_node(state: AgentState):
    cypher_prompt = get_cypher_generation_prompt()
    qa_prompt = get_qa_prompt()
    print(cypher_prompt)
    graph_rag_chain = GraphCypherQAChain.from_llm(
        cypher_llm=llm,
        qa_llm=llm,
        validate_cypher=True,
        graph=graph,
        verbose=True,
        return_intermediate_steps=True,
        return_direct=True,
        cypher_prompt=cypher_prompt,
        qa_prompt = qa_prompt,
        allow_dangerous_requests=True
    )
    
    schema_info = graph_rag_chain.invoke(state.cypher_details)
    print(schema_info)
    print("==================")
    print(schema_info['result'])
    
    return AgentState(
        user_query=state.user_query,
        db_query=state.db_query,
        general_query=state.general_query,
        schema_info = schema_info['result'],
        sql_query=None,
        error=None,
        loop_count=state.loop_count
    )
    
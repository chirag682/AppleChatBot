from langchain_neo4j import GraphCypherQAChain
from prompt_templates import get_analyze_query_prompt, get_cypher_generation_prompt, get_qa_prompt
from states.agent_state import AgentState
from config import llm, graph
from utils.format_final_response import format_schema_to_string

def analyze_schema_node(state: AgentState):
    cypher_prompt = get_cypher_generation_prompt()
    qa_prompt = get_qa_prompt()
    graph_rag_chain = GraphCypherQAChain.from_llm(
        cypher_llm=llm,
        qa_llm=llm,
        validate_cypher=True,
        graph=graph,
        verbose=True,
        return_intermediate_steps=True,
        return_direct = True,
        cypher_prompt=cypher_prompt,
        qa_prompt = qa_prompt,
        allow_dangerous_requests=True
    )
    
    
    try:
        schema_info = graph_rag_chain.invoke({"query": state.cypher_details})
        result_str = format_schema_to_string(schema_info['result'])
        # result_str = llm.invoke(qa_prompt.format(context=schema_info['result']))
        print(result_str)
        return AgentState(
            user_query=state.user_query,
            db_query=state.db_query,
            general_query=state.general_query,
            schema_info=result_str,
            sql_query=None,
            error=None,
            loop_count=state.loop_count
        )
    
    except Exception as e:
        # Optionally include more detailed logs or traceback
        error_msg = f"Cypher query generation failed: {str(e)}"
        print(error_msg)  # Log detailed traceback
        return AgentState(
            user_query=state.user_query,
            db_query=state.db_query,
            general_query=state.general_query,
            schema_info = state.db_query,
            sql_query=None,
            error=None,
            loop_count=state.loop_count
        )
    
from utils.format_final_response import apply_general_processing_with_llm
from utils.generate_report_url import generate_report_url
from states.agent_state import AgentState
from langchain_core.messages import AIMessage
from config import llm

def respond_to_user(state: AgentState):
    if state.error:
        return AgentState(
            user_query=state.user_query,
            final_response=[AIMessage(content=f"Could not execute query. Error: {state.error}")]
        )

    if not state.query_result:
        return AgentState(
            user_query=state.user_query,
            final_response=[AIMessage(content="No results found in the database.")]
        )

    # processed_result = apply_general_processing_with_llm(state)
    # processed_link = generate_report_url(state, llm)

    return AgentState(
        user_query=state.user_query,
        # final_response=AIMessage(content=f"Query executed successfully \n\n*Processed Results:* {processed_result}\n\n*Link to Report:* {processed_link}")
        final_response=AIMessage(content=f"Query executed successfully \n\n*Processed Results:* {state.query_result}")
    )

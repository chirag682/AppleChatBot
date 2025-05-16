from utils.format_final_response import apply_general_processing_with_llm
from utils.generate_report_url import generate_report_url
from states.agent_state import AgentState
from langchain_core.messages import AIMessage
from config import llm
from utils.render_table import render_query_result_table
from utils.generate_report import generate_pdf_report

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

    fig =  render_query_result_table(state.query_result)
    processed_result = apply_general_processing_with_llm(state)
    pdf_bytes = generate_pdf_report(state.user_query, processed_result, fig)
    # processed_link = generate_report_url(state, llm)

    return AgentState(
        user_query=state.user_query,
        # final_response=AIMessage(content=f"Query executed successfully \n\n*Processed Results:* {processed_result}\n\n*Link to Report:* {processed_link}")
        final_response=AIMessage(content=f"Query executed successfully \n\n*Processed Results:* {processed_result}"),
        pdf_bytes =pdf_bytes
    )

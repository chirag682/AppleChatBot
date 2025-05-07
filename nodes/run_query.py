from utils.run_sql_query import run_sql_query
from states.agent_state import AgentState

def run_query_and_handle_error_node(state: AgentState):
    result = run_sql_query(state.sql_query)
    if isinstance(result, str) and "Error" in result:
        return AgentState(
            user_query=state.user_query,
            db_query=state.db_query,
            general_query=state.general_query,
            sql_query=state.sql_query,
            error=result,
            loop_count=state.loop_count + 1
        )

    return AgentState(
        user_query=state.user_query,
        db_query=state.db_query,
        general_query=state.general_query,
        sql_query=state.sql_query,
        query_result=result,
        loop_count=state.loop_count
    )

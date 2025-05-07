from pydantic import BaseModel,Field
from typing import Optional, List
from langchain_core.messages import AIMessage, HumanMessage

# Define the AgentState class
class AgentState(BaseModel):
    user_query: str
    general_query: Optional[str] = None
    db_query: Optional[str] = None
    sql_query: Optional[str] = None
    query_result: Optional[List[dict]] = None
    error: Optional[str] = None
    final_response: Optional[AIMessage | HumanMessage] = None
    loop_count: Optional[int] = 0
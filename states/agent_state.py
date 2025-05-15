from pydantic import BaseModel,Field
from typing import Optional, List, Any
from langchain_core.messages import AIMessage, HumanMessage

# Define the AgentState class
class AgentState(BaseModel):
    user_query: str
    cypher_details: Optional[str] = None
    general_query: Optional[str] = None
    db_query: Optional[str] = None
    schema_info: Optional[str] = None
    sql_query: Optional[str] = None
    query_result: Optional[List[dict]] = None
    error: Optional[str] = None
    final_response: Optional[AIMessage | HumanMessage] = None
    loop_count: Optional[int] = 0
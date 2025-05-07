from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage
from pydantic import BaseModel
import re
from prompt_templates import get_analyze_query_prompt
from states.agent_state import AgentState
from config import llm

def analyze_query_node(state: AgentState):
    prompt_template = get_analyze_query_prompt(state)
    response = llm.invoke(prompt_template.format(input=state.user_query))
    response_text = response.content.strip()

    query_match = re.search(r"Query_Details:\s*(.+?)(?=\n[A-Za-z_]*Details:|$)", response_text, re.DOTALL | re.IGNORECASE)
    action_match = re.search(r"Action_Details:\s*(.+?)(?=\n[A-Za-z_]*Details:|$)", response_text, re.DOTALL | re.IGNORECASE)

    query_details = query_match.group(1).strip() if query_match else "Fetch relevant data"
    action_details = action_match.group(1).strip() if action_match else "Got it"

    return AgentState(
        user_query=state.user_query,
        db_query=query_details,
        general_query=action_details,
        sql_query=None,
        error=None,
        loop_count=state.loop_count
    )
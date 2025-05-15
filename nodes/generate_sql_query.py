from states.agent_state import AgentState
from config import llm, vectorstores
import re
from utils.schema_utils import fetch_table_names, format_schema_info, format_relations_info
from prompt_templates import get_sql_generation_prompt
from utils.schema_utils import prepare_schema_data
from FAQ import sample_queries


def generate_sql_node(state: AgentState):
    chroma_results = vectorstores.max_marginal_relevance_search(state.user_query,  k=10, fetch_k=20)  # Returns (Document, distance)
    # # Extract only user query texts from ChromaDB results
    retrieved_queries = [doc.page_content for doc in chroma_results]

    # Dictionary for quick lookup of SQL queries
    query_mapping = {item["question"]: item["answer"] for item in sample_queries}

    # Find matching SQL queries
    matched_sql_queries = [
        f" User Query: {user_query}\n   → SQL: {query_mapping.get(user_query, 'No SQL Query Found')}"
        for user_query in retrieved_queries
    ]

    # Format for prompt
    chroma_text = "\n".join(matched_sql_queries)

    """Use LLM to generate an SQL query based on user input."""
    prompt_template = get_sql_generation_prompt()
     
    prompt = prompt_template.invoke({
        "chroma_results":chroma_text,
        "schema_info":state.schema_info,
        "db_query":state.db_query,
        "input": state.user_query,
    })

    sql_query = llm.invoke(prompt).content.strip()
    print("-------------------------------")
    print(sql_query)
    print('-------------------------------')
    match = re.search(r"```sql\s*\n?(.*?)\n?```", sql_query, re.DOTALL | re.IGNORECASE)
    if match:
        return AgentState(user_query=state.user_query,db_query = state.db_query, general_query=state.general_query, sql_query=match.group(1).strip(),loop_count= state.loop_count)  # Extract and clean query
    return AgentState(user_query=state.user_query,db_query = state.db_query, general_query=state.general_query, sql_query=None,loop_count= state.loop_count)

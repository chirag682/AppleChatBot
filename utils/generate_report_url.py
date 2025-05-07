from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from prompt_templates import get_report_url_prompt

def generate_report_url(state, llm):
    """
    Uses the LLM to analyze the user query and generate a report URL.
    """

    # Define prompt template
    prompt_template = get_report_url_prompt()
    # Format the prompt with user input
    prompt = prompt_template.format(input=state.user_query, query=state.sql_query)
    response = llm.invoke(prompt)
    # Return the response content
    return response.content.strip()

# # Example Usage:
# user_query = "Show me all annotations associated with hierarrchy 'finance' and 'ACARE' ?"
# llm_response = generate_report_url(user_query, gemma_llm)
# print("Generated Report URL:", llm_response)

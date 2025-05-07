import re
import json
import pandas as pd
from langchain_core.prompts import ChatPromptTemplate
from config import llm

def apply_general_processing_with_llm(state):
    """
    Uses LLM to process query results based on the general_query instructions.
    This allows LLM to handle summarization, ranking, comparisons, etc.
    """

    # Convert query result into structured JSON format for LLM
    formatted_data = json.dumps(state.query_result, indent=2)

    df = pd.DataFrame(json.loads(formatted_data))
    parsed_data=df.to_csv()

    action_query=state.general_query
    # If no additional processing is required, return the raw results
    if state.general_query.lower() == "no additional processing required.":
        action_query=state.user_query

    # Construct LLM Prompt
    system_message = (
        "** Intelligent Data Processing Assistant**\n\n"
        "You are an **expert at transforming structured data** into human-readable insights.\n\n"

        "### ** Data Provided:**\n"
        f"User Question: {state.user_query}\n"
        f"User's detailed question: {action_query}\n"
        f"SQL Query: {state.sql_query}\n"
        f"Data: {parsed_data}\n"
        "**Task:**\n"
        "- You will receive a dataset returned from an SQL query. The data will be presented in a structured format such as a table or JSON object."
        # "- Your job is to analyze the data and provide a clear, natural-language summary that explains the key insights."
        "- Your job is to analyze the data and provide a clear and concise answer according to the provided **User Question** and with all **Data**"
        "- if **User Question** or **User's detailed question** asks for summary only then summarize the **Data** other wise provide a clear and concise answer"
        "- Ensure the explanation is easy to understand, even for someone without technical expertise."
        "**Instructions:**\n"
        "- Provide a clear, concise answer based on the data.\n"
        "- Base your answer strictly on the provided data and do not make any assumptions about data not present in the results.\n"
        "- Focus on natural language, using the SQL context as needed.\n"
        "**Additional Guidelines:**\n"
        "- Keep the response concise but informative."
        "- If the data includes monetary values, use appropriate formatting (e.g., '$' for USD)."
        "- If the data includes dates, present them in a natural format (e.g., 'January 1, 2025')."
        "- If the data shows growth or decline, mention it explicitly and provide possible reasons if applicable."
        "- If different users contains same annotations treat them as different. don't combine them"
        "- If a user asks for an annotation summary,then provide the explanation of provided content from the annotation table. The user may also request additional details about the annotations, which is specified in the user query (such as specific hierarchy, time range, or other relevant filters)."
        "**Important**\n"
        "- If any part of the data is unclear or incomplete, mention it but do not guess."
        "- If the data is inconsistent or contains errors, point them out respectfully."
    )
    # Construct LLM prompt
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_message)
    ])

    # Invoke LLM for processing
    response = llm.invoke(prompt_template.format())
    processed_result = response.content.strip()

    # Extract structured output using regex
    processed_match = re.search(r"Processed Output:\s*(.+)", processed_result, re.DOTALL | re.IGNORECASE)
    final_output = processed_match.group(1).strip() if processed_match else processed_result

    return final_output
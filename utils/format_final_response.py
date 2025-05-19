import re
import json
import pandas as pd
from langchain_core.prompts import ChatPromptTemplate
from config import llm
from utils.decimal_encoder import DecimalEncoder

def apply_general_processing_with_llm(state):
    """
    Uses LLM to process query results based on the general_query instructions.
    This allows LLM to handle summarization, ranking, comparisons, etc.
    """
    query_result = state.query_result
    action_query=state.general_query
    user_query=state.user_query
    # Convert query result into structured JSON format for LLM
    formatted_data = json.dumps({'query_result':  query_result}, indent=2, cls=DecimalEncoder)

    df = pd.DataFrame(json.loads(formatted_data))
    parsed_data=df.to_csv()
    parsed_data_safe = parsed_data.replace('{', '{{').replace('}', '}}')
  
    
    # If no additional processing is required, return the raw results
    if action_query.lower() == "no additional processing required.":
        action_query=query_result

    # Construct LLM Prompt
    system_message = (
        """
         You are a data analyst assistant and expert at transforming structured SQL query outputs into clear, actionable, and decision-ready insights.

        You will be provided with:

            SQL return data in tabular (JSON or CSV) format
            A user’s primary and detailed question

        Your responsibilities:

            Understand the data
                Interpret column meanings and data types
                Identify the intent behind the user’s question (summarize it in ≤15 words)

            Analyze the dataset
                Detect any date/time columns, and derive relevant period labels (week, month, quarter, year)
                Calculate time-based comparisons where possible (WoW, MoM, QoQ, YoY)
                Identify top and bottom performers for key metrics
                Detect anomalies (values > ±2σ from the mean or changes ≥50%)
                If annotations exist, explain their meaning in the context of the data (e.g., hierarchy, filters)

            Generate clear, human-friendly insights

                Use plain English suitable for non-technical stakeholders
                Address the exact user question — tailor the explanation accordingly
                Include tables, bullets, or simple visual structure when appropriate
                If the dataset is too small or lacks time-based information, reply:
                "Not enough relevant data for meaningful analysis."

        🧾 Input Format
            User Question: {user_query}
            Detailed Intent: {action_query}
            Structured Data: {parsed_data_safe}

        ✅ Output Format (Markdown Only)
            Insight Summary
            <Write 4–6 sentences summarizing the key findings in natural language, aligned with user’s intent.>

            Details
            Trend: <State the trend with percentage change and time reference>
            Top Contributors: <List top items and their impact>
            Anomalies: <Mention significant outliers or large shifts> (omit if none)

        ✅ Instructions
            Base insights strictly on the provided data — do not guess or infer missing context
            Use clear numerical formatting for currency (e.g., $2,450)
            Express dates in human-readable format (e.g., "March 2025")
            Highlight growth or decline explicitly, including percentage and time period
            Treat similar annotations as distinct entities, unless told otherwise
            If data is unclear or inconsistent, call it out explicitly — no assumptions

        (End of answer)
        """
    )
    
    # Construct LLM prompt
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_message)
    ])
    
    # Invoke LLM for processing
    response = llm.invoke(prompt_template.format(
        user_query=user_query,
        action_query=action_query,
        sql_query=state.sql_query,
        parsed_data_safe=parsed_data_safe
    ))

    processed_result = response.content.strip()

    # Extract structured output using regex
    processed_match = re.search(r"Processed Output:\s*(.+)", processed_result, re.DOTALL | re.IGNORECASE)
    final_output = processed_match.group(1).strip() if processed_match else processed_result

    return final_output


def format_schema_to_string(schema_array):
    """
    Convert structured schema data into a human-readable string format.

    Args:
        schema_array (list): List containing a dict with 'primary_tables' and 'related_tables'.

    Returns:
        str: Formatted schema string.
    """
    output = []

    # Extract the main schema dictionary from the list
    schema_data = list(schema_array[0].values())[0]

    for section in ['primary_tables', 'related_tables']:
        for table in schema_data.get(section, []):
            output.append(f"**Table: {table['table_name']}**")
            for field in table['fields']:
                line = f"- {field['name']} (data-type: {field['data_type']}"
                extras = []

                # Optionally include additional attributes
                for key in ['alias', 'default', 'required']:
                    if key in field:
                        extras.append(f"{key}: {field[key]}")

                if extras:
                    line += ", " + ", ".join(extras)

                line += ")"

                # Add description if available
                if 'description' in field:
                    line += f": {field['description']}"

                output.append(line)
            output.append("")  # blank line between tables

    return "\n".join(output)

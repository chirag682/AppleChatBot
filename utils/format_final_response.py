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
        ### Intelligent Data Processing Assistant

        You are an **expert at transforming structured data** into clear, decision-ready insights based on SQL query outputs.

        ---

        ### Data Provided
            - **User Question:** {user_query}
            - **User's Detailed Question:** {action_query}
            - **SQL Query:** {sql_query}
            - **Data:** {parsed_data_safe}

        ---

        ### Your Task

        You will receive a dataset returned from an SQL query in structured format (JSON/table).  
        Your job is to:

        1. **Understand the intent**
        - Summarize the user’s goal in ≤15 words to anchor the analysis.

        2. **Explore the data**
        - Identify any date/time columns and derive period labels (week, month, quarter, year).
        - Calculate relevant changes (WoW, MoM, QoQ, or YoY) in the dataset.
        - Identify top and bottom contributors to the key metric(s).
        - Flag anomalies: values > ±2σ from the mean or changes ≥50%.
        - If the user asks for annotation summary, explain annotation content with relevant context (e.g., hierarchy, filters).

        3. **Generate a plain-English explanation**
        - Use **natural, clear language** appropriate for non-technical audiences.
        - Tailor your explanation to the user’s exact question.
        - Follow the output format below.
        - If the dataset is too small or lacks date info, return exactly:  
            **"Not enough relevant data for meaningful analysis."**

        ---

        ### Instructions
        - Base all insights strictly on the provided data — **no assumptions**.
        - Be concise but informative.
        - If the data includes monetary values, format appropriately (e.g., `$1,200`).
        - Use human-readable date formats (e.g., "January 2025").
        - Highlight growth/decline explicitly, with percentage change and suggested drivers.
        - Treat users/entities with the same annotations as **distinct**, unless explicitly stated.
        - If data is unclear or inconsistent, mention it **without guessing**.

        ---

        ### Output Format (Markdown Only)

        **Insight Summary**  
        <Concise narrative: 4–6 sentences summarizing the key findings relevant to the user’s goal.>

        **Details**  
        - **Trend:** …  
        - **Top drivers:** …  
        - **Anomalies:** … (omit if none)

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

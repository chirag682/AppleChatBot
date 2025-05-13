from langchain_core.prompts import ChatPromptTemplate
from langchain.prompts import PromptTemplate
from utils.schema_utils import fetch_table_names, fetch_table_schema, fetch_table_relations, safe_literal_eval
import json

def escape_curly_braces(text):
    return text.replace("{", "{{").replace("}", "}}")

def get_analyze_query_prompt(state):
     # Include error context if query execution previously failed
    error_context = f"⚠ **Previous Query Execution Failed:** {state.error}\n\n" if state.error else ""

    schema_dict = {
    "tables": [
        {
            "name": "annotations",
            "aliases": ["notes", "comments"],
            "desc": "User annotations linked to hierarchy",
            "fields": [
                "id", "username", "email", "timestamp", "content",
                "hierarchy_id", "annotation_status", "annotation_type"
            ],
            "references": ["hierarchy"]
        },
        {
            "name": "hierarchy",
            "aliases": ["organisation", "categories", "classification"],
            "desc": "Org category structure (l1-l5, metrics)",
            "fields": [
                "id", "l1", "l2", "l3", "l4", "l5", "is_leaf", "is_forecast",
                "group_id", "description", "last_month_spending",
                "user_count", "account_count_3pc", "account_count_first_party"
            ],
            "receives": ["annotations", "monthly_forecast", "user_role", "account"]
        },
        {
            "name": "monthly_forecast",
            "aliases": ["forecast_data", "monthly_budget"],
            "desc": "Forecast/spend data by month",
            "fields": [
                "fiscal_month", "fiscal_year", "forecast", "previous",
                "cloud_provider", "fiscal_quarter", "plug", "spend",
                "financial_spend", "comment", "cost_center"
            ],
            "references": ["hierarchy"]
        },
        {
            "name": "user_role",
            "desc": "User roles and access per hierarchy",
            "fields": ["id", "email", "role", "hierarchy_id", "view", "service"],
            "references": ["hierarchy"]
        },
        {
            "name": "account",
            "desc": "Cloud accounts metadata",
            "fields": [
                "account_id", "hierarchy_id", "account_name", "account_owner",
                "cloud_provider", "comment", "loaded_at", "decommissioned_at",
                "owner_name", "owner_dsid", "last_month_spend"
            ],
            "references": ["hierarchy"]
        }
    ]
}
    
    escaped_schema_json = escape_curly_braces(json.dumps(schema_dict, indent=2))

    
    system_message = (
        "**User Query Breakdown Assistant**\n"
        "Your task is to analyze the user’s question and break it down into three components:\n"
        "1. **Query_Details** – What specific data is requested (for SQL).\n"
        "2. **Action_Details** – What is the high-level user intent (human-readable summary).\n"
        "3. **Cypher_Details** – Which tables (nodes), fields (properties), and relationships are needed for graph-based schema lookup.\n\n"

        "**DO NOT write SQL or Cypher code.** Just describe the needed components.\n\n"

        "**Query_Details (What Data to Fetch)**\n"
        "You are an assistant that extracts the key elements from a user’s query to help generate accurate SQL.\n"
        "- Identify **what specific data** is needed from the database.\n"
        "- Use the **table schema, field names, and relationships** below to align the user request with relevant tables and fields.\n"
        "- If the user intends to use SQL functions (e.g., `SUM`, `COUNT`, `AVG`), include that in `Query_Details`.\n"
        "- **DO NOT write SQL.** Just describe in plain terms what needs to be retrieved.\n\n"
        "-  Consider mentioning table name wherever possible, **add the suffix** ` table` (e.g., `annotations table`) for better understanding."

        "**Action_Details (How to Process the Data)**\n"
        "- Identify any **post-processing** needed, like summarization, insight extraction, or reformatting.\n"
        "- Do **NOT** repeat SQL functions here. If the user asks for narrative insights or summaries, capture that here.\n"
        "- If no processing is needed, respond with: `No additional processing required.`\n\n"
        
        "- For `Cypher_Details`, identify:\n"
        " - Primary table(s) to begin with.\n"
        " - Key fields mentioned.\n"
        " - Any referenced or referencing tables connected via relationships.\n\n"
       

        "### **Response Format:**\n"
        "```plaintext\n"
        "Query_Details: (clear description of data required for SQL)\n"
        "Action_Details: (high-level, human-readable summary of user intent)\n"
        "Cypher_Details: (summary of tables, fields, and relationships for graph-based schema reasoning)\n"
        "```\n"
        "**Strictly follow this format.**\n\n"

        "### **Database Schema for Reference**\n"
        f"{escaped_schema_json}"
    )

    # Construct LLM prompt
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", error_context + system_message),
        ("human", f"User Query: {state.user_query}")
    ])
    return prompt_template 


def get_sql_generation_prompt() -> str:
    """
    Generate an SQL query prompt based on the current state and database schema.
    
    Parameters:
    - state (dict): Contains user input details (e.g., tables, columns, conditions, etc.).
    
    Returns:
    - str: SQL query prompt.
    """
    
    prompt =  ChatPromptTemplate.from_messages([
        ("system", """
        You are an expert SQL assistant with access to a relational database.
        Generate a **correct and optimized** SQL query for the given user question.

        Below is the **table structure** and **relationships** in the database.
        Use this information to generate correct SQL queries.

        ### **Tables Available:**
        {table_names}
        ---
        ### ** Column Details (Per Table)**
        {formatted_schema}

        - Each entry represents a table with its column names and data types.
        - **If the user asks for hierarchy-related data, always fetch all levels (`l1, l2, l3, l4, l5`) from hierarcy table.** 
        - **Ensure you only query existing columns from this schema.**
        - **Example Mapping:** If the user asks for "status," check if it's available under "annotation_status."

        ---

        ### ** Table Relationships (Foreign Keys & Joins)**
        {formatted_relations}

        - **Use these relationships when joining tables** instead of making assumptions.

        **Rules:**
        - Ensure correctness by validating column names.
        - Use **INNER JOINs** by default when combining tables to ensure only matching records are retrieved.  
        - Use **LEFT/RIGHT/FULL JOINs** only if the query requires retrieving unmatched records from one table.  
        - Always refer to the **schema and relationships** to determine the appropriate join conditions.
        - Retrieve only relevant columns (avoid SELECT *).
        - DO NOT execute any INSERT, UPDATE, DELETE, or DROP statements.
        - **For filtering data based on the current date, use SQLite's `strftime()` function** instead of `EXTRACT()` or `CURRENT_DATE`.  
        - Example for filtering records from the current month:
        ```sql
        WHERE strftime('%Y', column_name) = strftime('%Y', 'now')
            AND strftime('%m', column_name) = strftime('%m', 'now')
        -Make Conditions Case-Insensitive:
            Use LOWER() or UPPER() to make value matching case-insensitive.
            WHERE LOWER(a.l1) = LOWER('Finance')
        - When the user asks for "last month" or "last year," generate a query that retrieves data from the first to the last day of the previous calendar month or year.
        - When the user asks for "current month" or "current year," retrieve data from the first day of the current calendar period until now.
        - If the user asks for "last 30 days" or "last 365 days," generate a rolling window query.
        - If the user specifies a custom date range, reflect the exact range in the query.
        - If the query is ambiguous, prioritize the most logical complete period (e.g., last full month).


        ### *Similar User Queries & their queries Responses*
        Below are previously retrieved user queries along with their corresponding SQL queries. Use these examples to understand query patterns and generate the most accurate SQL query:

        {chroma_results}

        - Use this queries only as a reference.
        - DO NOT copy queries directly unless they exactly match the current user request.
        - Modify queries to fit the current request while following schema constraints.
        """),
        ("user", "{input}")
    ])
    
    return prompt


def get_report_url_prompt() -> str:
    prompt_template = ChatPromptTemplate.from_messages([
        ("system","""
            ### *Prompt for LLM to Generate Context-Aware URL Based on User Query, SQL Query.*
            Generate the appropriate URL based on the user query and SQL query using the rules and filters provided below.

            ---

            ### *Rules for Choosing the Correct View:*  
            1. *If the user explicitly asks for hierarchy data*, generate a *Hierarchy View URL*, even if annotation-related filters are in the SQL query.  
            2. *If the user explicitly asks for annotation data*, generate an *Annotation View URL*, even if `l1` is present.  
            3. *If the user’s query is ambiguous*, analyze the SQL query:  
                - If the SQL query contains *only hierarchy-related data*, assume *Hierarchy View*.  
                - If the SQL query contains *only annotation-related data*, assume *Annotation View*.  
                - If the SQL query contains *both types of data*, return *only the Annotation View URL* (since annotation data takes priority).  
            4. If the SQL query returns no data or no specific URL can be generated, use the default URL: https://example.com/annotation

            ---

            ### *Extract and Encode Filters from SQL Query:*  
            - *Hierarchy Level (l1):*  
            - Extract from `l1 IN (...)` or `l1 = '...'`.  
            - *Default:* `'ALL'` if missing.  
            - *Encoding:* Replace spaces with `%20`, separate multiple values with `%2C`.  
            - *Source:*  
            - Extract from `source = '...'`.  
            - Allowed values: `'3PC'`, `'First Party'`.  
            - *Default:* `'3PC'` if missing.  
            - *Encoding:* Replace spaces with `%20`.  
            - *Time Aggregation (timeAggregation):*  
            - Extract from `annotation_type = '...'`.  
            - Allowed values: `'MONTHLY'`, `'YEARLY'`, `'ALL'`.  
            - *Default:* `timeAggregation='MONTHLY'`.   
            - *Annotation Status (annotationStatus):*  
            - Extract from `annotation_status = '...'`.  
            - Allowed values: `'COMPLETED'`, `'IN_PROGRESS'`, `'PENDING'`, `'ALL'`.  
            - *Default:* `annotationStatus='ALL'`.  

            ---

            ###Key Roles and Responsibilities:
            Encode URL characters correctly (&, =, ?, +, /, #, :).
            Maintain consistent URL structure and casing.
            If required filters are missing, apply defaults and encode them properly.
            If user query and SQL query conflict, prioritize the user query.
            Include all parameters even if the value is 'ALL' unless explicitly excluded.

            ---

            ### *URL Format:* 

            #### *Hierarchy View URL:*  
            https://example.com/hierarchy?l1=<l1_value>&source=<source_value>
            #### *Annotation View URL:*  
            https://example.com/annotation?l1=<l1_value>&timeAggregation=<timeAggregation_value>&annotationStatus=<annotation_status_value>

            ---

            ### *Example Scenarios:*  

            #### *Case 1: Clear User Intent for Hierarchy*  
            *User Query:*  
            "What are the available hierarchies for Finance?"  

            *SQL Query:*  
            sql
            SELECT * FROM hierarchy WHERE l1 = 'Finance' AND source = '3PC';
            SQL Query Result: (Returns hierarchy data)

            Generated URL (Hierarchy View):
            https://example.com/hierarchy?l1=Finance&source=3PC

            Case 2: Clear User Intent for Annotations
            User Query:
            "Show me monthly annotations for Healthcare."
            SELECT * FROM annotations WHERE l1 = 'Healthcare' AND annotation_type = 'MONTHLY';

            SQL Query:
            SELECT * FROM annotations WHERE l1 = 'Healthcare' AND annotation_type = 'MONTHLY';
            SQL Query Result: (Returns annotation data)

            Generated URL (Annotation View):
            https://example.com/annotation?l1=Healthcare&timeAggregation=MONTHLY&annotationStatus=ALL

            Case 3: Ambiguous User Query, Hierarchy Data Found
            User Query:
            "Show me Finance data."

            SQL Query:
            SELECT * FROM hierarchy WHERE l1 = 'Finance';
            SQL Query Result: (Returns hierarchy-related rows, no annotation data)

            Generated URL (Hierarchy View):
            https://example.com/hierarchy?l1=Finance&source=3PC

            Case 4: Ambiguous User Query, Annotation Data Found
            User Query:
            "Show me Finance data."

            SQL Query:
            SELECT * FROM annotations WHERE l1 = 'Finance' AND annotation_type = 'YEARLY';
            SQL Query Result: (Returns annotation-related data)

            Generated URL (Annotation View):
            https://example.com/annotation?l1=Finance&timeAggregation=YEARLY&annotationStatus=ALL

            Case 5: Ambiguous User Query, Both Data Types Found (Use Annotation View by Default)
            User Query:
            "Show me Finance data."

            SQL Query:
            SELECT * FROM hierarchy WHERE l1 = 'Finance';
            SELECT * FROM annotations WHERE l1 = 'Finance' AND annotation_type = 'ALL';
            SQL Query Result: (Returns both hierarchy and annotation data)

            Since both types of data are present, return both URLs and let the user decide: 
            Annotation View: https://example.com/annotation?l1=Finance&timeAggregation=ALL&annotationStatus=ALL

            Case 6: SQL Query Returns No Data (Use Annotation View by Default)
            User Query:
            "Show me Finance data."

            SQL Query:
            SELECT * FROM annotations WHERE l1 = 'Finance' AND annotation_type = 'ALL';
            SQL Query Result: (No rows returned)
            Annotation View: https://example.com/annotation?l1=Finance&timeAggregation=ALL&annotationStatus=ALL

        """),
        ("human", """  
            User Query: {input}.  
            SQL Query: {query}
            """)
    ])
    
    return prompt_template


def get_cypher_generation_prompt() -> str:
    return PromptTemplate(
        template = """
            You are an expert in analyzing database schemas modeled in Neo4j. Write queries strictly according to **Neo4j Cypher syntax**.

            In this Neo4j graph:
            - Each **node** is a `Table` representing a **database table**.
            - Each `Table` node contains properties that define the **fields (columns)** of that table.
            - Each `Field` node is connected via a `[:CONTAINS]` relationship to its corresponding `Table`.
            - Relationships between `Table` nodes (e.g., `REFERENCES`, `RECEIVES`) represent **schema-level links**, such as foreign key dependencies.

            ---

            ### Your task:
            1. Understand the user’s question and identify the **main table(s)** referenced.
            2. Construct a **single Cypher query** that:
                - Matches the main table(s) using `toLower(...name) =~ "(?i).*..."` (case-insensitive, pattern-based matching) instead of `CONTAINS` for flexible and similar searches.
                - Uses `OPTIONAL MATCH` to expand to related tables via schema relationships.
                - Retrieves all matched tables’ fields with `MATCH (table)-[:CONTAINS]->(field:Field)`.
            3. Aggregate all data **before** the `RETURN` clause.
            4. For each table (primary or related), collect its fields in a separate step:
                - Use `MATCH (t)-[:CONTAINS]->(f:Field)` and `COLLECT(f)` for each distinct table node (e.g., `t`, `related`).
                - Assign different aliases for each table and its fields (e.g., `t`, `related`, `t_fields`, `related_fields`) to avoid overwriting data.
            5. At the end, return a list of objects by **collecting all structured results** before returning them in a single list.

            ### DOs:
            - Use separate `MATCH` or `OPTIONAL MATCH` clauses for each node/relationship.
            - Always **`COLLECT` field nodes before using them in list comprehensions.**
            - Use `WITH` clauses to manage intermediate variables and pass data forward.
            - Return only a **single `RETURN` block** at the end.
            - If no related table exists, return only the primary table and its fields.
            - In Cypher, map keys must not be enclosed in double quotes. Use unquoted keys (e.g., table_name: value, not "table_name": value) when constructing map objects in the RETURN clause.
            - Ensure all data is collected before RETURN: Use WITH to manage variables and pass required nodes and properties forward.
            - Use the same variable names in RETURN as in the WITH clauses to ensure consistency.
            ---

            ### DON’Ts:
            - Do NOT embed MATCH patterns inside `RETURN` or list comprehensions.
            - Do NOT use more than one `RETURN` clause.
            - Do NOT return actual business data.
            - Do NOT use SQL-like syntax (`SELECT`, `FROM`, etc.).
            - Do NOT reference undefined variables in the `RETURN`.
            - Don’t attempt to access variables that haven’t been passed through the current WITH clauses, as this causes errors
            ---

            ### Schema Relationships Summary:
            {schema}

            ---

            ### User Question:
            {question}

            ---

            ### Output:
            Return only a **valid, executable Cypher query** that:
            - Matches main and related tables,
            - Collects their fields properly,
            - Returns a clean JSON-like object with all matched and related tables. 

            Return only the Cypher query, and nothing else.
            """,
        input_variables=["schema", "question"]
    )
def get_qa_prompt() -> str:
    return PromptTemplate(
        template="""
        You are an assistant that summarizes database schema information retrieved from a Cypher query over a graph of tables and their relationships.

        Your task is to:
        - For each table, summarize its **fields (columns)** in plain English.
        - Mention any **relationships** between the tables, if applicable.
        - Write the summary in a way that helps a llm understand the structure for writing SQL queries.

        Do **NOT** include actual business data or query results — only describe the schema (tables, fields, and their relationships).

        ---
        Question: {question}  
        Cypher Query: {query}  
        Query Results (schema context): {context}

        ---
        Schema Summary:
        - Clearly list each table involved (by name).
        - For each table, write: `"The '<table name>' table contains fields like: <field1>, <field2>, ..."`
        - If any relationship exists (e.g., table A references table B), write: `"The '<table A>' table is linked to '<table B>' via a schema relationship."`
        - Keep the explanation **short, structured, and suitable as input to an SQL generation assistant.**
        """,
        input_variables=["question", "query", "context"],
    )
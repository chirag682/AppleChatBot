from langchain_core.prompts import ChatPromptTemplate
from langchain.prompts import PromptTemplate
from utils.schema_utils import fetch_table_names, fetch_table_schema, fetch_table_relations, safe_literal_eval
import json

def escape_curly_braces(text):
    return text.replace("{", "{{").replace("}", "}}")

def get_analyze_query_prompt(state):
     # Include error context if query execution previously failed
    error_context = f"⚠ **Previous Query Execution Failed:** {state.error}\n\n" if state.error else ""

#     schema_dict = {
#     "tables": [
#         {
#             "name": "hierarchy",
#             "aliases": ["organisation", "categories", "classification"],
#             "desc": "Represents the full organizational category structure across multiple levels (L1 to L5). Each record defines a hierarchical node with optional metrics and metadata. It includes flags like `is_leaf` to denote terminal nodes and `is_forecast` for forecast-related nodes. Also tracks associated groups, textual descriptions, past financial performance, and entity counts (e.g., users and accounts). This table is referenced by several others including annotations, forecasts, accounts, and user-role mappings",
#             "fields": [
#                 "id", "l1", "l2", "l3", "l4", "l5", "is_leaf", "is_forecast",
#                 "group_id", "description", "last_month_spending",
#                 "user_count", "account_count_3pc", "account_count_first_party"
#             ],
#             "receives": ["annotations", "monthly_forecast", "user_role", "account"]
#         },
#         {
#             "name": "monthly_forecast",
#             "aliases": ["forecast_data", "monthly_budget"],
#             "desc": "Forecast/spend data by month",
#             "fields": [
#                 "fiscal_month", "fiscal_year", "forecast", "previous",
#                 "cloud_provider", "fiscal_quarter", "plug", "spend",
#                 "financial_spend", "comment", "cost_center"
#             ],
#             "references": ["hierarchy"]
#         },
#         {
#             "name": "user_role",
#             "aliases": ["user_info","user_permissions"],
#             "desc": "Stores information about all users, their assigned roles, and access permissions based on organizational hierarchy. Each record links a user (by email) to a specific role and a hierarchy level, along with defined views and services they can access.",
#             "fields": ["id", "email", "role", "hierarchy_id", "view", "service"],
#             "references": ["hierarchy"]
#         },
#         {
#             "name": "account",
#             "aliases": ["account","user_permissions"],
#             "desc": "Cloud accounts metadata",
#             "fields": [
#                 "account_id", "hierarchy_id", "account_name", "account_owner",
#                 "cloud_provider", "comment", "loaded_at", "decommissioned_at",
#                 "owner_name", "owner_dsid", "last_month_spend"
#             ],
#             "references": ["hierarchy"]
#         },
#         {
#             "name": "annotations",
#             "aliases": ["notes", "comments"],
#             "desc": "Contains annotations created by users, each linked to a specific level in the organizational hierarchy. These annotations typically represent user-generated notes, comments, or metadata associated with hierarchical entities.",
#             "fields": [
#                 "id", "username", "email", "timestamp", "content",
#                 "hierarchy_id", "annotation_status", "annotation_type"
#             ],
#             "references": ["hierarchy"]
#         }
#     ]
# }
    
    schema_dict = """
         
        Table: hierarchy (aliases: organisation, categories, classification)
        Represents the full organizational category structure from levels L1 to L5. Each row defines a node with metadata such as forecast flags, group association, performance indicators, and entity counts (users and accounts). 
        Referenced by: annotations, monthly_forecast, user_role, account

        Relationships:
        - Central table in the schema; acts as the parent for most other tables.
        - Joinable with: monthly_forecast, user_role, account, annotations (via hierarchy_id)

        Table: monthly_forecast (aliases: forecast_data, monthly_budget)
        Stores monthly and yearly forecast and budget data including adjustments, spending figures, and financial commentary.
        References: hierarchy

        Relationships:
        - Connected to hierarchy via hierarchy_id
        - Often used together with: hierarchy, user_role (for role-based budget access)

        Table: user_role (aliases: user_info, user_permissions)
        Contains user-to-role mapping, defining access based on organizational hierarchy and permissions like view or service access.
        References: hierarchy

        Relationships:
        - Linked to hierarchy for role scoping
        - Can be joined with: hierarchy, annotations (for role-specific annotations)

        Table: account (alias: account info)
        Stores metadata about cloud accounts including ownership, provider info, status, and links to hierarchy nodes.
        References: hierarchy

        Relationships:
        - Joinable with hierarchy for account classification
        - Often queried with: monthly_forecast (for account-based spend) and user_role (for access management)

        Table: annotations (aliases: notes, comments)
        Captures user-generated annotations tied to specific hierarchy levels. Typically used for storing comments, feedback, or notes.
        References: hierarchy

        Relationships:
        - Linked to hierarchy
        - Frequently combined with: user_role (to filter annotations by user) and monthly_forecast (for annotated metrics)
    """

    
    system_message = (
        "**User Query Breakdown Assistant**\n"
        "Your task is to analyze the user’s question and break it down into three components:\n"
        "1. **Query_Details** – What specific data is requested (for SQL).\n"
        "2. **Action_Details** – What is the high-level user intent (human-readable summary).\n"
        "3. **Cypher_Details** – Which tables (nodes) are needed for graph-based schema lookup.\n\n"

        "**DO NOT write SQL or Cypher code.** Just describe the needed components.\n\n"

        "**Query_Details (What Data to Fetch)**\n"
        "You are an assistant that extracts the key elements from a user’s query to help generate accurate SQL.\n"
        "- Identify **what specific data** is needed from the database.\n"
        "- Use the **table schema, field names, and relationships** below to align the user request with relevant tables and fields.\n"
        "- If the user intends to use SQL functions (e.g., `SUM`, `COUNT`, `AVG`), include that in `Query_Details`.\n"
        "- **DO NOT write SQL.** Just describe in plain terms what needs to be retrieved.\n\n"
        "-  Consider mentioning table name wherever possible, **add the suffix** ` table` (e.g., `annotations table`) for better understanding."
        "- - When matching textual values (e.g., for filters like names, labels, departments), **assume case-insensitive matching by default**. Indicate that the query should use `ILIKE` or `LOWER(...) = LOWER(...)` unless explicitly instructed otherwise."
        
        "**Action_Details (How to Process the Data)**\n"
        "- Identify any **post-processing** needed, like summarization, visualization, insight extraction, or reformatting.\n"
        "- Do **NOT** repeat SQL functions here. If the user asks for narrative insights or summaries, capture that here.\n"
        "- If no processing is needed, respond with: `No additional processing required.`\n\n"
        
        "- For `Cypher_Details`, identify:\n"
        "1. Identify tables that contain the core data requested and return as  **primary table(s)**."
        "2. Base your decision only on the **provided schema context**."
        "3. DO NOT generate Cypher or SQL code."
        "4. Use only the tables and relationships defined in the provided schema."
        "5. If the user’s query includes a field name, map it to the corresponding field name using the field information from the schema."
        "6. Do not introduce any tables or assumptions outside of what’s explicitly given."
            
        "### **Response Format:**\n"
        "```plaintext\n"
        "Query_Details: (clear description of data required for SQL)\n"
        "Action_Details: (high-level, human-readable summary of user intent)\n"
        "Cypher_Details: (summary of tables, and relationships for graph-based schema reasoning)\n"
        "```\n"
        "**Strictly follow this format.**\n\n"

        "### **Database Schema for Reference**\n"
        f"{schema_dict}"
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
    
        # ("system", """
        #     You are a PostgreSQL SQL generation assistant.

        #     Your task is to generate a **correct, complete, and optimized SQL query** by synthesizing:
        #     • The user’s natural-language question (`user_query`)
        #     • A schema-aware interpretation of their request (`db_query`)
        #     • The full database schema and relationships (`schema_info`)
        #     • Example historical queries for guidance (`chroma_results`)

        #     ────────────────────────────────────────────────────────

        #     INTERPRETED DB QUERY
        #     {db_query}

        #     Treat this as a helpful reformulation grounded in schema terminology. Use it to:
        #     • Resolve ambiguous terms
        #     • Align synonyms or alias-like language
        #     • Choose correct tables and fields

        #     ────────────────────────────────────────────────────────
        #     SCHEMA & RELATIONSHIPS
        #     {schema_info}

        #     — Use only columns/tables listed.
        #     — Use declared foreign key relationships for joins.
        #     — Never invent columns or guess join paths.

        #     ────────────────────────────────────────────────────────
        #     SQL GENERATION RULES

        #     1. **Correctness**
        #     • Validate every table, column, and data type.
        #     • Always choose join paths based on foreign key definitions.
        #     • Never use `SELECT *` — project only relevant + contextual columns.
        #     • When performing an ORDER BY on a field, ensure null values are excluded by adding a WHERE field IS NOT NULL clause to maintain sorting integrity.

        #     2. **Data-Type Awareness**
        #     • Don’t assume type from column name — always refer to schema.
        #         - e.g. `fiscal_year` might be `integer` or `varchar`.
        #     • Adjust comparisons and functions accordingly:
        #         - If `varchar`: use , `LOWER()`, `SUBSTRING()`, etc.
        #         - If `int/date`: use `=`, `>=`, `EXTRACT()`, etc.
        #     • Use `CAST()` when crossing types, like:  
        #         `CAST(fiscal_year AS INT)` or `CAST(period_str AS DATE)`
        #         -- Note: ILIKE and LIKE do not work directly with ENUM or USER_DEFINED values; cast to text before using them.

        #     3. **Time-Sensitive Handling**
        #     • Use correct logic for `timestamp` vs `varchar` date fields.
        #     • Prefer `NOW()` over `CURRENT_DATE` for dynamic filters.
        #     • Include `year` field when filtering by `month`, if possible.
        #     • Avoid using `EXTRACT()` on non-date fields.

        #     4. **Case-Insensitive Text Matching**
        #     • Use `LOWER(col) = LOWER(val)` for all text filters.
        #     • Prefer not to use ILIKE/LIKE unless the user explicitly requests case-insensitive or pattern matching, 

        #     5. **Hierarchies**
        #     • If the question involves hierarchy, include all levels:
        #         - `l1`, `l2`, `l3`, `l4`, `l5` from the `hierarchy` table.

        #     6. **Contextual Enrichment**
        #     • If fetching metrics (`spend`, `forecast`, `usage`, etc.), include useful grouping fields:
        #         - `cost_center`, `cloud_provider`, `owner`, `category`, etc. if present.
            
        #     7. **Complex Logic Handling**
        #     • For queries involving:
        #         - Top-N selection with nested breakdowns (e.g., top 5 orgs with spend by provider)
        #         - JSON aggregation (`ARRAY_AGG`, `JSON_BUILD_OBJECT`)
        #         - Window functions with filtering or ranking
        #     → Use a **WITH clause (CTE)** or temporary subqueries to:
        #         • Precompute aggregates before formatting them
        #         • Avoid nesting aggregate functions (e.g., `SUM()` inside `ARRAY_AGG()`)
        #         • Make complex queries more readable and maintainable
                
        #     ────────────────────────────────────────────────────────
        #     COMMON PITFALLS TO AVOID

        #     | Pitfall                             | Example                                             |
        #     |------------------------------------|-----------------------------------------------------|
        #     | Trusting column names over types   | Using `EXTRACT()` on `fiscal_year` that's VARCHAR   |
        #     | Assuming joins not based on FK     | Manual guesses instead of schema-enforced joins     |
        #     | Case-sensitive text comparison     | Using `=` instead of `ILIKE`                        |
        #     | SELECT *                           | Always specify fields explicitly                    |
        #     | Missing key grouping fields        | Omitting `cloud_provider`, `cost_center`, etc.      |

        #     ────────────────────────────────────────────────────────
        #     SIMILAR QUERIES REFERENCE Examples
        #     Example1:
        #         user:  List yearly wise spend for Infrastructure hierarchy
        #         sql : 'SELECT
        #                 monthly_forecast.fiscal_year AS fiscal_year,
        #                 SUM(monthly_forecast.spend) AS total_spend
        #             FROM
        #                 monthly_forecast
        #             JOIN
        #                 hierarchy ON monthly_forecast.hierarchy_id = hierarchy.id
        #             WHERE
        #                 hierarchy.l1 ILIKE 'Infrastructure'
        #             GROUP BY
        #                 fiscal_year
        #             ORDER BY
        #                 fiscal_year;'
        #     Example2:
        #         user:  List month wise spend for AWS cloud provider for acare hierarchy for current year,
        #         sql : 'SELECT
        #                     monthly_forecast.fiscal_year AS fiscal_year,
        #                     monthly_forecast.fiscal_month AS fiscal_month,
        #                     SUM(monthly_forecast.spend) AS total_spend
        #                 FROM
        #                     monthly_forecast
        #                 JOIN
        #                     hierarchy ON monthly_forecast.hierarchy_id = hierarchy.id
        #                 WHERE
        #                     lower(hierarchy.l1) = lower('Infrastructure') AND LOWER(monthly_forecast.cloud_provider::text) = LOWER('AWS') --cloud_provider is an ENUM, and PostgreSQL does not allow applying LOWER() directly to ENUM values — similar to how ILIKE fails on ENUMs.
        #                     AND monthly_forecast.fiscal_year = EXTRACT(YEAR FROM NOW())
        #                 GROUP BY
        #                     fiscal_year, fiscal_month
        #                 ORDER BY
        #                     fiscal_year, fiscal_month;'
        #         Example3:
        #             user:  List top 5 orgs with maximum spend in current fiscal year also listing the spend breakdown by cloud provider for each org.
        #             sql : 'WITH OrgSpend AS (
        #                     SELECT
        #                         mf.hierarchy_id,
        #                         h.l1,
        #                         h.l2,
        #                         h.l3,
        #                         h.l4,
        #                         h.l5,
        #                         SUM(mf.spend) AS total_spend
        #                     FROM
        #                         monthly_forecast mf
        #                     JOIN
        #                         hierarchy h ON mf.hierarchy_id = h.id
        #                     WHERE
        #                         mf.fiscal_year = EXTRACT(YEAR FROM NOW())
        #                         AND mf.spend IS NOT NULL  -- Ensure spend is not null before aggregation
        #                     GROUP BY
        #                         mf.hierarchy_id, h.l1, h.l2, h.l3, h.l4, h.l5
        #                     HAVING
        #                         SUM(mf.spend) IS NOT NULL  -- Exclude groups with null spend
        #                     ORDER BY
        #                         total_spend DESC
        #                     LIMIT 5
        #                 )
        #                 SELECT
        #                     os.l1,
        #                     os.l2,
        #                     os.l3,
        #                     os.l4,
        #                     os.l5,
        #                     os.total_spend,
        #                     LOWER(mf.cloud_provider::text) AS cloud_provider,
        #                     SUM(mf.spend) AS provider_spend
        #                 FROM
        #                     OrgSpend os
        #                 JOIN
        #                     monthly_forecast mf ON os.hierarchy_id = mf.hierarchy_id
        #                 WHERE
        #                     mf.fiscal_year = EXTRACT(YEAR FROM NOW())
        #                     AND mf.cloud_provider IS NOT NULL
        #                     AND mf.spend IS NOT NULL
        #                 GROUP BY
        #                     os.l1, os.l2, os.l3, os.l4, os.l5, os.total_spend, mf.cloud_provider
        #                 ORDER BY
        #                     os.total_spend DESC;'
        #     {chroma_results}

        #     Use these for structure & logic. Never copy unless the meaning matches exactly.

        #     ────────────────────────────────────────────────────────
        #     Now, generate the PostgreSQL SQL query based on the schema and the interpreted intent.
        # """),
        # ("user", "{input}")
        
        ("system", """
            You are a PostgreSQL SQL generation assistant.

            Your task is to generate a **correct, complete, and optimized SQL query** by synthesizing:

            INTERPRETED DB QUERY
            {db_query}

            → A version of the user’s query that has been rewritten using precise schema terminology.  
            Use this to:
            - Remove ambiguity or vague terms.
            - Align synonyms to schema-specific field names.
            - Choose correct tables and fields.

            DATABASE SCHEMA & RELATIONSHIPS
            {schema_info}

            → A complete list of available tables, columns, and declared foreign key relationships.  
            Strict rules:
            - Use only the listed tables and columns.
            - Only use declared foreign key relationships to join tables.
            - Never guess or invent join paths or columns.


            ─────────────────────────────────────────────
            🔧 SQL GENERATION RULES

            CORRECTNESS
            - Always validate table and column names using the schema.
            - Only use foreign key paths for joins.
            - Do not use `SELECT *` — project only relevant fields.
            - When using `ORDER BY`, include `WHERE column IS NOT NULL` to preserve sorting logic.

            DATA TYPES
            - Confirm column types using the schema before applying functions or filters.
            - For text fields: use `LOWER()`, `SUBSTRING()`, etc.
            - For numeric or date fields: use `=`, `>=`, `EXTRACT()`, etc.
            - Use `CAST()` where needed, such as:
            - `CAST(fiscal_year AS INT)`
            - `CAST(period_str AS DATE)`
            - ENUM or USER_DEFINED types must be cast to `TEXT` before using `LIKE`, `ILIKE`, or `LOWER()`.

            TIME FIELDS
            - Use `NOW()` for dynamic date filtering (not `CURRENT_DATE`).
            - Only apply `EXTRACT()` to actual date or timestamp fields.
            - When filtering by `month`, also include the `year`.

            TEXT COMPARISONS
            - By default, apply case-insensitive matching using `LOWER(column) = LOWER(value)`.
            - Use `ILIKE` or `LIKE` only if user explicitly requests pattern or partial match.

            HIERARCHY AWARENESS
            - If the question involves organizational structure, include all five hierarchy levels:
            - `l1`, `l2`, `l3`, `l4`, `l5` from the `hierarchy` table.

            METRIC CONTEXT
            - If querying metrics (e.g. spend, forecast, usage), enrich results by grouping with contextual fields like:
            - `cloud_provider`, `cost_center`, `category`, `owner` (if available in the schema).

            COMPLEX QUERIES
            Use CTEs (`WITH` clauses) when the query involves:
            - Top-N selection with nested grouping or filters
            - Precomputing aggregates before further operations
            - Using both `SUM()` and `ARRAY_AGG()` or JSON functions
            - Window functions for ranking, partitioning, or filtering

            ─────────────────────────────────────────────
            COMMON MISTAKES TO AVOID (LLM-FRIENDLY FORMAT)

            Avoid these common mistakes:

            - Never invent joins.  
            Only join tables using foreign keys declared in the schema.

            - Don’t assume column types.  
            Always confirm column types from the schema before filtering or casting.

            - Never use SELECT *.  
            Always list only the required columns in the SELECT clause.

            - Avoid case-sensitive comparisons.  
            Use `LOWER(column) = LOWER(value)` unless pattern matching is explicitly required.

            - Don’t omit context fields.  
            When showing metrics like spend or forecast, group by contextual fields like `cloud_provider`, `cost_center`, or `category`.

            ───────────────────────────────────────────── 
            SIMILAR QUERIES REFERENCE Examples
            Example1:
                user:  List yearly wise spend for Infrastructure hierarchy
                sql : 'SELECT
                        monthly_forecast.fiscal_year AS fiscal_year,
                        SUM(monthly_forecast.spend) AS total_spend
                    FROM
                        monthly_forecast
                    JOIN
                        hierarchy ON monthly_forecast.hierarchy_id = hierarchy.id
                    WHERE
                        hierarchy.l1 ILIKE 'Infrastructure'
                    GROUP BY
                        fiscal_year
                    ORDER BY
                        fiscal_year;'
            Example2:
                user:  List month wise spend for AWS cloud provider for acare hierarchy for current year,
                sql : 'SELECT
                            monthly_forecast.fiscal_year AS fiscal_year,
                            monthly_forecast.fiscal_month AS fiscal_month,
                            SUM(monthly_forecast.spend) AS total_spend
                        FROM
                            monthly_forecast
                        JOIN
                            hierarchy ON monthly_forecast.hierarchy_id = hierarchy.id
                        WHERE
                            lower(hierarchy.l1) = lower('Infrastructure') AND LOWER(monthly_forecast.cloud_provider::text) = LOWER('AWS') --cloud_provider is an ENUM, and PostgreSQL does not allow applying LOWER() directly to ENUM values — similar to how ILIKE fails on ENUMs.
                            AND monthly_forecast.fiscal_year = EXTRACT(YEAR FROM NOW())
                        GROUP BY
                            fiscal_year, fiscal_month
                        ORDER BY
                            fiscal_year, fiscal_month;'
                Example3:
                    user:  List top 5 orgs with maximum spend in current fiscal year also listing the spend breakdown by cloud provider for each org.
                    sql : 'WITH OrgSpend AS (
                            SELECT
                                mf.hierarchy_id,
                                h.l1,
                                h.l2,
                                h.l3,
                                h.l4,
                                h.l5,
                                SUM(mf.spend) AS total_spend
                            FROM
                                monthly_forecast mf
                            JOIN
                                hierarchy h ON mf.hierarchy_id = h.id
                            WHERE
                                mf.fiscal_year = EXTRACT(YEAR FROM NOW())
                                AND mf.spend IS NOT NULL  -- Ensure spend is not null before aggregation
                            GROUP BY
                                mf.hierarchy_id, h.l1, h.l2, h.l3, h.l4, h.l5
                            HAVING
                                SUM(mf.spend) IS NOT NULL  -- Exclude groups with null spend
                            ORDER BY
                                total_spend DESC
                            LIMIT 5
                        )
                        SELECT
                            os.l1,
                            os.l2,
                            os.l3,
                            os.l4,
                            os.l5,
                            os.total_spend,
                            LOWER(mf.cloud_provider::text) AS cloud_provider,
                            SUM(mf.spend) AS provider_spend
                        FROM
                            OrgSpend os
                        JOIN
                            monthly_forecast mf ON os.hierarchy_id = mf.hierarchy_id
                        WHERE
                            mf.fiscal_year = EXTRACT(YEAR FROM NOW())
                            AND mf.cloud_provider IS NOT NULL
                            AND mf.spend IS NOT NULL
                        GROUP BY
                            os.l1, os.l2, os.l3, os.l4, os.l5, os.total_spend, mf.cloud_provider
                        ORDER BY
                            os.total_spend DESC;'
            {chroma_results}

            Use these for structure & logic. Never copy unless the meaning matches exactly.

            ────────────────────────────────────────────────────────
            Now, generate the PostgreSQL SQL query based on the schema and the interpreted intent.
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
        # template = """
        #     You are an expert in analyzing database schemas modeled in Neo4j. Write queries strictly according to **Neo4j Cypher syntax**.

        #     In this Neo4j graph:
        #     - Each **node** is a `Table` representing a **database table**.
        #     - Each `Table` node contains properties that define the **fields (columns)** of that table.
        #     - Each `Field` node is connected via a `[:CONTAINS]` relationship to its corresponding `Table`.
        #     - Relationships between `Table` nodes (e.g., `REFERENCES`, `RECEIVES`) represent **schema-level links**, such as foreign key dependencies.

        #     ---

        #     ### Your task:
        #     1. Understand the user’s question and identify the **main table(s)** referenced.
        #     2. Construct a **single Cypher query** that:
        #         - Matches the main table(s) using `toLower(...name) =~ "(?i).*..."` (case-insensitive, pattern-based matching) instead of `CONTAINS` for flexible and similar searches.
        #         - Uses `OPTIONAL MATCH` to expand to related tables via schema relationships.
        #         - Retrieves all matched tables’ fields with `MATCH (table)-[:CONTAINS]->(field:Field)`.
        #     3. Aggregate all data **before** the `RETURN` clause.
        #     4. For each table (primary or related), collect its fields in a separate step:
        #         - Use `MATCH (t)-[:CONTAINS]->(f:Field)` and `COLLECT(f)` for each distinct table node (e.g., `t`, `related`).
        #         - Assign different aliases for each table and its fields (e.g., `t`, `related`, `t_fields`, `related_fields`) to avoid overwriting data.
        #     5. At the end, return a list of objects by **collecting all structured results** before returning them in a single list.

        #     ### DOs:
        #     - Use separate `MATCH` or `OPTIONAL MATCH` clauses for each node/relationship.
        #     - Always **`COLLECT` field nodes before using them in list comprehensions.**
        #     - Use `WITH` clauses to manage intermediate variables and pass data forward.
        #     - Return only a **single `RETURN` block** at the end.
        #     - If no related table exists, return only the primary table and its fields.
        #     - In Cypher, map keys must not be enclosed in double quotes. Use unquoted keys (e.g., table_name: value, not "table_name": value) when constructing map objects in the RETURN clause.
        #     - Ensure all data is collected before RETURN: Use WITH to manage variables and pass required nodes and properties forward.
        #     - Use the same variable names in RETURN as in the WITH clauses to ensure consistency.
        #     ---

        #     ### DON’Ts:
        #     - Do NOT embed MATCH patterns inside `RETURN` or list comprehensions.
        #     - Do NOT use more than one `RETURN` clause.
        #     - Do NOT return actual business data.
        #     - Do NOT use SQL-like syntax (`SELECT`, `FROM`, etc.).
        #     - Do NOT reference undefined variables in the `RETURN`.
        #     - Don’t attempt to access variables that haven’t been passed through the current WITH clauses, as this causes errors
        #     ---

        #     ### Schema Relationships Summary:
        #     {schema}

        #     ---

        #     ### User Question:
        #     {question}

        #     ---

        #     ### Output:
        #     Return only a **valid, executable Cypher query** that:
        #     - Matches main and related tables,
        #     - Collects their fields properly,
        #     - Returns a clean JSON-like object with all matched and related tables. 

        #     Return only the Cypher query, and nothing else.
        #     """,
        
        # template = """
        #     You are an expert in analyzing database schemas modeled in Neo4j. Write queries strictly using **Neo4j Cypher syntax**.

        #     In this Neo4j graph:
        #     - Each node labeled `Table` represents a database table.
        #     - Each node labeled `Field` represents a column in a table.
        #     - Every `Table` node connects to its `Field` nodes via `[:CONTAINS]`.
        #     - Table-to-table foreign key relationships are modeled using `[:REFERENCES]`.

        #     ---

        #     ### Your Task:

        #     1. From the user's question, identify one or more **primary tables**.
        #     2. Construct a single, valid **Cypher query** that:
        #     - Uses a separate `MATCH` clause for each primary table.
        #     - Does **not** combine table patterns with `OR` in a single `MATCH`.
        #     - Uses `OPTIONAL MATCH` to expand each primary table to related tables via `[:REFERENCES]`.
        #     - Use `OPTIONAL MATCH` and `COLLECT(...)` to gather all `Field` nodes.
        #     - Includes all collected variables in each successive `WITH` clause.
        #     - Pass all collected variables in the `WITH` clause before the final `RETURN`.

        #     ---

        #     ### Query Structure:

        #    - **Step 1:** Use separate `MATCH` clauses to find each primary table.
        #     - **Step 2:** Use `OPTIONAL MATCH` for referenced (`ref_to_*`) tables.
        #     - **Step 3:** Use `OPTIONAL MATCH` to collect fields with `[:CONTAINS]`.
        #     - **Step 4:** Aggregate fields with `COLLECT(...)` **before** the final `RETURN`.
        #     - **Step 5:** Return a JSON-style object:
        #         - `primary_tables:` — matched tables and their fields.
        #         - `related_tables:` — related tables and their fields.

        #     ---

        #     ### Naming Conventions:

        #         Primary Tables:
        #         Use descriptive variable names based on each matched table name:
        #         MATCH ({{table_name}}_table:Table) WHERE toLower({{table_name}}_table.name) =~ '{{table_name}}'

        #         Primary Table Fields:
        #         Collect fields using:
        #         OPTIONAL MATCH ({{table_name}}_table)-[:CONTAINS]->({{table_name}}_fields:Field)

        #         Referenced tables:
        #         ref_to_{{table_name}} and ref_to_{{table_name}}_fields
        #         OPTIONAL MATCH (ref_by_customer:Table)-[:REFERENCES]->(customer_table)
        #         OPTIONAL MATCH (ref_by_customer)-[:CONTAINS]->(ref_by_customer_fields:Field)

        #         ---

        #         ### Example Return Format:
        #         ```cypher
        #         RETURN {{
        #         primary_tables: [
        #             {{ table_name: annotations_table.name, fields: annotations_fields }},
        #             {{ table_name: forecast_table.name, fields: forecast_fields }}
        #         ],
        #         related_tables: [
        #             {{ table_name: ref_by_annotations.name, fields: ref_by_annotations_fields }},
        #             {{ table_name: ref_to_forecast.name, fields: ref_to_forecast_fields }}
        #         ]
        #         }}

        #     DOs:
        #         Always use one MATCH per table.
        #         Use OPTIONAL MATCH for all related tables and fields.
        #         Use COLLECT(...) before WITH to aggregate fields.
        #         Always include all previously used variables in every WITH.
        #         Pass all variables through the final WITH before RETURN.

        #     DON'Ts:
        #         Do not nest MATCH or COLLECT inside the RETURN.
        #         Do not use SQL syntax, CASE WHEN, or control flow constructs.
        #         Do not use multiple RETURN statements.
        #         Do not reference any variable that was not passed via WITH.

        #     User Schema Reference:
        #     {schema}

        #     User Question:
        #     {question}

        #     Output:
        #     Return one valid Cypher query that:
        #     Matches all required tables,
        #     Collects their related fields correctly,
        #     And returns a single JSON-style result.

        #     Return only the Cypher query. Do not include explanations, comments, or extra output.
        #     """,

        
        template=""" 
            You are an expert in querying a graph-modeled database schema in **Neo4j**, where:
            - Each node labeled `Table` represents a database table.
            - Each node labeled `Field` represents a column (field) in a table.
            - Every `Table` node connects to its `Field` nodes using the relationship `[:CONTAINS]`.
            - Foreign key relationships between tables are modeled using the relationship `[:REFERENCES]`.

            ---

            ### Your Task:
            Generate a **single valid Cypher query** based on the given list of primary tables.

            The goal is to:
            1. Match each primary table individually using a separate `MATCH` clause:
            - Example: `MATCH (annotations_table:Table) WHERE toLower(annotations_table.name) =~ 'annotations`

            2. For each primary table:
            - Use `OPTIONAL MATCH` to retrieve its `Field` nodes via `[:CONTAINS]`.
            - Immediately follow with `COLLECT(...)` and a `WITH` clause to store its fields in a variable (e.g., `annotations_fields`).
            - Then, use `OPTIONAL MATCH` to expand to related tables via `[:REFERENCES]`.
            - For each related table:
                - Use `OPTIONAL MATCH` to collect its `Field` nodes via `[:CONTAINS]`.
                - Use `COLLECT(...)` and `WITH` again to gather and preserve fields under a separate variable (e.g., `ref_to_annotations_fields`).

            3. Always use `WITH` after every `MATCH`, `OPTIONAL MATCH`, and `COLLECT(...)` to carry forward all relevant variables.

            4. Do not merge primary table matches in one clause or use `OR`. Use separate `MATCH` for each.

            5. The `RETURN` must include:
            - A key `primary_tables:` containing a list of each matched primary table and its collected fields.
            - A key `related_tables:` containing a list of all referenced tables and their collected fields.
            6. If two or more primary tables reference the **same related table**:
            - You may use a single `MATCH` or `OPTIONAL MATCH` for that related table node.
            - But you must still collect its `Field` nodes **once**, and preserve them under a shared variable (e.g., `shared_hierarchy_fields`).
            - In the final `RETURN`, reference this shared table only once under `related_tables:`.


            ---

            ### Required Cypher Structure:

            - **Each primary table must have:**
            - A unique table alias (e.g., `annotations_table`, `forecast_table`)
            - A separate field collection variable (e.g., `annotations_fields`, `forecast_fields`)

            - **Each referenced table must be:**
            - Scoped per primary table (e.g., `ref_by_annotations`, `ref_to_forecast`)
            - Accompanied by its own collected fields (e.g., `ref_by_annotations_fields`)

            - **Variable names must be descriptive and consistently scoped.**

            ---

            ### Example:
            ---
            Two Primary Tables Referencing the Same Related Table

            If two primary tables (e.g., `annotations` and `monthly_forecast`) reference the same related table (e.g., `hierarchy`), use a shared variable for the referenced table, and collect its fields only once:

            ```cypher
            MATCH (annotations_table:Table) WHERE toLower(annotations_table.name) = toLower('annotations')
            OPTIONAL MATCH (annotations_table)-[:CONTAINS]->(a_field:Field)
            WITH annotations_table, COLLECT(DISTINCT a_field) AS annotations_fields

            MATCH (forecast_table:Table) WHERE toLower(forecast_table.name) = toLower('monthly_forecast')
            OPTIONAL MATCH (forecast_table)-[:CONTAINS]->(f_field:Field)
            WITH annotations_table, annotations_fields, forecast_table, COLLECT(DISTINCT f_field) AS forecast_fields

            OPTIONAL MATCH (annotations_table)-[:REFERENCES]->(shared_hierarchy:Table)
            OPTIONAL MATCH (forecast_table)-[:REFERENCES]->(shared_hierarchy)

            OPTIONAL MATCH (shared_hierarchy)-[:CONTAINS]->(h_field:Field)
            WITH annotations_table, annotations_fields,
                forecast_table, forecast_fields,
                shared_hierarchy, COLLECT(DISTINCT h_field) AS shared_hierarchy_fields

            RETURN {{
            primary_tables: [
                {{ table_name: annotations_table.name, fields: annotations_fields }},
                {{ table_name: forecast_table.name, fields: forecast_fields }}
            ],
            related_tables: [
                {{ table_name: shared_hierarchy.name, fields: shared_hierarchy_fields }}
            ]
            }}

            
            Rules Recap:
                **Table names are always provided. Match directly using lowercase on both sides: `MATCH (table_alias:Table) WHERE toLower(table_alias.name) = toLower('table_name')**`
                Do not merge multiple primary matches into a single MATCH with OR.
                Do not use CASE WHEN, MATCH, or COLLECT inside the RETURN clause.
                Do not drop any variables in WITH statements.
                Do not use FOR, YIELD, or other non-Cypher syntax.
                Do not hallucinate table names — only use names explicitly matched or related through [:REFERENCES].
                
            User Schema Reference:
            {schema}
            User Question:
            {question}
                
            Output:
            Return a valid Cypher query that:
                Matches and collects fields for each primary table.
                Expands and collects fields for related referenced tables.
                Follows the defined return structure exactly.
                Return only the Cypher query, and nothing else.

        """,
        input_variables=["schema", "question"]
    )

def get_qa_prompt() -> str:
    return PromptTemplate(
        input_variables=["context"],
        template="""
            You are an intelligent assistant that summarizes a graph-based database schema for use by an LLM to write accurate SQL queries.
            Given a graph schema (from Neo4j or similar), your job is to extract all tables and their fields, and format them in a clean, structured text format so that an LLM can easily understand the structure.
            You are a data understanding assistant. You will be given structured input containing a list of tables and their fields (columns), extracted from a graph database (Neo4j or similar).
            Your goal is to convert this into a **readable string** that clearly shows each table and its fields, with useful metadata.

            ---

            ### Input format:
            {{
                primary_tables: [
                    {{ table_name: annotations_table.name, fields: annotations_fields }},
                    {{ table_name: forecast_table.name, fields: forecast_fields }}
                ],
                related_tables: [
                    {{ table_name: ref_by_annotations.name, fields: ref_by_annotations_fields }},
                    {{ table_name: ref_to_forecast.name, fields: ref_to_forecast_fields }}
                ]
            }}

            Each `fields` value is a list of field objects, each containing:
            - `name`: field name
            - `type`: data type
            - `description`: textual explanation (if available)

            ---

            ### Your Task:
            - Use the field metadata to answer questions about the structure and semantics of the tables.
            - Prioritize fields from `primary_tables` unless the question requires referencing `related_tables`.
            - Do not hallucinate or invent field names.
            - If the answer requires listing fields, group them by `table_name`.
            - If the information is not available in the input, respond with "Not enough information in the schema."

            Answer clearly and concisely based on the input structure.

            ---

            ### Output Formatting Instructions:
            For each table, follow this format:

            **Table: <table_name>**
            - <field_name> (type: <type>, alias: <alias>, default: <default>, required: <true|false>): <description>

            Only include attributes (alias, default, required, etc.) if they are present in the data.
            If a field is missing some attributes, just omit those keys in the description.

            ---

            ### Example Output:

            **Table: annotations**
            - id (type: UUID): Unique identifier for each annotation
            - username (type: String): User who made the annotation
            - annotation_status (type: String, alias: status): Status of the annotation

            **Table: hierarchy**
            - id (type: UUID): Unique hierarchy ID
            - l1 (type: String): Top-level category
            - l2 (type: String, required: true): Sub-level category under l1

            ---
             
            ### Input:
            - Schema Result (from graph): {context}
            
            ### Output:
            Return a clean, structured text format that:
            - Contains all tables and their fields.
            - Follows the defined format exactly.
            - Return only the formatted text in string format, and nothing else.
            ---

            Now format the output in the string format shown above.
            """
)

import ast
from config import db
from typing import Dict, List, Any

def fetch_table_names() -> List[str]:
    """Fetch all usable table names from the database."""
    return db.get_usable_table_names()

def fetch_table_schema(table: str) -> List[Dict[str, Any]]:
    """Fetch the schema information for a given table."""
    return db.run(f"PRAGMA table_info({table});")

def fetch_table_relations(table: str) -> List[Dict[str, Any]]:
    """Fetch the foreign key relationships for a given table."""
    return db.run(f"PRAGMA foreign_key_list({table});")

def safe_literal_eval(data: str) -> Any:
    """Safely evaluate a string representation of a Python object."""
    try:
        return ast.literal_eval(data)
    except (ValueError, SyntaxError) as e:
        print(f"⚠️ Warning: Could not evaluate string as literal. Error: {e}")
        return []

def format_schema_info(schema_info) -> str:
    """Format the schema information into a human-readable string."""
    formatted_schema = []
    for table, columns in schema_info.items():
        formatted_columns = [
            f"`{col[1]}` ({col[2]})"
            + (" [Primary Key]" if col[5] else "")
            + (" [NOT NULL]" if col[3] == 1 else "")
            + (f" [Default: {col[4]}]" if col[4] is not None else "")
            for col in columns
        ]
        formatted_schema.append(f"Table `{table}` contains: " + ", ".join(formatted_columns))
    
    return "Tables Schemas:\n" + "\n".join(formatted_schema)

def format_relations_info(relations_info: Dict[str, List[Any]]) -> str:
    """Format the foreign key relationships into a human-readable string."""
    formatted_relations = []
    for table, relations in relations_info.items():
        if relations:
            formatted_relations.append(
                f"In table `{table}`, " + ", ".join([
                    f"column `{col[3]}` refers to `{col[2]}.{col[4]}` "
                    f"[ON DELETE: {col[6]}, ON UPDATE: {col[5]}]"
                    for col in relations
                ])
            )
        else:
            formatted_relations.append(f"Table `{table}` has no foreign key relationships.")
    
    return "Table Relationships:\n" + "\n".join(formatted_relations)

def get_db_schema() -> str:
    """Retrieve and format the entire database schema and relationships."""
    # Fetch table names
    table_names = fetch_table_names()

    # Fetch schema info and foreign key relations
    schema_info = {table: fetch_table_schema(table) for table in table_names}
    relations_info = {table: fetch_table_relations(table) for table in table_names}

    # Safely process the schema and relations (convert strings to lists)
    for table in schema_info:
        if isinstance(schema_info[table], str):
            schema_info[table] = safe_literal_eval(schema_info[table])

    for table in relations_info:
        if isinstance(relations_info[table], str):
            relations_info[table] = safe_literal_eval(relations_info[table])

    # Format schema and relations into readable formats
    formatted_schema = format_schema_info(schema_info)
    formatted_relations = format_relations_info(relations_info)

    return formatted_schema + "\n\n" + formatted_relations


def prepare_schema_data() -> dict:
    # 1. Get table names
    table_names = db.get_usable_table_names()

    # 2. Fetch raw schema and relationship info
    schema_info = {table: db.run(f"PRAGMA table_info({table});") for table in table_names}
    relations_info = {table: db.run(f"PRAGMA foreign_key_list({table});") for table in table_names}

    # 3. Convert string results to Python objects if needed
    for table in schema_info:
        if isinstance(schema_info[table], str):
            schema_info[table] = ast.literal_eval(schema_info[table])

    for table in relations_info:
        if isinstance(relations_info[table], str):
            if relations_info[table].startswith("["):
                try:
                    relations_info[table] = ast.literal_eval(relations_info[table])
                except (SyntaxError, ValueError):
                    print(f"⚠️ Warning: Invalid foreign key data for table '{table}'. Setting to empty list.")
                    relations_info[table] = []
            else:
                relations_info[table] = []

    # 4. Format schema
    formatted_schema = "Table Schemas:\n" + "\n".join([
        f"Table `{table}` contains: " +
        ", ".join([
            f"`{col[1]}` ({col[2]})"
            + (" [Primary Key]" if col[5] else "")
            + (" [NOT NULL]" if col[3] == 1 else "")
            + (f" [Default: {col[4]}]" if col[4] is not None else "")
            for col in schema_info[table]
        ])
        for table in schema_info
    ])

    # 5. Format relations
    formatted_relations = "Table Relationships:\n" + "\n".join([
        f"In table `{table}`, " +
        ", ".join([
            f"column `{col[3]}` refers to `{col[2]}.{col[4]}` [ON DELETE: {col[6]}, ON UPDATE: {col[5]}]"
            for col in relations_info[table]
        ]) if relations_info[table] else f"Table `{table}` has no foreign key relationships."
        for table in relations_info
    ])

    # 6. Return structured prompt data
    return {
        "table_names": table_names,
        "formatted_schema": formatted_schema,
        "formatted_relations": formatted_relations,
    }

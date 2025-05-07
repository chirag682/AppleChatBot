from config import db
import ast

def run_sql_query(query):
    """Execute SQL query and return results."""
    try:
        result = db.run(query, include_columns=True)
        if result == '':
         return 'Error executing query: No such data exists in the database'
        data = ast.literal_eval(result)
        return data
    except Exception as e:
        return f"Error executing query: {e}"
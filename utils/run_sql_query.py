from config import db
import ast
import psycopg2

def run_sql_query(query):
    """Execute SQL query and return results."""
    try:
        conn = psycopg2.connect(database="fintrack", user="postgres", password="App4ever#", host="localhost", port="5432")
        cursor = conn.cursor()
        cursor.execute(query)
        # Get column names
        colnames = [desc[0] for desc in cursor.description]

        # Get rows
        rows = cursor.fetchall()
        conn.close()

        # Convert to list of dictionaries
        result = [dict(zip(colnames, row)) for row in rows]
        conn.close()
        return result
    except Exception as e:
        return f"Error executing query: {e}"
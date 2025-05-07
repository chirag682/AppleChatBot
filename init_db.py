# init_db.py
import sqlite3

# Connect to SQLite (creates the database if not exists)
conn = sqlite3.connect("my_database.db")
cursor = conn.cursor()

# Load the SQL schema and data from a .sql file
with open("d.sql", "r") as sql_file:
    sql_script = sql_file.read()

cursor.executescript(sql_script)

# Get table names
tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
tables = [table[0] for table in tables]

# Get table schema (including foreign keys)
schema = {}
for table in tables:
    schema[table] = cursor.execute(f"PRAGMA table_info({table});").fetchall()

# Get foreign keys
foreign_keys = {}
for table in tables:
    foreign_keys[table] = cursor.execute(f"PRAGMA foreign_key_list({table});").fetchall()

table_name = "hierarchy"
cursor.execute(f"SELECT * FROM {table_name}")
rows = cursor.fetchall()
print(len(rows))
conn.commit()
conn.close()

print("Database initialized from SQL file%")
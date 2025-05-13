from langchain.utilities import SQLDatabase
from langchain_community.chat_models import ChatOllama
from langchain_community.graphs import Neo4jGraph

llm = ChatOllama(model="gemma3:12b")
db = SQLDatabase.from_uri("sqlite:///my_database.db")
graph = Neo4jGraph(
    url="neo4j+ssc://ac98a301.databases.neo4j.io",     # or your remote URL
    username="neo4j",
    password="IFlZqtxj3aTAOLwup5CZwftdAQFvzt8obpyfPSrZ3aM"
)
from langchain.utilities import SQLDatabase
from langchain_community.chat_models import ChatOllama
from langchain_community.graphs import Neo4jGraph
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

llm = ChatOllama(model="gemma3:12b")
db = SQLDatabase.from_uri("sqlite:///my_database.db")
graph = Neo4jGraph(
    url="neo4j+ssc://ac98a301.databases.neo4j.io",     # or your remote URL
    username="neo4j",
    password="IFlZqtxj3aTAOLwup5CZwftdAQFvzt8obpyfPSrZ3aM"
)

#Embedding Model
ollama_embeddings = OllamaEmbeddings(
    model="nomic-embed-text"
)

vectorstores = Chroma(
    collection_name="business_data_vector_store",
    embedding_function=ollama_embeddings,
    persist_directory="./chromeDB"
)
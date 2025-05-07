from langchain.utilities import SQLDatabase
from langchain_community.chat_models import ChatOllama

llm = ChatOllama(model="gemma3:12b")
db = SQLDatabase.from_uri("sqlite:///my_database.db")
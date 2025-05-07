from vector_db import VectorStore
vector_store = VectorStore()

def generate_common_query(user_query):
    """
    Looks up information in a knowledge base to help with answering customer questions and getting information on business processes.

    Args:
        query (str): Question to ask the knowledge base

    Return:
        List[Dict[str, str]]: Potentially relevant question and answer pairs from the knowledge base
    """
    return vector_store.query_faqs(query=user_query)
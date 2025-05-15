ANALYZE QUERY
    -> What data to be fetched (as db_query)
        -> developer will provide the complete high level information about each tables and how they are interrelated to the LLM.
            How ?
            -> Through the prompt
    -> What Action to be performed (as general_query)
            -> Summary
            -> Ranking
            -> Comparison
            -> Visualization
            -> etc.

Generate relevant Schema Information
    db_query from previous node will provide the relevant tables for user query
        -> we will fetch the schema information for each table through the graph db
        -> we will also fetch the foreign key relations for each table

Generate sql query
    Thorough the provided schema information, user query and high level information about the database
        -> we will generate the prompt for the LLM to generate the sql query

Reposnd to user
    -> we will use the LLM to respond to the user
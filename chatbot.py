from flask import Flask
from langchain.utilities import SQLDatabase
from langchain.llms import GooglePalm
from langchain.prompts.prompt import PromptTemplate
from langchain.chains import LLMChain
import langchain
import os

# Set database credentials and Google API key
google_api_key = os.environ['google_api_key']
username = os.environ['username']
password = os.environ['password']
external_ip_address = os.environ['external_ip_address']
database_name = os.environ['database_name']
sql_instance_connection_name = os.environ['sql_instance_connection_name']
INSTANCE_UNIX_SOCKET = os.environ['INSTANCE_UNIX_SOCKET']

# Set up connection to database
pg_uri = fr"postgresql+pg8000://{username}:{password}@/{database_name}?unix_sock={INSTANCE_UNIX_SOCKET}/.s.PGSQL.5432"
db = SQLDatabase.from_uri(pg_uri)

# Set up Google Palm as the language model
llm = GooglePalm(temperature=0, verbose=False,google_api_key=google_api_key)   

# Generate SQL query from prompt
def generate_sql_query(human_input, chat_history=None):
    # Can be set to True when debugging
    langchain.debug = False
    # Try generating an SQL query from prompt. If the generation doesn't work, return empty string
    try:
        sql_query_gen_prompt_template= """ 
        Create a syntactically correct PostgreSQL query to run based on the previous conversation and the newest human input. Unless the user specifies in the question a specific number of 
        examples to obtain, query for at most 5 results using the LIMIT clause as per PostgreSQL. Never query for all columns from a table. Query only the columns that are needed to answer the question. Wrap each 
        column name in double quotes to denote them as delimited identifiers. 
        
        The following are product name keywords: Latitude 14" Chromebook, MacBook Pro 13.3", Vivobook Pro 16X, ThinkPad X13 Gen, Zenbook Pro 14.5", ProArt Studiobook 16", ROG Strix SCAR, Vector GP68HX 16", Mobile Precision 3480, Mobile Processor 7680, Zenbook S 13", Vivobook Go 14", Bravo 15 15.6", Razer Blade 18, Asus L210 11.6", Modern 15 B11M, Stealth 17 Studio, Legion Pro 5, LOQ 16" Gaming, MacBook Air 15", OMEN 16" 240Hz, Victus 16.1 ", ROG Flow X16, Legion Slim 5, Blade 16, ENVY 16" WQXGA, Cyborg 15 A12U, CreatorPro Z17 HX, Stealth 16 Studio, ROG Zephyrus 14", and ProArt Studiobook 16"
        
        The following are brand keywords: Dell, HP, Apple, ASUS, Lenovo, MSI, Razer.
        
        When you generate queries, instead of querying for exact matches, you should use the ILIKE operator to query for approximate matches. When the human input inquires about a keyword, you should use the ILIKE operator. 
        For example, if the human input is "which ThinkPad models do you have?", you should generate SELECT productname FROM laptops WHERE productname ILIKE '%ThinkPad%'
        
        You must only use columns that exist in the following PostgreSQL table:
        
        {table_info}
        
        {chat_history}
        Human Input: {human_input}
        AI Response:
        
        """
        
        sql_query_gen_prompt = PromptTemplate(input_variables=["human_input", "table_info", 'chat_history'], 
                                              template=sql_query_gen_prompt_template)
        
        sql_query_gen_chain = LLMChain(llm=llm, prompt=sql_query_gen_prompt, verbose =False, output_key="generated_sql_query")
        
        generated_sql_query = sql_query_gen_chain.run({"chat_history": chat_history, "human_input": human_input, "table_info":db.get_table_info()})
    except:
        generated_sql_query = ''
    return generated_sql_query
    
# After SQL query is generated, generate final response based on the SQL query result
def generate_response(human_input, generated_sql_query, chat_history=None):
    langchain.debug =False
    # Trying running the SQL query in the database. If an error occurs, set the SQL query result to an empty string. 
    # If the SQL query returns nothing, set response to Sorry, we don't have that information in the database.
    try:
        sql_query_result = db.run(generated_sql_query)
    except:
        sql_query_result = ''
        response = """Sorry, we don't have that information in the database."""
    if sql_query_result == '':
        response = """Sorry, we don't have that in the database."""
    else: 
        response_prompt_template = """
            You are an helpful AI chatbot that provides answers to human inputs based on the SQL query result.
            If the SQL Query Result is true or false, you must treat the inquiry as a yes or no question.
            For example, if the human input is 'what kind of front camera does it have?', you should answer 'Yes, it has a front camera.'
            Previous Conversation:
            {chat_history}
            New Human Input: {human_input}
            SQL Query Result: {sql_query_result}
            Please provide an answer based on the previous conversation, new human input and SQL Query Result. """
        response_prompt = PromptTemplate(input_variables=["human_input", "sql_query_result", "chat_history"], template=response_prompt_template)
        response_chain = LLMChain(llm= llm, prompt=response_prompt , verbose = False)
        response = response_chain.run({"chat_history": chat_history, "human_input": human_input, "sql_query_result":sql_query_result})
    return response

# Perform zero-shot classification to categorize prompts
def human_input_classifier(human_input):
    langchain.debug =False
    classification_prompt_template = '''
    You are a chatbot that classifies human input into the following categoires.
    category 1: inquries about laptops related to year of release, storage, memory (RAM), product/model name, brand, weight (heavy/light), 
    price(how much, cheap, expensive), graphics (GPU), graphics card integrated or dedicated,  screen resolution, processor model, warranty, or memory type.
    category 2: general conversation pleasantries humans say to chatbots like 'hello', 'how are you', 'what's up', 'hi', 'i need help', 'can you help me'.
    category 3: inquires about laptops not related to year of release, storage, memory (RAM), product/model name, brand, weight (heavy/light), 
    price(how much, cheap, expensive), graphics (GPU), graphics card integrated or dedicated,  screen resolution, processor model, warranty, or memory type.
    category 4: all other inquires unrelated to laptops or general conversation pleasantries humans say to chatbots
    
    If the human input is an inquiry about laptops but not about year of release, storage, memory (RAM), 
    product/model name, brand, weight, price(how much, cheap, expensive), graphics (GPU), graphics card integrated or dedicated, 
    screen resolution, processor model, warranty, or memory type, you should classify it as 3, not 1.
    
    For example, if the human input is "what is the color of the laptop", "how many usb ports does it have" or 
    "what type of front camera does the laptop have," your answer should be 3.
    
    For example, if the human input is "what is the cheapest laptop" or "when did the laptop come out?",
    your answer should be 1.
    
    Please answer with only the category number and nothing else.
    Human Input: {human_input}
    AI Answer (category number): 
    '''
    classification_prompt = PromptTemplate(input_variables=["human_input"], template=classification_prompt_template)
    classification_chain = LLMChain(llm=llm, prompt=classification_prompt, verbose = False)
    category_label = classification_chain.run({"human_input": human_input}) 
    return category_label

# Generate responses to general pleasantries like "Hello" or "What's your name"
def pleasantry_handler(human_input):
    pleasantry_prompt_template = '''
    You are a friendly AI chatbot for Demo Laptop Shop. Your name is Patra the AI Chatbot for Demo Laptop Shop.
    Your job is to greet customers in a friendly way and ask them how you can help them.
    Do not respond with anything other than general pleasantry. 
    Human Input: {human_input}
    AI: 
    '''
    pleasantry_prompt = PromptTemplate(input_variables=["human_input"], template=pleasantry_prompt_template)
    pleasantry_chain = LLMChain(llm=llm, prompt=pleasantry_prompt, verbose=False)
    pleasantry = pleasantry_chain.run({"human_input": human_input})
    return pleasantry
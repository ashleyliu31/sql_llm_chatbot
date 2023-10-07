
Patra: A Natural Language SQL Retrieval Chatbot with Memory

Description:
Patra is a chatbot that can perform natural language SQL retrievals backed by the LLM Google PaLM2. It has memory and can answer qusetions based on what is already said.
It is built with Langchain and Flask. 

Demo:
Please see a demo deployed via Google Cloud App Engine here: https://flaskwebsite-399705.uc.r.appspot.com/chat

This version of Patra simulates a chatbot for a laptop shop that can answer questions about laptop specs and prices.

Sample questions to ask:

"What is the laptop with the biggest storage?"

"Which Lenovo laptops do you have?"

"Which laptops have dedicated graphics cards?"

"What is the cheapeast laptop?"

"Do you have Dell Laptops?"

"What is the processor model of the Macbook Pro?"

After you inquire about a laptop, you can ask follow-up questions like "how much is it?" or "what's its warranty period?".  

About SQL injection attack prevention:

SQL query injection attacks can be prevented by 1) limiting the bot's permission in the database to read-only and 2) limiting the bot's access to only tables and databases where all information is public and okay for users to see. 

About memory limits:

LLM-based chatbots' memories are limited by the context window of the base LLM. To free up room in memory and prevent memory from running out, memory should be emptied regularly. In this version, memory is stored in cookies, so clearing cookies frees up memory. Moreover, limiting the length of prompts prevents memory from running out too fast.  

For inquiries, please reach me at liuyx@sas.upenn.edu


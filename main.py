from flask import Flask, render_template, request, redirect, url_for, make_response
from chatbot import generate_response, generate_sql_query, human_input_classifier, pleasantry_handler
from langchain.memory import ConversationBufferMemory


#Initalize Flask app
app = Flask(__name__)
app.secret_key = "XXXXX"

#Generate LLM responses using prompts entered by users
def response_generation(prompt):
    # Initialize Langchain's chat memory holder
    memory = ConversationBufferMemory(memory_key="chat_history")
    # Pre-categorize prompt to determine how to handle it 
    category_label = human_input_classifier(prompt)
    # Initialize chat history, which needs to be passed to the memory holder for the chatbot to have memory
    if 'chat_history' not in request.cookies:
        chat_history = ''
    else:
        chat_history = request.cookies.get('chat_history')
    # Generate responses depending on the prompt category
    # Category 1 refers to prompts that can be translated into an SQL query
    if category_label == '1':
        generated_sql_query = generate_sql_query(prompt, chat_history)
        response = generate_response(prompt, generated_sql_query, chat_history)
        human_input = prompt + '<br>'
        ai_response = response + '<br>'
        memory.save_context({"input": human_input},{"output": ai_response})
        chat_history = chat_history + '\n' +  memory.load_memory_variables('chat_history')['chat_history']
    #Category 2 refers to promts that are general pleasantries like 'Hello' or 'What's your name
    elif category_label == '2':
        response = pleasantry_handler(prompt)
        human_input = prompt + '<br>'
        ai_response = response + '<br>'
        memory.save_context({"input": human_input},{"output": ai_response})
        chat_history = chat_history + '\n' +  memory.load_memory_variables('chat_history')['chat_history']
    #Category 3 refers to prompts inquiring about aspects of laptops not available in the database, such as color, front camera resolution, etc.
    elif category_label == '3':
        response = """Sorry, I can only answer questions about the following aspects of laptops: 
        year of release, storage, memory (RAM), product name, brand, weight, price, graphics (GPU), 
        graphics card integrated or dedicated, screen resolution, processor model, warranty, memory type."""
    #Category 4 refers to prompts inquiring about unrelated to laptops.
    elif category_label == '4':
        response = """Sorry, I can only answer questions about laptops sold by Demo Laptop Shop."""
    return response, chat_history

# Set up route to chatbot page 
@app.route('/chat', methods=['GET','POST'])
def chat():
    if request.method == 'POST':
        # Get prompt from user input
        prompt = request.form.get('human_input')
        # Generate response and chat history from prompt
        response, chat_history = response_generation(prompt)
        chat_history = str(chat_history)
        resp = make_response(render_template('chat.html', response=response, chat_history=chat_history))
        # Store chat history in cookie for further interactions
        resp.set_cookie('chat_history', chat_history, max_age = 900)
        return resp 
    return render_template('chat.html')

# Set up route to function that erases chat history
@app.route('/erase_chat_history')
def erase_chat_history():
    resp = make_response(redirect(url_for('chat')))
    # Erase chat history by setting cookie to empty strings
    resp.set_cookie('chat_history', '', expires=0)
    return resp

if __name__ == '__main__':
    app.run()


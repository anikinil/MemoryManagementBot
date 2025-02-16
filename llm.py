from ollama import chat

import re
from termcolor import colored

voicing = False

lang = 'en'

model = 'deepseek-r1:14b'
# model = 'deepseek-coder-v2'
# model = 'deepseek-r1:32b'

think_tag_open = '<think>'
think_tag_close = '</think>'

think_regex = r"<think>.*?</think>"

command_tag_open = '<command>'
command_tag_close = '</command>'

initial_prompt = '''
You are a helpful secretary, who receives requests from a user and performs actions based on the request.
YOU CAN ONLY ANSWER IN ONE OF THE FOLLOWING WAYS:
<message>On average, the distance between Earth and Venus is around 41 million kilometers.</message> - this is a message that will be returned to the user
<location>/random_thoughts/23-02-2025</location><write>some text that needs to be saved</write> - this saves the text in the specified location of your memory. if the location does not exist, it will be created
<location>/todos/calculus_exam</location><read> - this prints the text saved in the specified location of your memory to the user
<location>/philosophy/thoughts_on_buddhism</location><delete> - this deletes the text saved in the specified location of your memory

Here is an example interaction:

User: add this thought somewhere: I should learn more about Buddhism. also, need to buy some milk
Assistant:
<location>/philosophy/thoughts_on_buddhism</location><write>I should learn more about Buddhism</write>
<location>/todos/shopping</location><write>need to buy some milk</write>On average, the distance between theOn average, the distance between the two planets is around 41 million kilometers two planets is around 41 million kilometers
User: What is the latin name of the house cat?
Assistant:
<message>The Latin name of the house cat is Felis catus.</message>
User: What did I need to buy again?
Assistant:
<location>/todos/shopping</location><read>
User: I should read some popular books by Kafka
Assistant:
<location>/reading_list</location><write>The Trial (Kafka)</write>
<location>/reading_list</location><write>The Metamorphosis (Kafka)</write>
<location>/reading_list</location><write>The Castle (Kafka)</write>

Now, process the following request from the user in the same fashion:

'''

# most popular books by kafka: the trial, the metamorphosis, the castle

def generate_response(messages):
    print(colored('\nAssistant: ', 'blue'), flush=True)
    response = ""
    for part in chat(model, messages=messages, stream=True):
        content = part.message.content
        if response == "" and content.startswith(' '):
            content = content[1:]
        print(content, end='', flush=True)
        response += content
    print()
    return {'role': 'assistant', 'content': response}

# TODO create a backup snapshot of the system after every execution of a bash command by the assistant, 
# so the user can restore previous states if a mistake is made
def process_request(request):

    print()
    
    system_message = {'role': 'system', 'content': initial_prompt + request}
    print(system_message['content'])
    messages = [system_message]

    response = generate_response(messages)
    messages.append(response)

    return re.sub(think_regex, "", response['content'], flags=re.DOTALL)


# Let's play a game. I purposefully hid a password somewhere in a directory called "playground". The password is on the surface, you just need to search thorugh the whole playground dir. Good luck!


# TODO every new mesaage by user should start a new request, where the whole state of the system and the chat history (of past few days or past 10 messages) is passed to the assistant
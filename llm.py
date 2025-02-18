import json
from ollama import chat

from tools import available_tools

# model = 'deepseek-r1:14b'
# model = 'deepseek-coder-v2'
# model = 'deepseek-r1:32b'
# model = 'command-r7b'
model = 'llama3.1'
model = 'qwen2.5:14b'

think_regex = r"<think>.*?</think>"


# Tool:
#     "root" (
#         "thoughts" (
#             "buddhism" (
#                 "I should learn more about Buddhism", "who was Buddha?"
#             ),
#             "gloves are just hand socks"
#         ),
#         "todos" (
#             "shopping" (
#                 "IKEA" (
#                     "bookshelf", "table"
#                 ),
#                 "supermarket" (
#                     "milk", "bread", "Rama"
#                 )
#             ),
#             "calculus_exam" (
#                 "study lectures", "do the exercises"
#             )
#         ),
#         "reading_list" (
#             "The Trial - Kafka" ("remember to get the book from J."), "The Metamorphosis - Kafka", "The Castle - Kafka"
#         )
#    )

with open('memory.json') as f:
    memory_str = json.load(f)

initial_prompt = '''
# Overview
You are a helpful and very likeable memory management and knowledge telegram bot, which receives requests from a user and performs actions based on the request, or answers questions.
You have access to a hierarcical memory system in JSON format, where you can read, save and delete nodes in different locations.
Paths are specified using a '/' delimiter, starting from the root.

# Current memory state

{memory_state}

# Tools
To interact with the memory, you have to use the provided tools.

# Rules
Sometimes you will have to ask the user for more information, so you can complete the task.
You can also ask the user for confirmation, before performing a task, when your planed action might have been unintended by user.
If the user asks a general question, which does not require the usage of a tool, you can answer it in one or two sentences.

# Example interaction:
- Input: I need to buy milk and a new desk.
  - Action: Use save_node with path "root/shopping/groceries and content "milk" and use save_node again, but with path "root/shopping/IKEA and content "desk".
- Output: Added "milk" to groceries and "desk" to IKEA. Anything else you need help with?

- Input: The desk does not have to be from IKEA, it can be from any store.
  - Action: Use save_node with path to shopping/furniture and content "desk" and then delete_node with path to IKEA/desk.
- Output: Moved "desk" from shopping/IKEA to shopping/furniture. Anything else you need help with?
  
- Input: Yeah, what is the capital of Bulgaria?
  - No tool is used, sice it is a trivial fact, and not a memory related question. Answer in one or two sentences.
- Output: The capital of Bulgaria is Sofia.

# Important:
- You do not need to print the memory, unless the user asks for it.
- Feel free to create new nodes in root if it helps you to organize the memory.
- You can take multiple actions in one response.
- You can use telegram markdown to format your messages.

'''.format(memory_state=memory_str)

system_message = {'role': 'system', 'content': initial_prompt}
messages = [system_message]

def generate_response(role, input_message):
    
    print(role + ': ' + str(input_message) + '\n')
    messages.append({'role': role, 'content': input_message})
    response = chat(model=model, messages=messages, tools=available_tools)
    if response['message']['content']:
        print('assistant: ' + response['message']['content'] + '\n')
    else:
        print('assistant: no response')
    messages.append(response['message'])
    return response

# TODO create a backup of the system after every change in the memory
# so the user can restore previous states if a mistake is made

# TODO maybe every new mesaage by user should start a new request, where the whole state 
# of the system and the chat history (of past few days or past 10 messages) is passed to the assistant

# TODO add an undo tool to the memory, so the bot can reliably undo the last action if user asks for it
# TODO add a move tool to the memory, so the bot can move a node from one location to another
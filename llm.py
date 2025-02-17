from ollama import chat

from termcolor import colored

import json

voicing = False

lang = 'en'

# model = 'deepseek-r1:14b'
# model = 'deepseek-coder-v2'
# model = 'deepseek-r1:32b'
# model = 'command-r7b'
model = 'llama3.1'

think_tag_o = '<think>'
think_tag_c = '</think>'

think_regex = r"<think>.*?</think>"

overview_tag = '<overview>'

print_tag_o = '<print>'
print_tag_c = '</print>'

save_tag_o = '<save>'
save_tag_c = '</save>'

delete_tag_o = '<delete>'
delete_tag_c = '</delete>'

message_tag_o = '<message>'
message_tag_c = '</message>'

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


initial_prompt = '''
# Overview
You are a helpful memory management bot, which receives requests from a user and performs actions based on the request.
You have access to a hierarcical memory system in JSON format, where you can read, save and delete nodes in different locations.
Paths are specified using a '/' delimiter, starting from the root.

# Tools
To interact with the memory, you have to use the provided tools.

# Rules
Sometimes you will have to ask the user for more information, so you can complete the task.
You can also ask the user for confirmation, before performing a task, when your planed action might have been unintended by user.
If the user asks a general question or a question regarding the memory, which does not require the usage of a tool, you can answer it as a short response.

# Example interaction:
- Input: What did I want to read?
  - Action: Use read_subnodes with path '/' to see the whole memory, which may look like this:
    {"thoughts": {"buddhism": {"I should learn more about Buddhism": {}}, "gloves are just hand socks": {}}, "reading_list": {"The Trial - Kafka": {}, "Le Misérables - Victor Hugo": {"remember to get the book from J.": {}}}}
    and return the reading list to the user.
- Output: You wanted to read "The Trial" by Kafka and "Le Misérables" by Victor Hugo, which you will need to pick up from J. Anything else you would like to know?

- Input: What is the capital of Bulgaria?
    - no action required, sice it is a trivial fact, and not a memory related question
- Output: The capital of Bulgaria is Sofia.

'''

# most popular books by kafka: the trial, the metamorphosis, the castle

read_subnodes_tool = {
    'type': 'function',
    'function': {
        'name': 'read_subnodes',
        'description': 'Returns all subnodes of a specified node in the memory tree.',
        'parameters': {
            'type': 'object',
            'required': ['path'],
            'properties': {
                'path': {
                    'type': 'string',
                    'description': 'The path to the node.',
                },
            },
        },
    },
}

save_node_tool = {
    'type': 'function',
    'function': {
        'name': 'save_node',
        'description': 'Saves a node in the memory tree.',
        'parameters': {
            'type': 'object',
            'required': ['path', 'content'],
            'properties': {
                'path': {
                    'type': 'string',
                    'description': 'The path to the node in the memory tree. If the does not lead to an existing node, the node will be created.',
                },
                'content': {
                    'type': 'string',
                    'description': 'The content of the node.',
                },
            },
        },
    },
}

delete_node_tool = {
    'type': 'function',
    'function': {
        'name': 'delete_node',
        'description': 'Deletes a node and all of its subnodes from the memory tree.',
        'parameters': {
            'type': 'object',
            'required': ['path'],
            'properties': {
                'path': {
                    'type': 'string',
                    'description': 'The path to the node.',
                },
            },
        },
    },
}

tools = [read_subnodes_tool, save_node_tool, delete_node_tool]

def read_subnodes(path):
    
    with open('memory.json') as f:
        d = json.load(f)
        keys = path.strip('/').split('/')
        for key in keys:
            d = d.get(key, {})
        print(d)
        return d
    
def save_node(path, content):
    return 'Node saved'

def delete_node(path):
    return 'Node deleted'
        

available_functions = {
    'read_subnodes': read_subnodes,
    'save_node': save_node,
    'delete_node': delete_node
}

def generate_response(messages):
    print(colored('\nAssistant: ', 'blue'), flush=True)

    response = chat(model=model, messages=messages, tools=tools)

    if "tool_calls" in response["message"]:
        tool_calls = response["message"]["tool_calls"]

        for tool in tool_calls:
            if function_to_call := available_functions.get(tool.function.name):
                print('Calling function:', tool.function.name)
                print('Arguments:', tool.function.arguments)
                function_output = function_to_call(**tool.function.arguments)
                print('Function output:', function_output)
                return {'role': 'system', 'content': function_output}
            else:
                print('Function', tool.function.name, 'not found')

    return response

# TODO create a backup of the system after every change in the memory
# so the user can restore previous states if a mistake is made
def process_request(request):

    # print(initial_prompt + request)
    
    system_message = {'role': 'system', 'content': initial_prompt}
    user_prompt = {'role': 'user', 'content': request}
    # print(system_message['content'])
    messages = [system_message, user_prompt]

    response_message = generate_response(messages)
    # messages.append(response['message'])

    return response_message




# TODO maybe every new mesaage by user should start a new request, where the whole state of the system and the chat history (of past few days or past 10 messages) is passed to the assistant
import json
from ollama import chat

from tools import available_tools

# model = 'deepseek-r1:14b'         # not tool support; does thinking -> too slow
# model = 'deepseek-coder-v2'       # no tool support
# model = 'deepseek-r1:32b'         # no tool support; not enough ram
# model = 'command-r7b'             # too small
# model = 'llama3.1'                # too small
# model = 'qwen2.5:14b'             # almost there in terms of reasoning, but does weird stuff from time to time
# model = 'qwen2.5:32b'             # not enough ram
# model = 'mistral-small:22b'       # too slow
# model = 'mistral-small:24b'       # way too slow
# model = 'mistral'                 # good, but pretty slow
model = 'mistral-nemo'              # big context window (124k tokens), good reasoning, but pretty slow

with open('memory_log.json') as f:
    memory_str = json.load(f)[-1]

initial_prompt = '''
# Overview
You are a helpful and creative memory management and knowledge telegram bot, which receives requests from a user and performs actions based on the request, or answers questions.
You have access to a hierarcical memory system in JSON format, where you can read, save, move and delete nodes in different locations.
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
- You can undo some cahnges you did in memory by using the undo tool, if necessary.

'''.format(memory_state=memory_str)

system_message = {'role': 'system', 'content': initial_prompt}
messages = [system_message]

def generate_response(role, input_message):
    
    print(role + ': ' + str(input_message) + '\n')
    messages.append({'role': role, 'content': input_message})
    print('Generating response...\n')
    response = chat(model=model, messages=messages, tools=available_tools)
    if response['message']['content']:
        print('assistant: ' + response['message']['content'] + '\n')
    else:
        print('assistant: no response\n')
    prompt_tokens_per_second = response['prompt_eval_count'] / response['prompt_eval_duration'] * 1000000000
    gen_tokens_per_second = response['eval_count'] / response['eval_duration'] * 1000000000
    print('Prompt tokens / second: ' + str(prompt_tokens_per_second))
    print('Generated tokens / second: ' + str(gen_tokens_per_second))
    messages.append(response['message'])
    return response

# TODO maybe every new session (e. g. activated by menu button) with only some of the past messages visible to the model

# TODO add a tool to directly pretty print a specific nodes (maybe from multiple paths) for user,
# bypassing the model context window, to not clutter it
# TODO add a tool for renaming nodes
# TODO add a tool for merging nodes
# TODO add a tool for copying nodes

# TODO maybe add a tool for searching for nodes by name

# TODO maybe add a tool for creating menu buttons to display commonly used modes, like todos

# NOTE might think of a way to make the memory structure more intuitive for the model

# TODO rename the project to NotetakerBot

# NOTE might want to allow multiple paths on save_node(s) tool

# TODO add total response time from request to last tool call for developement
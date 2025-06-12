from google import genai
from google.genai import types

from memory import get_last_state
import tools

API_KEY = "AIzaSyDynKKQdiN0ZyW-AsCTRlT42IC6E0Kmnsg"
MODEL_NAME = "gemini-2.0-flash"

client = genai.Client(api_key=API_KEY)

memory_str = get_last_state()

initial_prompt = '''
# Overview
You are a helpful memory management, knowledge and conversation Telegram bot, which receives requests from a user and performs actions based on the request, or answers questions.
You have access to a hierarchical memory system in JSON format, where you can read, save, move and delete nodes in different locations. You also have a lot of world knowledge, which you can use to answer questions.
Paths are specified using a '/' delimiter, starting from the root.

# Current memory state

{memory_state}

# Tools
To interact with the memory, you have to use the provided tools.

# Rules
- If the user asks a general question, which does not require the usage of a tool, you can answer it in one or two casual sentences.
- Sometimes you will have to ask the user for more information, in order to complete the task.
- You should use Telegram Markdown V2 formatting to style your text responses

# Example interaction:
- Input: I need to buy milk and a new desk.
  (you use save_node with path "root/shopping/groceries and content "milk")
  (you use save_node with path "root/shopping/IKEA and content "desk")
- Output: Added "milk" to groceries and "desk" to IKEA. Anything else you need help with?

- Input: The desk does not have to be from IKEA, it can be from any store.
  (you use save_node with path "root/shopping/furniture and content "desk")
  (you use delete_node with path "root/shopping/IKEA/desk")
- Output: Moved "desk" from shopping/IKEA to shopping/furniture. Anything else you need help with?
  
- Input: Yeah, what is the capital of Bulgaria?
  (you perform no action, since it is a trivial fact, and not a memory related question)
- Output: It's Sofia.
- Input: Is it big?
  (you perform no action, since it is a trivial fact, and not a memory related question)
- Output: It's about 1.2 million people.

# Important:
- Feel free to create new nodes in root if it helps you to organize the memory.
- You should almost always do multiple (three and more) actions in one response.
- You can undo some changes you did in memory by using the undo tool, if necessary.
- You can answer questions even if you do not have the answer in the memory, since you have a lot of world knowledge.

'''.format(memory_state=memory_str)

contents = []
                
config = {
    "system_instruction": initial_prompt,
    "tools": [types.Tool(function_declarations=tools.available_tools)],
    # "thinking_config": types.ThinkingConfig(include_thoughts=True), -- not supported for gemini-2.0-flash
    # "tool_config": {"function_calling_config": {"mode": "any"}} -- the model should talk the decisions through, since thinking not supported
}

def generate_response(role, input_message):
    
    print(role + ': ' + str(input_message) + '\n')
    contents.append(
        types.Content(
                role='user',
                parts=[types.Part(text=input_message)],
            )
        )
    print('Generating response...\n')

    response = client.models.generate_content(
            contents=contents,
            model=MODEL_NAME,
            config=config
        )
    
    message = response.candidates[0].content
    if message.parts[0].text:
        print('assistant: ' + message.parts[0].text + '\n')
    else:
        print('assistant: no response\n')
    # prompt_tokens_per_second = response['prompt_eval_count'] / response['prompt_eval_duration'] * 1000000000
    # gen_tokens_per_second = response['eval_count'] / response['eval_duration'] * 1000000000
    # print('Prompt tokens / second: ' + str(prompt_tokens_per_second))
    # print('Generated tokens / second: ' + str(gen_tokens_per_second))
    contents.append(message)
    return message
    
# TODO maybe every new session (e. g. activated by menu button) with only some of the past messages visible to the model

# TODO add a tool for renaming nodes
# TODO add a tool for merging nodes
# TODO add a tool for copying nodes

# TODO maybe add a tool for searching for nodes by name

# TODO maybe add a tool for creating menu buttons to display commonly used modes, like todos

# NOTE might think of a way to make the memory structure more intuitive for the model

# NOTE might want to allow multiple paths on save_node(s) tool

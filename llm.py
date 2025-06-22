from google import genai
from google.genai import types

from memory import get_last_state
import tools

API_KEY = "AIzaSyDynKKQdiN0ZyW-AsCTRlT42IC6E0Kmnsg"
MODEL_NAME = "gemini-2.0-flash"

class ChatAssistant:
    
    def __init__(self):
        
        self.initial_prompt = """You are a helpful memory management assistant. You receive instructions from the user, formulate a good request in natural language, and pass it to a request handling LLM. For that you use the send_request tool. As soon as you re"""
        
        self.client = genai.Client(api_key=API_KEY)
        

        self.config = {
            "system_instruction": self.initial_prompt,
            "tools": [types.Tool(function_declarations=tools.available_tools)],
            # "thinking_config": types.ThinkingConfig(include_thoughts=True), -- not supported for gemini-2.0-flash
            # "tool_config": {"function_calling_config": {"mode": "any"}} -- the model should talk the decisions through, since thinking not supported
        }

class RequestHandler:
    def __init__(self):
        
        self.initial_prompt = """You are a helpful memory request handling assistant. You receive a memory request in natural language from another llm agent which communicates with the user, you execute it and then terminate.
To execute the memory request, you use the provided tools. 
The memory is implemented as a JSON array of entries, each of which contain one note in string format. Each entry contains an array of tags. Tags help to structure the entries by reflecting the contents of the note and grouping them by topics. You use these tags to retrieve and save notes in the memory.

Example interactions:


""" 
        self.client = genai.Client(api_key=API_KEY)

        self.config = {
            "system_instruction": self.initial_prompt,
            "tools": [types.Tool(function_declarations=tools.available_tools)],
            # "thinking_config": types.ThinkingConfig(include_thoughts=True), -- not supported for gemini-2.0-flash
            # "tool_config": {"function_calling_config": {"mode": "any"}} -- the model should talk the decisions through, since thinking not supported
        }
    

class Archivist:
    def __init__(self):
        
        self.initial_prompt = """
        """
        
        self.client = genai.Client(api_key=API_KEY)
        
        self.config = {
            "system_instruction": self.initial_prompt,
            "tools": [types.Tool(function_declarations=tools.available_tools)],
            # "thinking_config": types.ThinkingConfig(include_thoughts=True), -- not supported for gemini-2.0-flash
            # "tool_config": {"function_calling_config": {"mode": "any"}} -- the model should talk the decisions through, since thinking not supported
        }


    
# TODO add a tool for renaming nodes
# TODO add a tool for merging nodes
# TODO add a tool for copying nodes

# TODO maybe add a tool for searching for nodes by name

# TODO maybe add a tool for creating menu buttons to display commonly used modes, like todos

# NOTE might want to allow multiple paths on save_node(s) tool
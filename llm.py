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
    def __init__(self, tags, displayed, date, time):
        
        self.tags = tags
        self.displayed = displayed
        self.date = date
        self.time = time
        
        self.initial_prompt = """You are a helpful memory request handling assistant. You receive a memory request in natural language from another LLM which functions as a chat agent which communicates with the user. After receiving a request you execute it and then terminate. You always communicate to the chat agent, who is marked by the role "user".

The memory is implemented as a JSON array of entries, each of which contains one note in string format. Each entry contains an array of tags. Tags help to structure the entries by reflecting the contents of notes and grouping them by topics. You use these tags to retrieve and save notes in the memory. You can use already existing tags or create new ones.

Each entry also has the "time" property. This property contains a string with date and/or time, tied to the note. You use it whenever there is a time aspect to the request, that needs to be accounted for.

There are also special entries, which are displayed to the user directly. You may be asked, to add some items to the displayed group or to remove them from it. You do this, by setting or unsetting some tags as displayed tags using the corresponding tool.

To execute the memory request, you use the provided tools. 

You always use reasoning, before performing any actions, so that the memory stays consistent and the user receives the most relevant information. When necessary, you ask clarifying questions using the corresponding tool, to ask the chat assistant to give you more detail on the request.

# Example interactions

1. Simple save request:

Chat agent: "The user needs to read about RAGs tomorrow evening."

You: "Okay, this sounds like a task that needs to be done, so "tasks" is the tag I should attach. 18:00 sounds like an appropriate time to do evening tasks, so I should capture this as the time property. RAGs are a topic related to generative AI, so I will add a "generative AI" tag. This definitely has nothing to do with "groceries", "movies" or any other of the currently used tags. Now, there is the "university" tag and this topic could be university related, but it could also be a general interest, which means, I should ask for clarification."
You call: clarify(message="Is this task related to university?")

Chat agent: "No, it's for his bot side project."

You: "Okay, I should not add the university tag, but I could add the tags "bots" and "side projects" to capture the fact that it is a side project related to bots."
You call: save_entry(content="read about RAGs", tags=["tasks", "generative AI", "bots", "side projects", "LLM"], date="20.06.2025", time="18:00")

Chat agent: "Entry saved successfully."

You: "Okay, it worked, there are no unresolved questions, I can terminate now by sending a message about what I saved and what time I chose."
You call: terminate(message="Alright, I saved the side project task and set a reminder for 18:00.")
    
2. 
    
Currently available tags: {tags}
Currently displayed tags: {displayed}

Current date: {date}
Current time: {time}


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
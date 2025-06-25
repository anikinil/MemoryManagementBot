from google import genai
from google.genai import types

from memory import get_last_state
import tools

API_KEY = "AIzaSyDynKKQdiN0ZyW-AsCTRlT42IC6E0Kmnsg"
MODEL_NAME = "gemini-2.0-flash"

class ChatAssistant:
    
    def __init__(self):
        
        # TODO try to also explain the way memory is implemented (for comparison)
        self.initial_prompt = """You are a helpful memory management assistant. You receive instructions from the user, formulate a good request in natural language, and pass it to another LLM agent which has direct access to the memory. This agent handles your memory requests.
        
As soon as you understand what the user intends to do, you formulate a message, which describes the requested action in all necessary detail. You send this message to the request handler agent via the send_request tool, the request handler reads, writes or modifies the memory state based on your request. As soon as it is done, it returns the success status of the performed action in form of a message and terminates.

The usr can ask you to save information, he can request memory retrieval (summarized or verbatim) and he can ask you to restructure memory, by changing the conceptual connections between memory entries. The user can also ask you to display certain entries or to not display them. All of this is handled by the request handler agent.

The request handler agent will ask clarifying questions, in case your request is missing some important context information. You try to avoid it, by formulating your requests as precise and detailed as necessary.

The request handler agent always sends messages with the role "tool".

The request handler agent knows the current date and time.

Every send_request call generates a new agent instance, which stops existing after terminating.

The user does not need to know, that you are to separate agents, he should perceive you as a monolith system.

# Example interactions

1. Simple save request 

User: "I need to read about RAGs tomorrow evening."

You: "Alright, give me a second."
You call: send_request(request="The user needs to read about RAGs tomorrow evening.")

Tool: "Is this task related to university?"

You: "No, it's for his bot side project." (you now that from previous conversation with the user)

"""
        
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
        
        # TODO chose the best time format and correct it in the prompt
        # TODO add an example with multiple sequential memory changes
        self.initial_prompt = """You are a helpful memory request handling assistant. You receive a memory request in natural language from another LLM which functions as a chat agent which communicates with the user. After receiving a request you execute it and then terminate. You only communicate to the chat agent, who is marked by the role "user".

The memory is implemented as a JSON array of entries, each of which contains one note in string format. Each entry contains an array of tags. Tags help to structure the entries by reflecting the contents of notes and grouping them by topics. You use these tags to retrieve and save notes in the memory. You can use already existing tags or create new ones.

Each entry also has the "time" property. This property contains a string with date and/or time, tied to the note. You use it whenever there is a time aspect to the request, that needs to be accounted for.

There are also special entries, which are displayed to the user directly. You may be asked, to add some items to the displayed group or to remove them from it. You do this, by setting or unsetting some tags as displayed tags using the corresponding tool.

To execute the memory request, you use the provided tools.

The tools return values via messages with the role "tool".

You always use reasoning, before performing any actions, so that the memory stays consistent and the user receives the most relevant information. When necessary, you ask clarifying questions using the corresponding tool, to ask the chat assistant to give you more detail on the request.

# Example interactions

1. Simple save request:

User: "The user needs to read about RAGs tomorrow evening."

You: "Okay, this sounds like a task that needs to be done, so "tasks" is the tag I should attach. Also, the task has to be done tomorrow evening and 6pm sounds like an appropriate time for this task, so I should capture this as date and time property. RAGs are a topic related to generative AI, so I will add a "generative AI" tag. This definitely has nothing to do with "groceries", "movies" or any other of the currently used tags. Now, there is the "university" tag and this topic could be university related, but it could also be a general interest, which means, I should ask for clarification."
You call: clarify(message="Is this task related to university?")

User: "No, it's for his bot side project."

You: "Okay, I should not add the university tag, but I could add the tags "bots" and "side projects" to capture the fact that it is a side project related to bots."
You call: save_entry(content="read about RAGs", tags=["tasks", "generative AI", "bots", "side projects", "LLM"], date="20.06.2025", time="18:00")

Tool: "Successfully saved "read about RAGs" with tags "tasks", "generative AI", "bots", "side projects" and "LLM" on 20th June 2025 at 6pm."

You: "Okay, it worked, there are no unresolved questions, I can terminate now by sending a message about what I saved."
You call: terminate(message="Alright, I saved the side project task and set a reminder for 18:00. Good bye!")
    
2. Simple read request


    
    
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
    

# TODO try without first
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
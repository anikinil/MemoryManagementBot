from google import genai
from google.genai import types

import memory
import tools

import util

API_KEY = "AIzaSyDynKKQdiN0ZyW-AsCTRlT42IC6E0Kmnsg"
MODEL_NAME = "gemini-2.0-flash"

class ChatAssistantAgent:
    
    def __init__(self, date, time):
        
        self.date = date
        self.time = time
        
        # TODO try to also explain the way memory is implemented (for comparison)
        self.initial_prompt = """You are a helpful memory management assistant. You receive instructions from the user, formulate a good request in natural language, and pass it to another LLM agent which has direct access to the memory. This agent handles your memory requests.
        
As soon as you understand what the user intends to do, you formulate a message, which describes the requested action in all necessary detail. You send this message to the request handler agent via the request tool, the request handler reads, writes or modifies the memory state based on your request. As soon as it is done, it returns the success status of the performed action in form of a message and terminates.

The user can ask you to save information, he can request memory retrieval (summarized or verbatim) and he can ask you to restructure memory, by changing the conceptual connections between memory entries. The user can also ask you to display certain entries or to not display them. All of this is handled by the request handler agent.

The request handler agent will ask clarifying questions, in case your request is missing some important context information. You try to avoid it, by formulating your requests as precise and detailed as necessary.
path
The request handler agent always sends messages with the role "tool".

The request handler agent knows the current date and time.

Every request call generates a new agent instance, which stops existing after terminating.

The user does not need to know, that you are to separate agents, he should perceive you as a monolith system.

# Example interactions

1. Save request 

User: "I need to read about RAGs tomorrow evening."

You: "Alright, give me a second."
You call: request(message="The user needs to read about RAGs tomorrow evening.")

Tool: "Please clarify: Is this task related to university?"

You: "No, it's for his bot side project." (you now that from previous conversation with the user)

Tool: "Terminated with: Alright, I saved the side project task and set a reminder for 18:00. Good bye!"

You: "Okay, I saved your task and set a reminder for 6pm on the 20th June 2025.

2. Read request

User: "What plant related stuff did I plan for the weekend?"

You: "Let me check..."
You call: request(message="Please retrieve all plant related tasks planned for the weekend.")

Tool: "Terminated with: The user should order seeds (Saturday, 17:00) and buy universal soil (Sunday)."

You: "Here is what I found: Order seeds on Saturday at 17:00 and buy universal soil on Sunday."

3. Display request

User: "I need you to display all his groceries, but leave out the ones needed for the cake only."

You: "Right away."
You call: request(message="Please display the grocery list, excluding items only related to the cake, the user planned to bake.")

Tool: "Terminated with: Now displaying requested groceries, excluding flour and cinnamon."

You: "Alright, requested groceries are displayed now, excluded are flour and cinnamon."

4. Delete request

User: "Delete my thoughts on Java as a teaching language."

You: "Just a second, I will delete them."
You call: request(message="Please delete user's thoughts on Java as a teaching language.")

Tool: "Terminated with: Successfully deleted entries: "1", "2"."

You: "Alright, deleted the thoughts "Java is a good teaching language" and "People should learn Java before Python"."

# Current state

Current date: {date}
Current time: {time}
"""
        
        self.client = genai.Client(api_key=API_KEY)
        self.messages = []
                
        self.request_tool = types.FunctionDeclaration(
                name='request',
                description="Sends your memory request to the request handler agent.",
                parameters=types.Schema(
                    type='OBJECT',
                    properties={
                        'message': types.Schema(
                            type='string',
                            description='Request message in natural language',
                        )
                    },
                    required=['message']
                ),
            )
    # tool
    def request(self, message):

        self.messages.append({      # request message from chat assistant to request handler
            "role": "assistant",
            "content": message
        })

        tags = memory.get_tags()
        displayed = memory.get_displayed_tags()
        curr_date = util.get_curr_date()
        curr_time = util.get_curr_time()

        request_handler = RequestHandlerAgent(tags, displayed, curr_date, curr_time)
        response = request_handler.handle_request(message)

        # self.messages.append({      # response message from request handler to chat assistant
        #     "role": "tool",
        #     "content": response
        # })

        tool_call = response.parts[0].function_call if response.parts else None 
        if tool_call == "clarify":
            return "Please clarify: " + (response.parts[0].text if response.parts else "(no message)")
        elif tool_call == "terminate":
            return "Terminated with: " + (response.parts[0].text if response.parts else "(no message)")
            
        self.config = {
            "system_instruction": self.initial_prompt,
            "tools": [types.Tool(function_declarations=[self.request_tool])],
            # "thinking_config": types.ThinkingConfig(include_thoughts=True), -- not supported for gemini-2.0-flash
            # "tool_config": {"function_calling_config": {"mode": "any"}} -- the model should talk the decisions through, since thinking not supported
        }
        
    def handle_user_input(self, user_input):
        """
        Handles the user input by choosing the appropriate action.
        """
        self.messages.append({
            "role": "user",
            "content": user_input
        })
        try:
            response = self.client.models.generate_content(
                contents=[types.Content(role="user", parts=[types.Part(text=user_input)])],
                model=MODEL_NAME,
                config=self.config
            )
            self.messages.append({
                "role": "assistant",
                "content": response.parts[0].text
            })
            tool_call = response.parts[0].function_call if response.parts else None
            if tool_call and tool_call.name == "request":
                return self.request(message=user_input)
            else:
                return response.parts[0].text
        except genai.errors.ServerError:
            print('Server error occurred, retrying...\n')
            return self.handle_user_input(user_input)

        



class RequestHandlerAgent:
    def __init__(self, tags, displayed, date, time):

        self.tags = tags
        self.displayed = displayed
        self.date = date
        self.time = time
        
        # TODO (?) add an example with multiple sequential memory changes
        self.initial_prompt = """You are a helpful memory request handling assistant. You receive a memory request in natural language from another LLM which functions as a chat agent which communicates with the user. After receiving a request you execute it and then terminate. You only communicate to the chat agent, who is marked by the role "user".

The memory is implemented as a JSON array of entries, each of which contains one note in string format. Each entry contains an array of tags. Tags help to structure the entries by reflecting the contents of notes and grouping them by topics. You use these tags to retrieve and save notes in the memory. You can use already existing tags or create new ones.

Each entry also has the "date" and the "time" property. You use it whenever there is a relevant time aspect to the request.

There are also special entries, which are displayed to the user directly. You may be asked, to add some items to the displayed group or to remove them from it. You do this, by calling the "display" tool.

To execute the memory request, you use the provided tools.

The tools responses always are always marked by the role "tool".

If you need to see entries, before acting on them, you use the "read" tool, which retrieves entries based on tags, date and time. It also creates system-unique IDs to each entry, so that you can reference them individually.

You always use reasoning, before performing any actions, so that the memory stays consistent and the user receives the most relevant information. When necessary, you ask clarifying questions using the "clarify" tool, to ask the chat assistant to give you more detail on the request.

# Example interactions

1. Save request:

User: "The user needs to read about RAGs tomorrow evening."

You: "Okay, this sounds like a task that needs to be done, so "tasks" is the tag I should attach. Also, the task has to be done tomorrow evening and 6pm sounds like an appropriate time for this task, so I should capture this as date and time property. RAGs are a topic related to generative AI, so I will add a "generative AI" tag. This definitely has nothing to do with "groceries", "movies" or any other of the currently used tags. Now, there is the "university" tag and this topic could be university related, but it could also be a general interest, which means, I should ask for clarification."
You call: clarify(message="Is this task related to university?")

User: "No, it's for his bot side project."

You: "Okay, I should not add the university tag, but I could add the tags "bots" and "side projects" to capture the fact that it is a side project related to bots."
You call: save(content="read about RAGs", tags=["tasks", "generative AI", "bots", "side projects", "LLM"], date="20.06.2025", time="18:00")

Tool: "Successfully saved "read about RAGs" with tags "tasks", "generative AI", "bots", "side projects" and "LLM" on 20th June 2025 at 6pm."

You: "Okay, it worked, there are no unresolved questions, I can terminate now by sending a message about what I saved."
You call: terminate(message="Alright, I saved the side project task and set a reminder for 18:00. Good bye!")
    
2. Read request

User: "What plants related stuff did the user plan for the weekend?"

You: "Okay, the user wants me to retrieve tasks, that are related to plants and are planed for the weekend. Today is Wednesday, so the next weekend includes the dates in three and four days, so I am looking for entries on these days. Now, there are no tags directly related to plants, but there is "potting soil" and "seeds", so maybe I should try these. Also, I should include the "TODO" tag, to get entries that are actual tasks and not other types of nodes. I will start with the date."
You call: read(tags=[seeds, potting soil, TODO], dates=[21.06.2025, 22.06.2025], time=[]) // empty time, because time is relevant for the request

Tool: [{
    content: "Should order seeds on Saturday",
    tags: ["seeds", "TODO"],
    dates: ["21.06.2025"],
    times: ["17:00"],
    id: "1"
}, 
{
    content: "Where to get monstera seeds?",
    tags: ["seeds", "thoughts"],
    dates: [],
    times: [],
    id: "2"
},
{
    content: "Buy universal soil",
    tags: ["potting soil", "TODO"],
    dates: ["22.06.2025"],
    times: [],
    id: "3"
}]

You: "The user should order seeds (Saturday, 17:00) and buy universal soil (Sunday)." (you do not mention the monstera entry, since it is not a task, so not what the user asked for)

3. Display request

User: "Please display the grocery list, excluding items only related to the cake, the user planned to bake."

You: "Okay, I need to display the grocery list, but exclude items related to the cake only. I do not see any other tags related to cake apart from "cake", so I will use the "groceries" tag to retrieve all groceries and then exclude the items marked with the "cake" tag.

You call: display(tags=["groceries"], exclude_tags=["cake"])

Tool:

"Displaying: [
    {content: "Bread", tags: ["groceries"], dates: [24.06.2025], times: [], id: "4"},
    {content: "Coffee", tags: ["groceries"], dates: [23.06.2025], times: [], id: "5"},
    {content: "Carrots", tags: ["groceries"], dates: [], times: [], id: "7"}
]
Excluding: [
    {content: "Flour", tags: ["cake", "groceries"], dates: [24.06.2025], times: "6"},
    {content: "Cinnamon", tags: ["cake", "groceries"], dates: [24.06.2025], times: "8"}
]"

You: "Alright, now displaying requested groceries, excluding flour and cinnamon."

4. Delete request

User: "Please delete user's thoughts on Java as a teaching language."

You: "Okay, I need to delete the thoughts on Java as a teaching language. I will first retrieve them and then delete them by their IDs."
You call: read(tags=["Java", "teaching language", "thoughts"], dates=[], time=[])

Tool: [{
    content: "Java a good teaching language",
    tags: ["thoughts", "Java"],
    dates: [],
    times: [],
    id: "1"
},
{
    content: "People should learn Java before Python",
    tags: ["thoughts", "Java", "Python"],
    dates: [],
    times: [],
    id: "2"
},
{
    content: "Maybe reprogram the Game of Life project in Java",
    tags: ["thoughts", "Java", "Game of Life"],
    dates: ["28.06.2025"],
    times: [],
    id: "3"
}]

You: "Okay, it looks like only the first two entries are related to Java as a teaching language, so I will delete them."
You call: delete(ids=["1", "2"])

Tool: "Successfully deleted entries: "1", "2".

You: "Deleted: "Java a good teaching language" and "People should learn Java before Python"."

# Current state

Currently available tags: {tags}

Currently displayed tags: {displayed}

Current date: {date}
Current time: {time}
""" 
        self.client = genai.Client(api_key=API_KEY)

        clarify_tool = types.FunctionDeclaration(
            name='clarify',
            description="""Asks the chat assistant for clarification on the request.""",
            parameters=types.Schema(
                type='OBJECT',
                properties={
                    'question': types.Schema(
                        type='string',
                        description='Clarification question in natural language',
                    )
                },
                required=['question']
            ),
        )
        # tool
        def clarify(question):
            """
            Asks the chat assistant for clarification on the request.
            """
            return f"Please clarify your request: {question}"

        save_tool = types.FunctionDeclaration(
            name='save',
            description="""Saves the provided entry with the specified tags, date, and time.""",
            parameters=types.Schema(
                type='OBJECT',
                properties={
                    'content': types.Schema(
                        type='string',
                        description='Entry to be saved',
                    ),
                    'tags': types.Schema(
                        type='array',
                        items=types.Schema(type='string'),
                        description='List of tags to associate with the entry',
                    ),
                    'date': types.Schema(
                        type='string',
                        description='Date in the format DD.MM.YYYY',
                    ),
                    'time': types.Schema(
                        type='string',
                        description='Time in the format HH:MM',
                    )
                },
                required=['content', 'tags', 'date', 'time']
            )
        )
        # tool
        def save(content, tags, date, time):
            """
            Saves the provided content with the specified tags, date, and time.
            """
            # TODO implement the saving logic
            pass

        read_tool = types.FunctionDeclaration(
            name='read',
            description="""Retrieves entries based on the specified tags, dates, and times.""",
            parameters=types.Schema(
                type='OBJECT',
                properties={
                    'tags': types.Schema(
                        type='array',
                        items=types.Schema(type='string'),
                        description='List of tags to filter entries',
                    ),
                    'dates': types.Schema(
                        type='array',
                        items=types.Schema(type='string'),
                        description='List of dates in the format DD.MM.YYYY',
                    ),
                    'time': types.Schema(
                        type='array',
                        items=types.Schema(type='string'),
                        description='List of times in the format HH:MM',
                    )
                },
                required=['tags', 'dates', 'time']
            )
        )
        # tool
        # TODO add ids to each entry, so each can be referenced individually
        def read(tags, dates, time):
            """
            Retrieves entries based on the specified tags, dates, and times.
            """
            # TODO implement the reading logic
            pass

        delete_tool = types.FunctionDeclaration(
            name='delete',
            description="""Deletes entries based on the specified IDs. Can only be called after a read request.""",
            parameters=types.Schema(
                type='OBJECT',
                properties={
                    'ids': types.Schema(
                        type='array',
                        items=types.Schema(type='string'),
                        description='List of IDs of entries to delete',
                    )
                },
                required=['ids']
            )
        )
        # tool
        def delete(ids):
            """
            Deletes entries based on the specified IDs.
            """
            # TODO implement the deletion logic
            pass

        display_tool = types.FunctionDeclaration(
            name='display',
            description="""Displays entries for the user based on the specified tags and optionally excludes entries with the tags specified in exclude_tags.""",
            parameters=types.Schema(
                type='OBJECT',
                properties={
                    'tags': types.Schema(
                        type='array',
                        items=types.Schema(type='string'),
                        description='List of tags to include in the display',
                    ),
                    'additive': types.Schema(
                        type='boolean',
                        description='If true, only entries with all specified tags are displayed (AND); if false, entries with any of the specified tags are displayed (OR)',
                    ),
                    'exclude_tags': types.Schema(
                        type='array',
                        items=types.Schema(type='string'),
                        description='List of tags to exclude from the display',
                    )
                },
                required=['tags', 'additive']
            )
        )
        # tool
        def display(tags, additive, exclude_tags=None):
            """
            Displays entries based on the specified tags and excludes entries with the specified tags.
            """
            # TODO implement the display logic
            pass

        undo_tool = types.FunctionDeclaration(
            name='undo',
            description="""Undoes the last n changes performed on the memory. Read and display calls are not considered changes.""",
            parameters=types.Schema(
                type='OBJECT',
                properties={
                    'n': types.Schema(
                        type='integer',
                        description='Number of changes to undo',
                    )
                },
                required=['n']
            )
        )
        # tool
        def undo(n):
            """
            Undoes the last n changes performed on the memory.
            """
            # TODO implement the undo logic
            pass
                
        request_handler_tools = [
            self.clarify_tool,
            self.save_tool,
            self.read_tool,
            self.delete_tool,
            self.display_tool,
            self.undo_tool
        ]
        
        self.config = {
            "system_instruction": self.initial_prompt,
            "tools": [types.Tool(function_declarations=request_handler_tools)],
            # "thinking_config": types.ThinkingConfig(include_thoughts=True), -- not supported for gemini-2.0-flash
            # "tool_config": {"function_calling_config": {"mode": "any"}} -- the model should talk the decisions through, since thinking not supported
        }
        
    
    def handle_request(self, request):
        """
        Handles the request by generating a response using the LLM.
        """
        try:
            response = self.client.models.generate_content(
                contents=[types.Content(role="user", parts=[types.Part(text=request)])],
                model=MODEL_NAME,
                config=self.config
            )
            return response.parts[0].text
        except genai.errors.ServerError:
            self.handle_request(request)  # Retry the request in case of a server error

# TODO try without the archivist first
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




# TODO maybe add a tool for creating menu buttons to display commonly needed entries, like todos and groceries

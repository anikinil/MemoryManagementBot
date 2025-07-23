from json import tool
from google import genai
from google.genai import types

import memory

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
And you call: request(message="The user needs to read about RAGs tomorrow evening.")

Tool: "Please clarify: Is this task related to university?"

You: "No, it's for his bot side project." (you now that from previous conversation with the user)

Tool: "Terminated with: Alright, I saved the side project task and set a reminder for 18:00. Good bye!"

You: "Okay, I saved your task and set a reminder for 6pm on the 20th June 2025.

2. Read request

User: "What plant related stuff did I plan for the weekend?"

You: "Let me check..."
And you call: request(message="Please retrieve all plant related tasks planned for the weekend.")

Tool: "Terminated with: The user should order seeds (Saturday, 17:00) and buy universal soil (Sunday)."

You: "Here is what I found: Order seeds on Saturday at 17:00 and buy universal soil on Sunday."

3. Display request

User: "I need you to display all his groceries, but leave out the ones needed for the cake only."

You: "Right away."
And you call: request(message="Please display the grocery list, excluding items only related to the cake, the user planned to bake.")

Tool: "Terminated with: Now displaying requested groceries, excluding flour and cinnamon."

You: "Alright, requested groceries are displayed now, excluded are flour and cinnamon."

4. Delete request

User: "Delete my thoughts on Java as a teaching language."

You: "Just a second, I will delete them."
And you call: request(message="Please delete user's thoughts on Java as a teaching language.")

Tool: "Terminated with: Successfully deleted entries: "1", "2"."

You: "Alright, deleted the thoughts "Java is a good teaching language" and "People should learn Java before Python"."

# Current state

Current date: """ + date + """
Current time: """ + time + """
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
        
        self.config = {
            "system_instruction": self.initial_prompt,
            "tools": [types.Tool(function_declarations=[self.request_tool])],
            # "thinking_config": types.ThinkingConfig(include_thoughts=True), -- not supported for gemini-2.0-flash
            # "tool_config": {"function_calling_config": {"mode": "any"}} -- the model should talk the decisions through, since thinking not supported
        }
        
    # tool
    def request(self, message):
        
        print("MESSAGE in request (tool) in ChatAssistantAgent")
        print(message)

        self.messages.append({      # request message from chat assistant to request handler
            "role": "assistant",
            "content": message
        })

        tags = memory.get_tags()
        displayed = memory.get_displayed_tags()
        curr_date = util.get_curr_date()
        curr_time = util.get_curr_time()

        request_handler = RequestHandlerAgent(tags, displayed, curr_date, curr_time)
        response_content = request_handler.handle_request(message)
        
        print("RESPONSE_CONTENT from request_handler.handle_request in request (tool) in CAA")
        print(response_content)

        message = response_content.parts[0].text
        tool_call = response_content.parts[1].function_call
        if tool_call == "clarify":
            return "Please clarify: " + (message if message else "(no message)")
        elif tool_call == "terminate":
            return "Terminated with: " + (message if message else "(no message)")
        else:
            print("RequestHandlerAgent was supposed to call clarify or terminate but did neither: " + (message if message else "(no message)"))

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
            print("RESPONSE in handle_user_input in ChatAssistantAgent:")
            print(response)
            response_content = response.candidates[0].content.parts[0]
            self.messages.append({
                "role": "assistant",
                "content": response_content
            })
            tool_call = response_content.function_call
            if tool_call and tool_call.name == "request":
                return self.request(**tool_call.args)
            else:
                return response_content.text
        except genai.errors.ServerError:
            print('Server error occurred, retrying...\n')
            return self.handle_user_input(user_input)



class RequestHandlerAgent:
    def __init__(self, tags, displayed_tags, date, time):

        self.tags = tags
        self.displayed_tags = displayed_tags
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
And you call: clarify(message="Is this task related to university?")

User: "No, it's for his bot side project."

You: "Okay, I should not add the university tag, but I could add the tags "bots" and "side projects" to capture the fact that it is a side project related to bots."
And you call: save(content="read about RAGs", tags=["tasks", "generative AI", "bots", "side projects", "LLM"], date="20.06.2025", time="18:00")

Tool: "Successfully saved "read about RAGs" with tags "tasks", "generative AI", "bots", "side projects" and "LLM" on 20th June 2025 at 6pm."

You: "Okay, it worked, there are no unresolved questions, I can terminate now by sending a message about what I saved."
And you call: terminate(message="Alright, I saved the side project task and set a reminder for 18:00. Good bye!")
    
2. Read request

User: "What plants related stuff did the user plan for the weekend?"

You: "Okay, the user wants me to retrieve tasks, that are related to plants and are planed for the weekend. Today is Wednesday, so the next weekend includes the dates in three and four days, so I am looking for entries on these days. Now, there are no tags directly related to plants, but there is "potting soil" and "seeds", so maybe I should try these. Also, I should include the "TODO" tag, to get entries that are actual tasks and not other types of nodes. I will start with the date."
And you call: read(tags=[seeds, potting soil, TODO], dates=[21.06.2025, 22.06.2025], time=[]) // empty time, because time is relevant for the request

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

And you call: display(tags=["groceries"], exclude_tags=["cake"])

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
And you call: read(tags=["Java", "teaching language", "thoughts"], dates=[], time=[])

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
And you call: delete(ids=["1", "2"])

Tool: "Successfully deleted entries: "1", "2".

You: "Deleted: "Java a good teaching language" and "People should learn Java before Python"."

# Current state

Currently available tags: """ + ", ".join(tags) + """

Currently displayed tags: """ + ", ".join(displayed_tags) + """

Current date: """ + date + """
Current time: """ + time + """
""" 
        self.client = genai.Client(api_key=API_KEY)

        self.clarify_tool = types.FunctionDeclaration(
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
        
        self.save_tool = types.FunctionDeclaration(
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
        
        self.read_tool = types.FunctionDeclaration(
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

        self.display_tool = types.FunctionDeclaration(
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

        self.delete_tool = types.FunctionDeclaration(
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

        self.undo_tool = types.FunctionDeclaration(
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
        
        self.request_handler_tools = [
            self.clarify_tool,
            self.save_tool,
            self.read_tool,
            self.delete_tool,
            self.display_tool,
            self.undo_tool
        ]
        
        self.config = {
            "system_instruction": self.initial_prompt,
            "tools": [types.Tool(function_declarations=self.request_handler_tools)],
            # "thinking_config": types.ThinkingConfig(include_thoughts=True), -- not supported for gemini-2.0-flash
            # "tool_config": {"function_calling_config": {"mode": "any"}} -- the model should talk the decisions through, since thinking not supported
        }
        
        
        
    # tool
    def clarify(question):
        """
        Asks the chat assistant for clarification on the request.
        """
        return f"Please clarify your request: {question}"

        
    # tool
    def save(content, tags, date, time):
        """
        Saves the provided content with the specified tags, date, and time.
        """
        # TODO implement the saving logic
        pass

        
    # tool
    # TODO add ids to each entry, so each can be referenced individually
    def read(tags, dates, time):
        """
        Retrieves entries based on the specified tags, dates, and times.
        """
        # TODO implement the reading logic
        pass

        
    # tool
    def delete(ids):
        """
        Deletes entries based on the specified IDs.
        """
        # TODO implement the deletion logic
        pass

    
    # tool
    def display(tags, additive, exclude_tags=None):
        """
        Displays entries based on the specified tags and excludes entries with the specified tags.
        """
        # TODO implement the display logic
        pass

    # tool
    def undo(n):
        """
        Undoes the last n changes performed on the memory.
        """
        # TODO implement the undo logic
        pass
        
    
    def handle_request(self, request):
        """
        Handles the request by generating a response using the LLM.
        """
        try:
            print("REQUEST in handle_request in RequestHandlerAgent")
            print(request)
            response = self.client.models.generate_content(
                contents=[types.Content(role="user", parts=[types.Part(text=request)])],
                model=MODEL_NAME,
                config=self.config
            )
            print("RESPONSE in handle_request in RequestHandlerAgent")
            print(response)
            response_content = response.candidates[0].content
            
            response_tool_call = None
            # sometimes tool call is already in the 1st (and only) part, but sometimes it comes in 2nd part
            if response_content.parts[0].function_call is not None:
                response_tool_call = response_content.parts[0].function_call
            elif len(response_content.parts) > 1 and response_content.parts[1].function_call is not None:
                response_tool_call = response_content.parts[1].function_call

            if response_tool_call == "terminate":
                print("TERMINATE in handle_request in RHA")
                return response_content
            elif response_tool_call == "clarify":
                print("CLARIFY in handle_request in RHA")
                return response_content
            elif response_tool_call is not None:
                tool_response = self.execute_memory_action(response_tool_call)
            else:
                print("NO TOOL CALL DETECTED in handle_request in RHA")

            return response_content
        except genai.errors.ServerError:
            self.handle_request(request)  # Retry the request in case of a server error

    # is called from handle_request, when a memory action is detected in the response of the RequestHandlerAgent
    def execute_memory_action(self, tool_call):
        
        print("\nREQUESTED ACTION is", tool_call)

        return "" # should return the tool response(s)


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

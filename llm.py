from json import tool
import os
from google import genai
from google.genai import types

import memory
import util

# TODO if anything goes wrong (agent retries same request) stop and reinitialize the agent with same input

API_KEY = os.environ['GEMINI_API_KEY']
# MODEL_NAME = "gemini-2.0-flash"
MODEL_NAME = "gemini-2.5-pro"

class ChatAssistant:
    
    def __init__(self, date, time):
        
        self.date = date
        self.time = time
        
        # TODO try to also explain the way memory is implemented (for comparison)
        self.initial_prompt = """You are a memory management agent. You receive a user message and do one of two things:

If it's a general question (e.g., unrelated to memory), answer directly.
If it's a memory-related request (save, read, delete, display), choose one of:

    - save: save information to memory
    - read: retrieve information from memory
    - delete: remove information from memory
    - display: make information visible to the user directly

Use the corresponding tool with precise natural-language parameters.

After receiving a tool response, summarize or rephrase it clearly and concisely before replying to the user. Do not omit any important details from the tool's response when replying to the user.

Current date: """ + date + """
Current time: """ + time

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
            # "thinking_config": types.ThinkingConfig(include_thinking=True, thinking_budget=100)
            "tool_config": {"function_calling_config": {"mode": "any"}}
        }
        
    # tool
    def request(self, message):

        print("REQUEST_TEXT in request (tool) in ChatAssistantAgent")
        print(message)

        message = types.Content(parts=[types.Part(text=message)], role='user')

        self.messages.append({      # request message from chat assistant to request handler
            "role": "model",
            "content": message
        })

        tags = memory.get_tags()
        displayed = memory.get_displayed_tags()
        curr_date = util.get_curr_date()
        curr_time = util.get_curr_time()

        request_handler = RequestHandlerAgent(tags, displayed, curr_date, curr_time, self)
        response_content = request_handler.handle_request(message)
        
        print("RESPONSE_CONTENT from request_handler.handle_request in request (tool) in CAA")
        print(response_content)

        return response_content if response_content else "No response."

        # message = response_content.parts[0].text
        # tool_call = response_content.parts[1].function_call
        # if tool_call == "clarify":
        #     return "Please clarify: " + (message if message else "(no message)")
        # elif tool_call == "terminate":
        #     return "Terminated with: " + (message if message else "(no message)")
        # else:
        #     print("RequestHandlerAgent was supposed to call clarify or terminate but did neither: " + (message if message else "(no message)"))

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
            response_content = response.candidates[0].content
            
            tool_call = None
            # sometimes tool call is already in the 1st (and only) part, but sometimes it comes in 2nd part
            if response_content.parts[0].function_call is not None:
                tool_call = response_content.parts[0].function_call
            elif len(response_content.parts) > 1 and response_content.parts[1].function_call is not None:
                tool_call = response_content.parts[1].function_call
            self.messages.append({
                "role": "model",
                "content": response_content
            })
            
            
            print("\nTOOL_CALL in handle_user_input in ChatAssistantAgent:")
            print(tool_call)

            if tool_call and tool_call.name == "request":
                return self.request(**tool_call.args)
            else:
                return response_content.parts[0].text
        except genai.errors.ServerError:
            print('Server error occurred, retrying...\n')
            return self.handle_user_input(user_input)

    def answer_clarification_request(self, question):
        """
        Answers the clarification request from the RequestHandlerAgent.
        """
        self.messages.append({
            "role": "user",
            "content": question
        })
        try:
            response = self.client.models.generate_content(
                contents=[types.Content(role="user", parts=[types.Part(text=question)])],
                model=MODEL_NAME,
                config=self.config
            )
            print("\nRESPONSE in answer_clarification_request in ChatAssistantAgent:")
            print(response)
            response_content = response.candidates[0].content.parts[0]
            self.messages.append({
                "role": "model",
                "content": response_content
            })
            return response_content.text
        except genai.errors.ServerError:
            print('Server error occurred, retrying...\n')
            return self.answer_clarification_request(question)



class ReadAgent:
    def __init__(self, tags, displayed_tags, date, time, chat_assistant_agent):

        self.tags = tags
        self.displayed_tags = displayed_tags
        self.date = date
        self.time = time
        self.chat_assistant_agent = chat_assistant_agent

        # TODO (?) add an example with multiple sequential memory changes
        self.initial_prompt = """You are a helpful memory management agent. You retrieve information from memory based on the user's request.
The memory consists of a list of entries, each with the following fields:

    - content: the text of the entry
    - tags: a list of tags, related to the entry
    - dates: a list of due dates in the format DD.MM.YYYY
    - times: a list of due times in the format HH:MM
        
Retrieve entries by calling the "read" tool with tags and/or dates and/or times as parameters.
After receiving a tool response, summarize or rephrase it clearly and concisely and reply to the user by calling the "terminate" tool with the response text.
Do not omit any details.
"""

        self.client = genai.Client(api_key=API_KEY)
        self.messages = []

        self.read_tool = types.FunctionDeclaration(
            name='read',
            description="""Retrieves entries from memory.""",
            parameters=types.Schema(
                type='OBJECT',
                properties={
                    'tags': types.Schema(
                        type='array',
                        items=types.Schema(type='string'),
                        description='List of tags to filter entries',
                    ),
                    'additive': types.Schema(
                        type='boolean',
                        description='If true, only entries with all specified tags are displayed (AND); if false, entries with any of the specified tags are displayed (OR)',
                    ),
                    'exclude': types.Schema(
                        type='array',
                        items=types.Schema(type='string'),
                        description='List of tags, entries containing which will not be displayed',
                    ),
                    'dates': types.Schema(
                        type='array',
                        items=types.Schema(type='string'),
                        description='List of dates in the format DD.MM.YYYY (if empty, no date filtering is applied)',
                    ),
                    'time': types.Schema(
                        type='array',
                        items=types.Schema(type='string'),
                        description='List of times in the format HH:MM (if empty, no time filtering is applied)',
                    )
                },
                required=['tags']
            )
        )
        
        self.terminate_tool = types.FunctionDeclaration(
            name='terminate',
            description="""Terminates the conversation and returns the response to the user.""",
            parameters=types.Schema(
                type='OBJECT',
                properties={
                    'response': types.Schema(
                        type='string',
                        description='Response text to be returned to the user',
                    )
                },
                required=['response']
            )
        )
        
        self.request_handler_tools = [
            self.read_tool,
            self.terminate_tool
        ]
        
        self.config = {
            "system_instruction": self.initial_prompt,
            "tools": [types.Tool(function_declarations=self.request_handler_tools)],
            # "thinking_config": types.ThinkingConfig(include_thinking=True, thinking_budget=100)
            "tool_config": {"function_calling_config": {"mode": "any"}}
        }
        
        
          
    def handle_request(self, request_contents):
        """
        Handles the request from ChatAssistantAgent.
        """
        try:
            print("REQUEST in handle_request in RequestHandlerAgent")
            print(request_contents)
            self.messages.append({"role": "user", "content": request_contents})
            response = self.client.models.generate_content(
                contents=request_contents,
                model=MODEL_NAME,
                config=self.config
            )
            print("RESPONSE in handle_request in RequestHandlerAgent")
            print(response)
            response_content = response.candidates[0].content
            
            tool_call = None
            # sometimes tool call is already in the 1st (and only) part, but sometimes it comes in 2nd part
            if response_content.parts[0].function_call is not None:
                tool_call = response_content.parts[0].function_call
            elif len(response_content.parts) > 1 and response_content.parts[1].function_call is not None:
                tool_call = response_content.parts[1].function_call

            if tool_call is None:
                return "Unexpected behavior: did not call any tool, response: " + response_content.parts[0].text if response_content.parts else "(no message)"
            
            # if tool_calls correctly contains the tool call, append it to the messages
            self.messages.append({
                "role": "model",
                "content": response_content.parts[0]
            })

            if tool_call.name == "terminate":
                print("TERMINATED with: " + (response_content.parts[0].text if response_content.parts else "(no message)"))
                return "Terminated with: " + (response_content.parts[0].text if response_content.parts else "(no message)")
            elif tool_call.name == "clarify":
                question = tool_call.args.get('question', '')
                clarification = self.clarify(question)
                clarification_content = types.Content(parts=[types.Part(text=clarification)], role='user')
                return self.handle_request(clarification_content)  # Retry with clarification
            else:
                tool_response = self.execute_memory_action(tool_call)
                tool_response_content = types.Content(parts=[types.Part(text=tool_response)], role='user')
                return self.handle_request(tool_response_content)  # Retry with the tool response

        except genai.errors.ServerError:
            return self.handle_request(request_contents)  # Retry the request in case of a server error

    # is called from handle_request, when a memory action is detected in the response of the RequestHandlerAgent
    def execute_memory_action(self, tool_call):
        
        print("\nREQUESTED ACTION is", tool_call)

        # return_value = "Entry \"milk\" saved successfully with tag \"groceries\""  # should return the tool response(s)
        return_value = """[{content: "Buy milk", tags: ["buy", "groceries"], dates: [27.06.2025], times: [], id: "1"},{content: "Bread", tags: ["buy", "groceries"], dates: [], times: [], id: "2"}]"""

        print("RETURN_VALUE in execute_memory_action in RequestHandlerAgent:", return_value)
        return return_value

    # tool
    def read(self):
        """
        Retrieves entries from memory based on the specified tags, dates, and times.
        """
        # TODO implement the reading logic
        # For now, just return a dummy response
        return "Dummy response from read tool"
    
    # tool
    def terminate(self, response):
        """
        Terminates the conversation and sends the response to the ChatAssistant.
        """
        print("TERMINATED with response:", response)


class SaveAgent:
    def __init__(self, content, tags, date, time, chat_assistant_agent):
        self.content = content
        self.tags = tags
        self.date = date
        self.time = time
        self.chat_assistant_agent = chat_assistant_agent

        self.initial_prompt = """You are a helpful memory management agent. You save information to memory based on the user's request.
The memory consists of a list of entries, each with the following fields:

    - content: the text of the entry
    - tags: a list of tags, related to the entry
    - dates: a list of due dates in the format DD.MM.YYYY
    - times: a list of due times in the format HH:MM

Save entries by calling the "save" tool with the content, tags, date, and time as parameters.
After receiving a tool response reply with a confirmation message by calling the "terminate" tool with the response text."""

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


#########
# TOOLS #
#########

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
        
        
        
        
          
    # tool
    def clarify(self, question):
        """
        Asks the chat assistant for clarification on the request.
        """
        clarification = self.chat_assistant_agent.answer_clarification_request(f"Please clarify your request: {question}")
        return clarification

        
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
        

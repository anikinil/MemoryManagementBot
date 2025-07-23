
from llm import RequestHandlerAgent
from google.genai import types

from util import get_curr_date, get_curr_time

########################################################
############### Chat Assistant Tools ###################
########################################################



########################################################
############### Request Handler Tools ##################
########################################################


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
    clarify_tool,
    save_tool,
    read_tool,
    delete_tool,
    display_tool,
    undo_tool
]
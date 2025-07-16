
from memory import delete_last_logs, get_last_state, save_state
from google.genai import types

from util import format_subnodes


read_subnodes_tool = types.FunctionDeclaration(
    name='read_subnodes',
    description="""Returns all subnodes of a specified node to the agent. The user does not see the output of this tool, it is used to read the memory tree and understand the current state of the memory.""",
    parameters=types.Schema(
        type='OBJECT',
        properties={
            'path': types.Schema(
                type='string',
                description='Path to the node.',
            ),
        },
        required=['path'],
    ),
)

print_subnodes_tool = types.FunctionDeclaration(
    name='print_subnodes',
    description='Prints all subnodes of a specified node to the user. This tool is used to display the memory tree to the user, if he demands it specifically.',
    parameters=types.Schema(
        type='OBJECT',
        properties={
            'path': types.Schema(
                type='string',
                description='Path to the node.',
            ),
        },
        required=['path'],
    ),
)

save_node_tool = types.FunctionDeclaration(
    name='save_node',
    description='Saves a new node in the memory tree.',
    parameters=types.Schema(
        type='OBJECT',
        required=['path'],
        properties={
            'path': {
                'type': 'string',
                'description': 'Path to the new node in the memory tree. If the nodes in the path do not exist yet, they will be created. Format: root/some_node/.../this_is_a_new_node',
            },
        },
    ),
)

move_nodes_tool = types.FunctionDeclaration(
    name='move_nodes',
    description='Moves a node and all of its subnodes to a new location in the memory tree. Node at old_path becomes the child of the node at new_path. If the nodes at new_path do not exist yet, they will be created.',
    parameters=types.Schema(
        type='OBJECT',
        required=['old_path', 'new_path'],
        properties={
            'old_path': types.Schema(
                type='string',
                description='Path to the node to be moved.',
            ),
            'new_path': types.Schema(
                type='string',
                description='Path to the new location of the node.',
            ),
        },
    ),
)

delete_nodes_tool = types.FunctionDeclaration(
    name='delete_nodes',
    description='Deletes a node and all of its subnodes from the memory tree.',
    parameters=types.Schema(
        type='OBJECT',
        required=['path'],
        properties={
            'path': types.Schema(
                type='string',
                description='Path to the node.',
            ),
        },
    ),
)

undo_n_changes_tool = types.FunctionDeclaration(
    name='undo_n_changes',
    description='Undo the last n changes on the memory tree.',
    parameters=types.Schema(
        type='OBJECT',
        required=['n'],
        properties={
            'n': types.Schema(
                type='integer',
                description='The number of changes to undo.',
            ),
        },
    ),
)

available_tools = [read_subnodes_tool, print_subnodes_tool, save_node_tool, move_nodes_tool, delete_nodes_tool, undo_n_changes_tool]

def read_subnodes(path):

    state = get_last_state()
    keys = path.strip('/').split('/')
    for key in keys:
        if key not in state:
            return 'Node does not exist'
        state = state.get(key, {})
    return state

def print_subnodes(path):
    subnodes = read_subnodes(path)
    if subnodes == 'Node does not exist':
        return subnodes
    if not subnodes:
        return 'No subnodes found'
    if isinstance(subnodes, dict):
        return '\n'.join(format_subnodes(subnodes))
    return str(subnodes)

def save_node(path):

    state = get_last_state()

    keys = path.split('/')
    current = state

    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]

    current[keys[-1]] = {}

    if current == state:
        return 'Node already exists'
    else:
        save_state(state)
        return 'Node saved'

def move_nodes(old_path, new_path):

    state = get_last_state()

    sub = read_subnodes(old_path)
    if sub == 'Node does not exist':
        return 'Node does not exist: ' + old_path

    if old_path.rsplit('/',1)[0] == new_path:
        return 'New path already leads to the location of the node to be moved'

    keys = new_path.strip('/').split('/')
    current = state
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]

    current[keys[-1]] = {old_path.split('/')[-1]: sub, **(current[keys[-1]] if keys[-1] in current else {})}

    keys = old_path.strip('/').split('/')
    current = state
    for key in keys[:-1]:
        if key not in current:
            return 'Node does not exist'
        current = current[key]

    if keys[-1] not in current:
        return 'Node does not exist'

    current.pop(keys[-1], None)

    save_state(state)
    return 'Nodes moved'

def delete_nodes(path):
    state = get_last_state()

    keys = path.strip('/').split('/')
    sub_state = state
    for key in keys[:-1]:
        if key not in sub_state:
            return 'Node does not exist'
        sub_state = sub_state[key]

    if keys[-1] not in sub_state:
        return 'Node does not exist'

    sub_state.pop(keys[-1], None)

    save_state(state)
    return 'Node deleted'
        
def undo_n_changes(n):
    try:
        delete_last_logs(n)
    except ValueError as e:
        return 'The memory has been changed less than ' + str(n) + ' times'
    return 'Last ' + str(n) + ' changes undone'

available_functions = {
    'read_subnodes': read_subnodes,
    'print_subnodes': print_subnodes,
    'save_node': save_node,
    'move_nodes': move_nodes,
    'delete_nodes': delete_nodes,
    'undo_n_changes': undo_n_changes,
}
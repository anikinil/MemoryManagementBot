
import json

from memory import delete_last_logs, get_last_state, save_state


read_subnodes_tool = {
    'type': 'function',
    'function': {
        'name': 'read_subnodes',
        'description': 'Returns all subnodes of a specified node.',
        'parameters': {
            'type': 'object',
            'required': ['path'],
            'properties': {
                'path': {
                    'type': 'string',
                    'description': 'The path to the node.',
                },
            },
        },
    },
}

save_node_tool = {
    'type': 'function',
    'function': {
        'name': 'save_node',
        'description': 'Saves a node in the memory tree.',
        'parameters': {
            'type': 'object',
            'required': ['path', 'content'],
            'properties': {
                'path': {
                    'type': 'string',
                    'description': 'The path to the node in the memory tree. If the does not lead to an existing node, the node will be created.',
                },
                'content': {
                    'type': 'string',
                    'description': 'The content of the node.',
                },
            },
        },
    },
}

move_nodes_tool = {
    'type': 'function',
    'function': {
        'name': 'move_nodes',
        'description': 'Moves a node and all of its subnodes to a new location in the memory tree. Node at old_path becomes the child of the node at new_path.',
        'parameters': {
            'type': 'object',
            'required': ['old_path', 'new_path'],
            'properties': {
                'old_path': {
                    'type': 'string',
                    'description': 'The path to the node to be moved.',
                },
                'new_path': {
                    'type': 'string',
                    'description': 'The path to the new location of the node.',
                },
            },
        },
    },
}

delete_nodes_tool = {
    'type': 'function',
    'function': {
        'name': 'delete_nodes',
        'description': 'Deletes a node and all of its subnodes from the memory tree.',
        'parameters': {
            'type': 'object',
            'required': ['path'],
            'properties': {
                'path': {
                    'type': 'string',
                    'description': 'The path to the node.',
                },
            },
        },
    },
}

undo_n_changes_tool = {
    'type': 'function',
    'function': {
        'name': 'undo_n_changes',
        'description': 'Undo the last n changes on the memory tree.',
        'parameters': {
            'type': 'object',
            'required': ['n'],
            'properties': {
                'n': {
                    'type': 'integer',
                    'description': 'The number of changes to undo.',
                },
            },
        },
    },
}

available_tools = [read_subnodes_tool, save_node_tool, move_nodes_tool, delete_nodes_tool, undo_n_changes_tool]

def read_subnodes(path):

    state = get_last_state()
    keys = path.strip('/').split('/')
    for key in keys:
        if key not in state:
            return 'Node does not exist'
        state = state.get(key, {})
    return state

def save_node(path, content):

    state = get_last_state()

    keys = path.split('/')
    current = state

    for key in keys:
        if key not in current:
            current[key] = {}
        current = current[key]

    current[content] = {}

    if current == state:
        return 'Node already exists'
    else:
        save_state(state)
        return 'Node saved'

# fix
def move_nodes(old_path, new_path):

    state = get_last_state()

    sub = read_subnodes(old_path)
    if sub == 'Node does not exist':
        return 'Node does not exist: ' + old_path

    if old_path == new_path:
        return 'Paths are the same'

    keys = new_path.strip('/').split('/')
    current = state
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]

    current[keys[-1]] = {old_path.split('/')[-1]: sub, **current[keys[-1]]}

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
    'save_node': save_node,
    'move_nodes': move_nodes,
    'delete_nodes': delete_nodes,
    'undo_n_changes': undo_n_changes,
}
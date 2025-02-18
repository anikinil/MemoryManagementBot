
import json


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

delete_node_tool = {
    'type': 'function',
    'function': {
        'name': 'delete_node',
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

available_tools = [read_subnodes_tool, save_node_tool, delete_node_tool]

def read_subnodes(path):
    
    with open('memory.json') as f:
        d = json.load(f)
        keys = path.strip('/').split('/')
        for key in keys:
            if key not in d:
                return 'Node does not exist'
            d = d.get(key, {})
        return d
    
def save_node(path, content):

    with open('memory.json') as f:
        d = json.load(f)

    keys = path.split('/')
    current = d

    for key in keys:
        if key not in current:
            current[key] = {}
        current = current[key]

    current[content] = {}

    if current == d:
        return 'Node already exists'
    else:
        with open('memory.json', 'w') as f:
            json.dump(d, f, indent=4)
        return 'Node saved'

def move_nodes(old_path, new_path):

    with open('memory.json') as f:
        d = json.load(f)

    keys = old_path.strip('/').split('/')
    sub_d = d
    for key in keys[:-1]:
        sub_d = sub_d.setdefault(key, {})

    content = sub_d.pop(keys[-1], None)

    keys = new_path.strip('/').split('/')
    current = d
    for key in keys:
        if key not in current:
            current[key] = {}
        current = current[key]

    current[content] = {}

    with open('memory.json', 'w') as f:
        json.dump(d, f, indent=4)

def delete_node(path):
    with open('memory.json') as f:
        d = json.load(f)

    keys = path.strip('/').split('/')
    sub_d = d
    for key in keys[:-1]:
        if key not in sub_d:
            return 'Node does not exist'
        sub_d = sub_d[key]

    if keys[-1] not in sub_d:
        return 'Node does not exist'

    sub_d.pop(keys[-1], None)

    with open('memory.json', 'w') as f:
        json.dump(d, f, indent=4)

    return 'Node deleted'
        

available_functions = {
    'read_subnodes': read_subnodes,
    'save_node': save_node,
    'delete_node': delete_node
}
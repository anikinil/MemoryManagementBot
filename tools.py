
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
            d = d.get(key, {})
        return d
    
def save_node(path, content):

    with open('memory.json') as f:
        d = json.load(f)
        keys = path.strip('/').split('/')
        for key in keys[:-1]:
            d = d.get(key, {})
        d[keys[-1]] = content
        return d

def delete_node(path):

    with open('memory.json') as f:
        d = json.load(f)
        keys = path.strip('/').split('/')
        for key in keys[:-1]:
            d = d.get(key, {})
        d.pop(keys[-1], None)
        return d
        

available_functions = {
    'read_subnodes': read_subnodes,
    'save_node': save_node,
    'delete_node': delete_node
}
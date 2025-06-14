import json

from util import format_subnodes

def init_memory():
    f = open('memory_log.json', 'w')
    f.write('[{"root": {}}]')
    f = open('memory_state.txt', 'w')
    f.write('{"root": {}}')
    f.close()

def get_last_state():
    try:
        with open('memory_log.json') as f:
            d = json.load(f)
            return d[-1] if d else {"root": {}}
    except FileNotFoundError:
        init_memory()
        return {"root": {}}

def save_state(state):
    with open('memory_log.json') as f:
        d = json.load(f)
    d.append(state)
    with open('memory_log.json', 'w') as f:
        json.dump(d, f, indent=4)

def delete_last_logs(n):
    with open('memory_log.json') as f:
        d = json.load(f)
    if len(d) < n-1:
        raise ValueError('Not enough logs to delete: only ' + str(len(d)) + ' logs available')
    for i in range(n):
        d.pop()
    with open('memory_log.json', 'w') as f:
        json.dump(d, f, indent=4)

def update_display():
    state = get_last_state()
    with open('memory_state.txt', 'w') as f:
        json.dump(format_subnodes(state), f, indent=4)
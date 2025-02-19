import json

def get_last_state():

    with open('memory_log.json') as f:
        d = json.load(f)[-1]
    return d

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
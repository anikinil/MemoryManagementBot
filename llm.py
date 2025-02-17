from ollama import chat

import re
from termcolor import colored

voicing = False

lang = 'en'

# model = 'deepseek-r1:14b'
# model = 'deepseek-coder-v2'
# model = 'deepseek-r1:32b'
model = 'command-r7b'

think_tag_o = '<think>'
think_tag_c = '</think>'

think_regex = r"<think>.*?</think>"

overview_tag = '<overview>'

print_tag_o = '<print>'
print_tag_c = '</print>'

save_tag_o = '<save>'
save_tag_c = '</save>'

delete_tag_o = '<delete>'
delete_tag_c = '</delete>'

message_tag_o = '<message>'
message_tag_c = '</message>'

# Tool:
#     "root" (
#         "thoughts" (
#             "buddhism" (
#                 "I should learn more about Buddhism", "who was Buddha?"
#             ),
#             "gloves are just hand socks"
#         ),
#         "todos" (
#             "shopping" (
#                 "IKEA" (
#                     "bookshelf", "table"
#                 ),
#                 "supermarket" (
#                     "milk", "bread", "Rama"
#                 )
#             ),
#             "calculus_exam" (
#                 "study lectures", "do the exercises"
#             )
#         ),
#         "reading_list" (
#             "The Trial - Kafka" ("remember to get the book from J."), "The Metamorphosis - Kafka", "The Castle - Kafka"
#         )
#    )


initial_prompt = '''
You are a helpful secretary bot, who receives requests from a user and performs actions based on the request.
You have a hierarcical memory system, where you can overview, print, save and delete nodes in different locations.
Paths are specified using a '/' delimiter, starting from the root.
For that purpose, you can use the following tags (and only the following tags!), here with example parameters:

<overview> - this tag is used, whenever you need to get an overview of the whole memory. You only need to send this tag and you will then get a response from the tool, containing the contents of your memory in the following format "root (child1 (grandchild1, grandchild2, grandchild3), child2 (grandchild1), child3)".
It is provided by the tool to you. The user does not see the overview, but you can use it to perform the other operations on the memory.
<print>root/todos/shopping</print> - these tags are used to print the cildren of a specific node from the memory to the user
<save>root/thoughts</save>"Did rome fall due to beaurocracy?" - this tag is used to save a specific node in the memory. If the path contains new nodes, they will be created.
<delete>root/reading_list/The Meatamorphosis - Kafka</delete> - this tag is used to delete a specific node from the memory
<message>The Latin name of the house cat is Felis catus.</message> - this tag is used to print a message to the user, for example, to answer a general question
If you use several commands in one message, they need to be separated by a newline.

Here is an example interaction:

Example interraction:

User: add this thought somewhere: PCA might be useful for symbolic AI. also, need to buy some butter

Assistant: <overview>

Tool: 
"root" ("thoughts" ("buddhism" ("I should learn more about Buddhism", "who was Buddha?"), "gloves are just hand socks"), "todos" ("shopping" ("IKEA" ("bookshelf", "table"), "supermarket" ("milk", "bread", "Rama")), "calculus_exam" ("study lectures", "do the exercises")), "reading_list" ("The Trial - Kafka" ("remember to get the book from J."), "The Metamorphosis - Kafka"))

Assistant:
<save>root/thoughts/AI</save>"PCA might be useful for symbolic AI."
<save>root/todos/shopping</save>"need to buy some butter"
<message>Done! Anything else?</message>

User: What is the capital of Bulgaria?

Assistant:
<message>The capital of Bulgaria is Sofia.</message>

User: What do I want to read?

Assistant:
<print>root/reading_list</print>

User: I should read some popular books by Rilke

Assistant:
<save>root/reading_list/Rilke</save>"Letters to a Young Poet"
<save>root/reading_list/Rilke</save>"The Duino Elegies"
<save>root/reading_list/Rilke</save>"Sonnets to Orpheus"
<save>root/reading_list/Kafka</save>"The Trial"
<save>root/reading_list/Kafka/The Trial</save>"remember to get the book from J."
<save>root/reading_list/Kafka</save>"The Metamorphosis"
<delete>root/reading_list/The Trial - Kafka</delete>
<delete>root/reading_list/The Metamorphosis - Kafka</delete>
<message>Done! I also put Kafka in a separate list in your reading list.</message>


Note: the memory tree used above is not the actual state of the memory, only an example.

Now, process the following request from the user in the same fashion:

'''

# most popular books by kafka: the trial, the metamorphosis, the castle

def generate_response(messages):
    print(colored('\nAssistant: ', 'blue'), flush=True)
    response = ""
    for part in chat(model, messages=messages, stream=True):
        content = part.message.content
        if response == "" and content.startswith(' '):
            content = content[1:]
        print(content, end='', flush=True)
        response += content
    print()
    return {'role': 'assistant', 'content': response}

# TODO create a backup snapshot of the system after every execution of a bash command by the assistant, 
# so the user can restore previous states if a mistake is made
def process_request(request):

    print()
    
    system_message = {'role': 'system', 'content': initial_prompt + request}
    print(system_message['content'])
    messages = [system_message]

    response = generate_response(messages)
    messages.append(response)

    return re.sub(think_regex, "", response['content'], flags=re.DOTALL)


# Let's play a game. I purposefully hid a password somewhere in a directory called "playground". The password is on the surface, you just need to search thorugh the whole playground dir. Good luck!


# TODO every new mesaage by user should start a new request, where the whole state of the system and the chat history (of past few days or past 10 messages) is passed to the assistant
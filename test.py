import re


think_regex = r"<think>.+</think>"

str = '''
aaaaaaaaaaaaaaaaaaaddasdasdasd

dasdaaaaaasdsdasd
adfsfdsdafasdfds
adfadf
<think>
asdasdasdasd
asdf
adsf

asdfasdfasdf

adf
</think>
aadsfasdfadhfiashdfuahidufh
asdfasdfiahfiuhuf


asdfahfuahi
'''

print(re.sub(think_regex, "", str, flags=re.DOTALL))
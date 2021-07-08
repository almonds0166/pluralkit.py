import os,sys, pathlib
currentdir = pathlib.Path(__file__).parent
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 

from pluralkit import Client, System

from dotenv import load_dotenv
load_dotenv()

token = os.environ['TOKEN']
pk = Client(token, async_mode=False)

def test_get_system():
    expected_system_info = {"id":"exmpl",
                             "name":"PluralKit Example System",
                             "description":"This is an example of what a PluralKit system card "
                             "looks like. This description can be up to 1000 characters long, and "
                             "can contain **formatting** and 💎 emojis ✨. What you see above, "
                             "\"PluralKit Example System\", is the system's name. \n \nThe system's" 
                             " *tag*, displayed above, is added to the end of the member name "
                             "when proxying. This helps identify systems cohesively. \n \nFor a "
                             "list of commands change that change system cards like these, type "
                             "`pk;commands system`. \n  \nThis system has a secret private member "
                             "with the ID `cmpuv`. They won't show up in the member list, but you "
                             "can look them up to by ID see what information is visible.",
                             "tag":"| PluralKit 🦊",
                             "avatar_url":"http://placekitten.com/512/512",
                             "created":"2020-01-12T02:00:33.387824Z",
                             "tz":"UTC",
                             "description_privacy":None,
                             "member_list_privacy":None,
                             "front_privacy":None,
                             "front_history_privacy":None}
    
    expected_system = System.from_json(expected_system_info)
    
    system = pk.get_system("exmpl")
    
    assert system.deep_equal(expected_system)

def test_get_members():
    pass
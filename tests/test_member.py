 
import os,sys, pathlib
currentdir = pathlib.Path(__file__).parent
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 

from pluralkit import Client, Member

token = os.environ['TOKEN']
pk = Client(token, async_mode=False)
    
def test_get_member():

    
    reference_member_info = {
              "id":"gaznz",
              "name":"Tester T. Testington",
              "color": None,
              "display_name": None,
              "birthday": None,
              "pronouns": None,
              "avatar_url": None,
              "description":"Here is an example of another member, albeit with less properties set." 
              " It's possible to have members without proxy tags - useful for record-keeping.",
              "proxy_tags":[],
              "keep_proxy": False,
              "privacy":None,
              "visibility":None,
              "name_privacy":None,
              "description_privacy":None,
              "birthday_privacy":None,
              "pronoun_privacy":None,
              "avatar_privacy":None,
              "metadata_privacy":None,
              "created":"2020-01-12T02:21:26.274746Z"
              }
    
    reference_member = Member.from_json(reference_member_info)
    
    test_member = pk.get_member("gaznz")
        
    try:
        assert test_member._deep_equal(other=reference_member) is True
    except AssertionError:
        for key, value in test_member.__dict__.items():
            if key not in ("id", "created"):
                try:
                    assert value == reference_member.__dict__[key]
                except AssertionError as e:
                    print(f"Error occured at {key}: {value}")
                    assert value == reference_member.__dict__[key]

def test_edit_member():
    
    choices = {
        "id": ["cewel"],
        "name": ["test_1", "test_2", "test_3"],
        "display_name": ["testing_1", "testing_2", "testing_3"],
        "description": ["testing..._1", "testing..._2", "testing..._3"],
        "pronouns": ["they/them", "she/her", "he/him"],
        "color": ["red", "#ffffff", ""],
        "created": ["2021-06-14T01:48:54.911915Z"],
        "avatar_url": ["https://cdn.pixabay.com/photo/2015/04/23/22/00/tree-736885__480.jpg", 
                       "https://image.shutterstock.com/image-photo/mountains-under-mist-morning-"
                       "amazing-260nw-1725825019.jpg"],
        "birthday": ["1904-02-28", "2025-06-12", "0834-12-23"],
        "proxy_tags": [[{"prefix": "t;"}], [{"suffix": ";t"}], [{"prefix": "te;"}]],
        "keep_proxy": [True, False],
        "visibility": ["public", "private"],
        "name_privacy": ["public", "private"],
        "description_privacy": ["public", "private"],
        "avatar_privacy": ["public", "private"],
        "birthday_privacy": ["public", "private"],
        "pronoun_privacy": ["public", "private"],
        "metadata_privacy": ["public", "private"],
    }

    
    from random import choice
    
    member = {}
    for key, value in choices.items():
        i = choice(value)
        member[key] = i
        
    m = Member.from_json(member)
    member = pk.edit_member(member_id=m.id, name=m.name, display_name=m.display_name, 
                            description=m.description, pronouns=m.pronouns, color=m.color, 
                            avatar_url=m.avatar_url, birthday=m.birthday, proxy_tags=m.proxy_tags, 
                            keep_proxy=m.keep_proxy, visibility=m.visibility, 
                            name_privacy=m.name_privacy, description_privacy=m.description_privacy, 
                            avatar_privacy=m.avatar_privacy, birthday_privacy=m.birthday_privacy, 
                            pronoun_privacy=m.pronoun_privacy, metadata_privacy=m.metadata_privacy)
        
    try:
        assert member._deep_equal(other=m, new_member=True) is True
    except AssertionError:
        for key, value in member.__dict__.items():
            if key not in ("id", "created"):
                try:
                    assert value == m.__dict__[key]
                except AssertionError as e:
                    print(f"Error occured at {key}: {value}")
                    assert value == m.__dict__[key]

def test_new_member():
    
    new_member_info = {
              "id":"gaznz",
              "name":"Tester T. Testington",
              "color": None,
              "display_name": None,
              "birthday": None,
              "pronouns": None,
              "avatar_url": None,
              "description":"Here is an example of another member, albeit with less properties set." 
              " It's possible to have members without proxy tags - useful for record-keeping.",
              "proxy_tags":[],
              "keep_proxy": False,
              "privacy":None,
              "visibility":None,
              "name_privacy":None,
              "description_privacy":None,
              "birthday_privacy":None,
              "pronoun_privacy":None,
              "avatar_privacy":None,
              "metadata_privacy":None,
              "created":"2020-01-12T02:21:26.274746Z"
              }
    new_member = Member.from_json(new_member_info)
    
    member = pk.new_member(name=new_member.name, color=new_member.color, 
                           display_name=new_member.display_name, 
                           birthday=new_member.birthday, pronouns=new_member.pronouns, 
                           avatar_url=new_member.avatar_url, description=new_member.description, 
                           visibility=new_member.visibility, name_privacy=new_member.name_privacy, 
                           birthday_privacy=new_member.birthday_privacy, 
                           keep_proxy=new_member.keep_proxy, proxy_tags=new_member.proxy_tags, 
                           pronoun_privacy=new_member.pronoun_privacy, 
                           description_privacy=new_member.description_privacy, 
                           metadata_privacy=new_member.metadata_privacy, 
                           avatar_privacy=new_member.avatar_privacy)
    try:
        assert member._deep_equal(other=new_member, new_member=True) is True
    except AssertionError:
        for key, value in member.__dict__.items():
            if key not in ("id", "created"):
                try:
                    assert value == new_member.__dict__[key]
                except AssertionError:
                    try:
                        pk.delete_member(member.id)
                    except:
                        print(f"Unable to delete member {member.id}")
                    print(f"Error occured at {key}: {value}")
                    assert value == new_member.__dict__[key]
            
    pk.delete_member(member.id)
        
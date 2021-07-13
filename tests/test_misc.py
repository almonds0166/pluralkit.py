import os,sys, pathlib
currentdir = pathlib.Path(__file__).parent
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 

from pluralkit import Client

token = os.environ['TOKEN']
pk = Client(token, async_mode=False)

def test_new_switch():
    members = ["daoof", "cewel", "irqkk", "xadsg"]
    fronters = pk.get_fronters()
    for member in members:
        if not [member] == fronters:
            pk.new_switch([member])

def test_get_message():
    pk.get_message(860690364317958164)
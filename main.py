import asyncio
from pluralkit import Client

async def main(pk):
   print(await pk.get_member("cewel"))

pk = Client(token="o47dXs8ITV0Dgak65PKI/eagWm+g6Vatse7uOGo/zwfshSodaT7E/1ona/7wxID2") # your token here

loop = asyncio.get_event_loop()
loop.run_until_complete(main(pk))
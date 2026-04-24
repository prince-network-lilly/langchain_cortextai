from light_client import LIGHTClient
client=LIGHTClient()

CORTEX_BASE = "https://api.cortex.lilly.com"
comp_res = client.post(
        f"{CORTEX_BASE}/model/ask/mydemo-prince-l103669?default_knowledge=true",
        data={"q": "hi there!"})

res=comp_res.json()
print(res)
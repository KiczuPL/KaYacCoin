import json
import random

from pydantic import BaseModel


class MyModel(BaseModel):
    nonce: int


nonce = random.getrandbits(64)
c = MyModel(nonce=nonce)

# Możesz określić precyzję podczas konwersji na JSON
json_data = json.dumps({"nonce": nonce}, separators=(',', ':'), indent=2)
print(nonce)
print(c.model_dump_json())
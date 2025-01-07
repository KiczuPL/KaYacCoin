import json

import requests

ports = [2000, 2001, 2002, 2003, 2004, 2005]

chains = []

for i, port in enumerate(ports):
    url = f"http://localhost:{port}/allBlocks"
    response = requests.request("GET", url, verify=False)
    body = response.json()
    chains.append(body)

min_chain_length = min([len(chain) for chain in chains])

c = [chain[:min_chain_length] for chain in chains]

print(c[0])
print(c[1])
print(c[2])
print(c[3])

print(f"Is fork free: {json.dumps(c[0]) == json.dumps(c[1]) == json.dumps(c[2]) == json.dumps(c[3]) == json.dumps(c[4]) == json.dumps(c[5])}")

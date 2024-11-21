from state.block_data import BlockData

x: BlockData = BlockData(index=1, previous_hash="0", timestamp="2021-01-01", nonce=0, transactions=[])

print(x.model_dump_json())
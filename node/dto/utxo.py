from typing import List


class UTxO:
    txOutId: str
    txOutIndex: int
    amount: int


class GetBalanceDTO:
    balance: int
    uTxOs: List[UTxO]

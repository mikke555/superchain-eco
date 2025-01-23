from ens import ENS
from web3 import HTTPProvider, Web3

from modules.config import ethereum


class ENS:
    w3 = Web3(HTTPProvider(ethereum.rpc_url))
    ns = ENS.from_web3(w3)

    @classmethod
    def get_ens(cls, address):
        return cls.ns.name(address)

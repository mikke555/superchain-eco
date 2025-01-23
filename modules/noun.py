import random

from web3 import HTTPProvider, Web3

from modules.config import NOUNS_DESCRIPTOR_V2, NOUNS_SEEDER, NOUNS_SEEDER_ABI, ethereum


class Noun:
    w3 = Web3(HTTPProvider(ethereum.rpc_url))
    noun_seeder = w3.to_checksum_address(NOUNS_SEEDER)
    noun_descriptor = w3.to_checksum_address(NOUNS_DESCRIPTOR_V2)
    noun_seeder_contract = w3.eth.contract(NOUNS_SEEDER, abi=NOUNS_SEEDER_ABI)

    @classmethod
    def generate_seed(self) -> tuple:
        noun_id = random.randint(0, 2048)  # any valid uint256
        seed = self.noun_seeder_contract.functions.generateSeed(
            noun_id, self.noun_descriptor
        ).call()

        return seed

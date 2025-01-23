from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import HTTPProvider, Web3
from web3.contract import Contract
from web3.exceptions import Web3Exception, Web3RPCError
from web3.middleware import ExtraDataToPOAMiddleware

from models.network import Network
from modules.config import ERC20_ABI, optimism
from modules.http import HttpClient
from modules.logger import logger


class Wallet(HttpClient):
    def __init__(
        self,
        pk: str,
        counter: str = None,
        proxy: str = None,
        chain: Network = optimism,
    ):
        super().__init__(proxy=proxy)
        self.account = Account.from_key(pk)
        self.address = self.account.address
        self.label = f"{counter} {self.address} |"

        self.chain = chain
        self.w3 = Web3(HTTPProvider(chain.rpc_url))

        self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

    def __str__(self) -> str:
        return f"Wallet(address={self.address})"

    def sign_message(self, message: str) -> str:
        message_encoded = encode_defunct(text=message)
        signed_message = self.account.sign_message(message_encoded)
        return "0x" + signed_message.signature.hex()

    def get_contract(self, address: str, abi: dict = None) -> Contract:
        contract_address = self.w3.to_checksum_address(address)
        if not abi:
            abi = ERC20_ABI

        return self.w3.eth.contract(address=contract_address, abi=abi)

    def get_token(self, token_address: str = None) -> dict:
        token = self.get_contract(token_address)

        return {
            "address": token.address,
            "name": token.functions.name().call(),
            "symbol": token.functions.symbol().call(),
            "decimals": token.functions.decimals().call(),
        }

    def get_balance(self, token_address: str = None) -> int:
        if token_address == None:
            balance = self.w3.eth.get_balance(self.address)
        else:
            token = self.get_contract(token_address)
            balance = token.functions.balanceOf(self.address).call()

        return balance

    def get_gas(self, tx: dict) -> dict:
        gas_price_legacy = self.w3.eth.gas_price
        max_priority_fee = self.w3.eth.max_priority_fee
        latest_block = self.w3.eth.get_block("latest")
        base_fee = int(max(gas_price_legacy, latest_block["baseFeePerGas"]))

        max_fee_per_gas = max_priority_fee + base_fee

        if self.chain.eip_1559:
            tx["maxFeePerGas"] = max_fee_per_gas
            tx["maxPriorityFeePerGas"] = max_priority_fee

        else:
            tx["gasPrice"] = gas_price_legacy

        tx["gas"] = self.w3.eth.estimate_gas(tx)

        return tx

    def get_tx_data(self, value=0, get_gas=False, **kwargs):
        tx = {
            "chainId": self.w3.eth.chain_id,
            "from": self.address,
            "nonce": self.w3.eth.get_transaction_count(self.address),
            "value": value,
            **kwargs,
        }

        return self.get_gas(tx) if get_gas else tx

    def sign_tx(self, tx):
        return self.w3.eth.account.sign_transaction(tx, self.account.key)

    def send_tx(
        self,
        tx,
        tx_label="",
    ):
        try:
            signed_tx = self.sign_tx(tx)

            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            logger.info(f"{tx_label} | {self.chain.explorer}/tx/0x{tx_hash.hex()}")

            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=400)

            if tx_receipt.status:
                logger.success(f"{tx_label} | Tx confirmed \n")
                return tx_receipt.status, tx_hash.hex()
            else:
                raise Exception(f"{tx_label} | Tx Failed \n")

        except Web3RPCError as err:
            if "insufficient funds" in str(err):
                logger.error(f"{tx_label} | Insufficient funds \n")

        except Web3Exception as err:
            logger.error(f"{tx_label} | {err} \n")

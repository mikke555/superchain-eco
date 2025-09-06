import random
import secrets
import time
from datetime import datetime, timezone

from eth_account import Account
from faker import Faker
from web3 import constants
from web3.types import TxReceipt

import settings
from models.responses.bages import BadgesResponse
from models.responses.claim import ClaimResponse
from modules.config import (
    SAFE4337_MODULE,
    SAFE_L2,
    SAFE_L2_ABI,
    SAFE_PROXY_FACTORY,
    SAFE_PROXY_FACTORY_ABI,
    SUPERCHAIN_ACCOUNT_SETUP,
    SUPERCHAIN_ACCOUNT_SETUP_ABI,
    SUPERCHAIN_GUARD,
    SUPERCHAIN_MODULE,
    SUPERCHAIN_MODULE_ABI,
    optimism,
)
from modules.ens import ENS
from modules.logger import logger
from modules.noun import Noun
from modules.utils import ether, random_sleep, wei, write_to_csv
from modules.wallet import Wallet


class Safe(Wallet):
    def __init__(self, pk, counter, proxy, chain=optimism):
        super().__init__(pk, counter, proxy, chain)

    # Utility methods
    def get_superchain_account(self) -> str:
        contract = self.get_contract(SUPERCHAIN_MODULE, abi=SUPERCHAIN_MODULE_ABI)
        return contract.functions.getUserSuperChainAccount(self.address).call()[0]

    def get_username(self) -> str:
        ens_domain = ENS.get_ens(self.address)
        return ens_domain[:-4] if ens_domain else Faker().user_name()

    def encode_setup_data(self) -> bytes:
        contract = self.get_contract(address=SUPERCHAIN_ACCOUNT_SETUP, abi=SUPERCHAIN_ACCOUNT_SETUP_ABI)

        data = contract.encode_abi(
            # fmt: off
            "setupSuperChainAccount",
            args=(
                [SAFE4337_MODULE],          # modules (address[])
                SUPERCHAIN_MODULE,          # superChainModule (address)
                SUPERCHAIN_GUARD,           # guard (address)
                self.address,               # owner (address)
                Noun.generate_seed(),       # seed (tuple)
                self.get_username(),        # superChainID (string)
            ),
        )
        return data  # fmt: on

    def encode_initializer(self) -> bytes:
        contract = self.get_contract(SAFE_L2, abi=SAFE_L2_ABI)
        setup_data_bytes = self.encode_setup_data()

        data = contract.encode_abi(
            # fmt: off
            "setup",
            args=(  
                [self.address],             # _owners (address[])
                1,                          # _threshold (uint256)
                SUPERCHAIN_ACCOUNT_SETUP,   # to (address)
                setup_data_bytes,           # data (bytes)
                SAFE4337_MODULE,            # fallbackHandler (address)
                constants.ADDRESS_ZERO,     # paymentToken (address)
                0,                          # payment (uint256)
                constants.ADDRESS_ZERO,     # paymentReceiver (address)
            ),
        )
        return data  # fmt: on

    def create_account(self) -> TxReceipt:
        """Function: createProxyWithNonce(address _singleton,bytes initializer,uint256 saltNonce)"""
        contract = self.get_contract(SAFE_PROXY_FACTORY, abi=SAFE_PROXY_FACTORY_ABI)
        initializer = self.encode_initializer()

        contract_tx = contract.functions.createProxyWithNonce(
            SAFE_L2,  # _singleton (address)
            initializer,  # initializer (bytes)
            0,  # saltNonce (uint256)
        ).build_transaction(self.get_tx_data())

        return self.send_tx(contract_tx, tx_label=f"{self.label} Create account")

    # API requests
    def get_auth_token(self) -> None:
        logger.debug(f"{self.label} Getting session cookie")
        self.get("/auth/session")

    def get_nonce(self) -> str:
        logger.debug(f"{self.label} Querying nonce")
        resp = self.get("/auth/nonce")

        if resp.status_code == 200:
            return resp.text

        raise Exception(f"Failed to get nonce")

    def get_message(self) -> str:
        dt_now = datetime.now(timezone.utc)
        ms = str(dt_now.microsecond).zfill(6)[:3]
        timestamp = f"{dt_now:%Y-%m-%dT%H:%M:%S}.{ms}Z"

        return (
            "account.superchain.eco wants you to sign in with your Ethereum account:\n"
            f"{self.address}\n\n"
            "Welcome to SuperAccounts!\n"
            "Please sign this message\n\n"
            "URI: https://account.superchain.eco\n"
            "Version: 1\n"
            "Chain ID: 10\n"
            f"Nonce: {self.get_nonce()}\n"
            f"Issued At: {timestamp}"
        )

    def login(self) -> None:
        message = self.get_message()
        signature = self.sign_message(message)

        logger.debug(f"{self.label} Signing in")

        endpoint = "/auth/verify"
        payload = {"message": message, "signature": signature}

        resp = self.post(endpoint, json=payload)

        if resp.status_code != 200:
            raise Exception(f"Failed to authorize")

        token = resp.json()["token"]
        self.headers.update({"Authorization": f"Bearer {token}"})

    def get_points(self, safe_address) -> int:
        resp = self.get(f"/api/user/{safe_address}/badges")
        badges = BadgesResponse(currentBadges=resp.json()["currentBadges"])

        # Check if wallet has any badges at all
        if not badges.currentBadges:
            logger.warning(f"{self.label} No badges found, skipping CSV write")
            return 0

        # Collect badge data
        badge_data = [self.address]
        for badge_id in settings.BADGE_IDS_TO_CHECK:
            badge = badges.get_badge_by_id(badge_id)
            if badge:
                # Handle None currentCount by using 0 as default
                current_count = badge.currentCount if badge.currentCount is not None else 0
                logger.info(f"{self.label} Badge: {badge.metadata.name} {badge.tier} {current_count}")
                badge_data.extend([badge.metadata.name, current_count])
            else:
                # Add empty values for missing badges to maintain consistency
                badge_data.extend(["", 0])

        write_to_csv(
            path=f"reports/{datetime.today():%Y-%m-%d}.csv",
            headers=None,
            data=badge_data,
        )

        total_points = badges.total_points()
        logger.debug(f"{self.label} Total points: {total_points} \n")

        return total_points

    def claim_badges(self, safe_address) -> None:
        max_attempts = 10
        retry = 0

        while True:
            retry += 1

            logger.debug(f"{self.label} Attempting to claim {retry}/{max_attempts}")
            resp = self.post(f"/api/user/{safe_address}/badges/claim")

            if resp.status_code == 201:
                data = ClaimResponse(**resp.json())

                if not data.updatedBadges:
                    logger.warning(f"{self.label} No new badges to claim")
                    return

                for badge in data.updatedBadges:
                    logger.success(f"{self.label} Claimed: {badge.metadata.name} tier {badge.claimableTier}")

                if data.totalPoints:
                    logger.success(f"{self.label} Claimed: {data.totalPoints} points")

                if data.isLevelUp:
                    logger.success(f"{self.label} Level up: {data.isLevelUp}")

                break  # Exit the loop on successful claim

            else:
                logger.error(f"{self.label} Unable to claim: <{resp.status_code}> {resp.text}")

            if retry >= max_attempts:
                logger.error(f"{self.label} Exceeded max attempts ({max_attempts})")
                break

            time.sleep(5)

    # Actions
    def init(self) -> bool:
        account_addr = self.get_superchain_account()

        if account_addr != constants.ADDRESS_ZERO:
            logger.warning(f"{self.label} Account exists")
        else:
            if not self.create_account():
                return False

            while True:
                account_addr = self.get_superchain_account()

                if account_addr != constants.ADDRESS_ZERO:
                    break
                time.sleep(5)

        # API requests
        self.get_auth_token()
        self.login()
        self.claim_badges(account_addr)
        points = self.get_points(account_addr)

        write_to_csv(
            path=f"log/{datetime.today().strftime('%Y-%m-%d')}.csv",
            headers=["address", "points"],
            data=[self.address, points],
        )

        return True

    def fund_account(self) -> TxReceipt:
        account_addr = self.get_superchain_account()

        if account_addr == constants.ADDRESS_ZERO:
            return

        min_wei, max_wei = [wei(val) for val in settings.FUND_VALUE]
        transfer_value = random.randint(min_wei, max_wei)
        balance = self.get_balance()

        if transfer_value > balance:
            logger.warning(f"{self.label} Amount {transfer_value / 10**18:.6f} exceeds wallet balance \n")
            return False

        tx = self.get_tx_data(value=transfer_value, to=account_addr, get_gas=True)

        return self.send_tx(
            tx,
            tx_label=f"{self.label} Fund with {ether(transfer_value):.6f} ETH",
        )

    def create_approved_hash_signature(self, signer_address: str) -> bytes:
        """
        Create a 65-byte signature for Gnosis Safe's "approved hash" scheme.
        The final byte is set to 0x01, marking it as an 'approved hash' signature.
        """
        # Strip the '0x' and convert to raw bytes
        signer_bytes = bytes.fromhex(signer_address[2:])

        # Pad the 20-byte address to 32 bytes
        address_padded = b"\x00" * 12 + signer_bytes  # 12 zero bytes + 20-byte address

        # For "approved hash", r = s = 0 and the last byte = 0x01 (signature type)
        # So total = address_padded (32 bytes) + 32 zero bytes + 1-byte signature type
        signature = address_padded + (b"\x00" * 32) + b"\x01"

        return signature

    def withdraw_funds(self) -> TxReceipt:
        account = self.get_superchain_account()
        balance = self.w3.eth.get_balance(account)

        if account == constants.ADDRESS_ZERO:
            logger.warning(f"{self.label} Account does not exist \n")
            return False

        if not balance:
            logger.warning(f"{self.label} No balance to withdraw \n")
            return False

        account_contract = self.get_contract(account, abi=SAFE_L2_ABI)
        contract_tx = account_contract.functions.execTransaction(
            self.address,  # to (address)
            balance,  # value (uint256)
            "0x",  # data (bytes)
            0,  # operation (uint256)
            0,  # safeTxGas (uint256)
            0,  # baseGas (uint256)
            0,  # gasPrice (uint256)
            constants.ADDRESS_ZERO,  # gasToken (address)
            constants.ADDRESS_ZERO,  # refundReceiver (address)
            self.create_approved_hash_signature(self.address),  # signatures (bytes)
        ).build_transaction(self.get_tx_data())

        return self.send_tx(contract_tx, tx_label=f"{self.label} Withdraw funds")

    def disperse(self) -> bool:
        account = self.get_superchain_account()
        balance = self.w3.eth.get_balance(account)

        if account == constants.ADDRESS_ZERO:
            logger.warning(f"{self.label} Account does not exist \n")
            return False

        if not balance:
            logger.warning(f"{self.label} No balance to disperse \n")
            return False

        num_accounts_to_create = random.randint(*settings.DISPERSE_RECIPIENTS)

        for index in range(num_accounts_to_create):
            private_key = "0x" + secrets.token_hex(32)
            recipient = Account.from_key(private_key).address

            logger.debug(f"{self.label} New EOA created")
            logger.debug(f"{self.label} Pk: {private_key}")
            logger.debug(f"{self.label} Address: {recipient}")

            val_range = [wei(val) for val in settings.DISPERSE_VALUE]
            transfer_value = random.randint(*val_range)

            account_contract = self.get_contract(account, abi=SAFE_L2_ABI)
            contract_tx = account_contract.functions.execTransaction(
                recipient,  # to (address)
                transfer_value,  # value (uint256)
                "0x",  # data (bytes)
                0,  # operation (uint256)
                0,  # safeTxGas (uint256)
                0,  # baseGas (uint256)
                0,  # gasPrice (uint256)
                constants.ADDRESS_ZERO,  # gasToken (address)
                constants.ADDRESS_ZERO,  # refundReceiver (address)
                self.create_approved_hash_signature(self.address),  # signatures (bytes)
            ).build_transaction(self.get_tx_data())

            tx_status = self.send_tx(
                contract_tx,
                tx_label=f"{self.label} Send ETH to recipient {index+1}",
            )

            if tx_status and index <= num_accounts_to_create:
                random_sleep(*settings.SLEEP_BETWEEN_ACTIONS)

        return True

    def run_full_flow(self):
        if not self.init():
            return
        random_sleep(*settings.SLEEP_BETWEEN_ACTIONS)

        if not self.fund_account():
            return
        random_sleep(*settings.SLEEP_BETWEEN_ACTIONS)

        if not self.disperse():
            return
        random_sleep(*settings.SLEEP_BETWEEN_ACTIONS)

        self.withdraw_funds()

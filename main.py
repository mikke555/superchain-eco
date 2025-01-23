import random

import questionary
from questionary import Choice

import settings
from modules.logger import logger
from modules.safe import Safe
from modules.utils import read_file, sleep


def get_action() -> str:
    choices = [
        Choice("Full flow", "full"),
        Choice("Create account and claim badges", "init"),
        Choice("Fund account", "fund"),
        Choice("Withdraw funds", "withdraw"),
        Choice("Disperse dust", "disperse"),
        Choice("Quit", "quit"),
    ]

    custom_style = questionary.Style(
        [
            ("qmark", "fg:#47A6F9 bold"),
            ("pointer", "fg:#47A6F9 bold"),
            ("selected", "fg:#47A6F9"),
            ("highlighted", "fg:#808080"),
            ("answer", "fg:#808080 bold"),
            ("instruction", "fg:#8c8c8c italic"),
        ]
    )

    action = questionary.select(
        "SUPERCHAIN ECO Account:",
        choices=choices,
        style=custom_style,
    ).ask()

    return action


def get_accounts() -> list[dict]:
    keys = read_file("keys.txt")
    proxies = read_file("proxies.txt", prefix="http://")

    accounts = [
        {
            "pk": key,
            "proxy": proxies[index % len(proxies)] if settings.USE_PROXY else None,
        }
        for index, key in enumerate(keys)
    ]

    if settings.SHUFFLE_WALLETS:
        random.shuffle(accounts)

    if not settings.USE_PROXY:
        logger.warning("You are not using proxies")

    return accounts


def main():
    action = get_action()
    accounts = get_accounts()

    for index, account in enumerate(accounts, start=1):
        safe = Safe(**account, counter=f"[{index}/{len(accounts)}]")

        try:
            (action == "full") and safe.run_full_flow()
            (action == "init") and safe.init()
            (action == "fund") and safe.fund_account()
            (action == "withdraw") and safe.withdraw_funds()
            (action == "disperse") and safe.disperse()
            (action == "quit" or action == None) and quit()

            if index < len(accounts):
                sleep(*settings.SLEEP_BETWEEN_WALLETS)

        except Exception as err:
            logger.error(f"Error processing wallet: {err}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("Cancelled by user")

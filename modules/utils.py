import csv
import os
import random
import time
from datetime import datetime
from decimal import Decimal

from tqdm import tqdm
from web3 import Web3


def wei(value: float | Decimal) -> int:
    return Web3.to_wei(value, "ether")


def ether(value: int) -> Decimal:
    return Web3.from_wei(value, "ether")


def read_file(path: str, prefix: str = ""):
    with open(path) as file:
        rows = [f"{prefix}{row.strip()}" for row in file]
    return rows


def random_sleep(max_time, min_time=1):
    if min_time > max_time:
        min_time, max_time = max_time, min_time

    x = random.randint(min_time, max_time)
    time.sleep(x)


def sleep(sleep_time, to_sleep=None, label="Sleeping"):
    if to_sleep is not None:
        x = random.randint(sleep_time, to_sleep)
    else:
        x = sleep_time

    desc = datetime.now().strftime("%H:%M:%S")

    for _ in tqdm(range(x), desc=desc, bar_format=f"{{desc}} | {label} {{n_fmt}}/{{total_fmt}}"):
        time.sleep(1)

    print()  # line break


def write_to_csv(path, headers, data):
    directory = os.path.dirname(path)

    if directory:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    with open(path, mode="a", newline="") as file:
        writer = csv.writer(file)

        if file.tell() == 0 and headers is not None:
            writer.writerow(headers)

        writer.writerow(data)

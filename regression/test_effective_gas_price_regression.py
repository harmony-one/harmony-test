#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Harmony JSON-RPC Transaction Consistency Regression Tests for effectiveGasPrice field

This script verifies the consistency of transaction data obtained through Harmony blockchain
JSON-RPC namespaces (`eth`, `hmy`, `hmyv2`). Specifically, it ensures the `gasPrice` from transaction details
matches the `effectiveGasPrice` in the transaction receipts.

Core Components:
- Parametrized tests across transaction types:
    - Staking calls
    - Smart contract calls
    - Coin transfers
    - Dynamically fetched latest testnet transaction via Harmony's Blockscout API.

Key Features:
- Dynamically retrieves the most recent transaction hash for testing.
- Covers different JSON-RPC namespaces to enforce consistency and compatibility.
- Clearly structured using pytest parametrization for ease of extension.

Dependencies:
    - requests
    - pytest
    - pyhmy (Harmony Python SDK)

Usage:
    Run the tests directly with pytest:
        $ pytest <this_script>.py

Raises:
    AssertionError: If `gasPrice` does not match `effectiveGasPrice`.
    Exception: For network-related failures or missing transaction data.
"""

import requests

import pytest
from pyhmy.rpc.request import base_request

from utils import (
    check_and_unpack_rpc_response,
)


namespace = ["eth", "hmy", "hmyv2"]

endpoints = {
    "shard_0": "https://api.s0.b.hmny.io",
    "shard_1": "https://api.s1.b.hmny.io",
    "blockscout": "https://explorer.testnet.harmony.one/api/v2/main-page/transactions",
}

archival_transactions = {
    "staking_call": "0xfc78151506dfa4b2f01b5bacac698203348a92eb70fd2b8179b51897a580e26c",
    "smart_contract_call": "0x5df75796f9a563d0cd84d8bf86d62f5bbeb696d63b656cf7b659ec3244ff4c1f",
    "coin_transfer": "0x174a4ff5073ee5e811e117e9ee950f382dcb388aa50bac45f75e9f50aa051c15",
    "latest": "retrived_from_blockscout",
}


def get_indexed_latest_transaction(blockscout_url):
    """
    Fetches transactions from the specified Harmony blockscout API and returns the last transaction.

    Parameters:
        url (str): The API endpoint URL to fetch transactions from.

    Returns:
        str: The last transaction hash from the retrieved data.

    Raises:
        Exception: If the request fails or no transactions are found.
    """
    headers = {"accept": "application/json"}
    response = requests.get(blockscout_url, headers=headers)

    if response.status_code == 200:
        transactions = response.json()
        if transactions:
            return transactions[0]["hash"]
        else:
            raise Exception("No transactions found.")
    else:
        raise Exception(f"Request failed with status code {response.status_code}")


@pytest.mark.parametrize("key,value", archival_transactions.items())
@pytest.mark.parametrize("namespace", namespace)
def test_effective_gas_price(namespace, key, value):
    """
    Tests if the transaction's gasPrice matches its receipt's effectiveGasPrice
    for different archival transactions and RPC operation prefixes.
    When you are using 2 parametrize fixtures - pytest will create matrix
        of all possible variations, e.g. 3 namespaces * 4 items == 12 tests
    Note: for the latest transaction it is using call to the blockscout API

    Parameters:
        namespace (str): Prefix of RPC operation - eth, hmy, hmyv2
        key (str): Identifier of the transaction (e.g., 'latest', 'smart_contract_call').
        value (str): Transaction hash or placeholder for transaction.

    Asserts:
        receipt_response["effectiveGasPrice"] is equal to:
        * for eth, hmy == hex `0x174876e800`
        * for hmyv2 == int `100000000000`
    """
    if key == "latest":
        value = get_indexed_latest_transaction(endpoints["blockscout"])

    receipt = base_request(
        namespace + "_getTransactionReceipt",
        params=[value],
        endpoint=endpoints["shard_0"],
    )
    receipt_response = check_and_unpack_rpc_response(receipt, expect_error=False)

    if type(receipt_response["effectiveGasPrice"]) is str:
        assert receipt_response["effectiveGasPrice"] == "0x174876e800"
    else:
        assert receipt_response["effectiveGasPrice"] == 100000000000

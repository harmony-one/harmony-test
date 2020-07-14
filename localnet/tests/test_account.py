#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
import json
import traceback

import pytest
from pyhmy.rpc.request import (
    base_request
)

from txs import (
    tx_timeout,
    endpoints,
    initial_funding,
    assert_valid_test_from_address
)
from utils import (
    is_valid_json_rpc,
    check_and_unpack_rpc_response,
    assert_valid_json_structure
)


@pytest.fixture(scope="module")
def account_test_tx():
    """
    Fixture to send (if needed) and return a transaction to be
    used for all tests in this test module.
    """

    def get_transaction():
        raw_response = base_request('hmy_getTransactionByHash', params=[test_tx["hash"]],
                                    endpoint=endpoints[test_tx["from-shard"]])
        return check_and_unpack_rpc_response(raw_response, expect_error=False)

    test_tx = {
        "from": "one1v92y4v2x4q27vzydf8zq62zu9g0jl6z0lx2c8q",
        "to": "one1s92wjv7xeh962d4sfc06q0qauxak4k8hh74ep3",
        "amount": "1000",
        "from-shard": 0,
        "to-shard": 0,
        "hash": "0xad262f6e399bd15e4cf3bc1717a481db6b595ace025bb1803021602067b43bbc",
        "nonce": "0x0",
        "signed-raw-tx": "0xf86e80843b9aca008252088080948154e933c6cdcba536b04e1fa03c1de1bb6ad8f7893635c9adc5dea000008028a0642d2d1a6b4e1049fccc23431bcd27fa19f249c27657ffca3653950b50bbde7aa06c8cc31c0fdeb6e1c80fc1a69d721de29a9830edff23b5af561d240c1df96179",
    }

    in_initially_funded = False
    for tx in initial_funding:
        if tx["to"] == test_tx["from"] and tx["to-shard"] == test_tx["from-shard"]:
            in_initially_funded = True
            break
    if not in_initially_funded:
        raise AssertionError(f"Test transaction from address {test_tx['from']} "
                             f"not found in set of initially funded accounts.")

    tx_response = get_transaction()
    if tx_response is not None:
        return tx_response
    else:
        # Validate tx sender
        assert_valid_test_from_address(test_tx["from"], test_tx["from-shard"], is_staking=False)

        # Send tx
        response = base_request('hmy_sendRawTransaction', params=[test_tx["signed-raw-tx"]],
                                endpoint=endpoints[test_tx["from-shard"]])
        assert is_valid_json_rpc(response), f"Invalid JSON response: {response}"
        # Do not check for errors since resending initial txs is fine & failed txs will be caught in confirm timeout.

        # Confirm tx within timeout window
        start_time = time.time()
        while time.time() - start_time <= tx_timeout:
            tx_response = get_transaction()
            if tx_response is not None:
                return tx_response
        raise AssertionError("Could not confirm initial transactions on-chain.")


def test_get_transactions_count(account_test_tx):
    """
    Note that v1 & v2 have the same responses.
    """
    reference_response = 0

    # Check v1, SENT
    raw_response = base_request("hmy_getTransactionsCount",
                                params=[account_test_tx["to"], "SENT"],
                                endpoint=endpoints[account_test_tx["shardID"]])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    assert response == 0, f"Expected account  {account_test_tx['to']} to have 0 sent transactions"

    # Check v2, SENT
    raw_response = base_request("hmyv2_getTransactionsCount",
                                params=[account_test_tx["to"], "SENT"],
                                endpoint=endpoints[account_test_tx["shardID"]])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    assert response == 0, f"Expected account  {account_test_tx['to']} to have 0 sent transactions"

    # Check v1, RECEIVED
    raw_response = base_request("hmy_getTransactionsCount",
                                params=[account_test_tx["to"], "RECEIVED"],
                                endpoint=endpoints[account_test_tx["shardID"]])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    assert response == 1, f"Expected account  {account_test_tx['to']} to have 1 received transactions"

    # Check v2, RECEIVED
    raw_response = base_request("hmyv2_getTransactionsCount",
                                params=[account_test_tx["to"], "RECEIVED"],
                                endpoint=endpoints[account_test_tx["shardID"]])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    assert response == 1, f"Expected account  {account_test_tx['to']} to have 1 received transactions"

    # Check v1, ALL
    raw_response = base_request("hmy_getTransactionsCount",
                                params=[account_test_tx["to"], "ALL"],
                                endpoint=endpoints[account_test_tx["shardID"]])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    assert response == 1, f"Expected account  {account_test_tx['to']} to have 1 received transactions"

    # Check v2, ALL
    raw_response = base_request("hmyv2_getTransactionsCount",
                                params=[account_test_tx["to"], "ALL"],
                                endpoint=endpoints[account_test_tx["shardID"]])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    assert response == 1, f"Expected account  {account_test_tx['to']} to have 1 received transactions"


def test_get_staking_transactions_count(account_test_tx):
    """
    Note that v1 & v2 have the same responses.
    """
    reference_response = 0

    # Check v1, SENT
    raw_response = base_request("hmy_getStakingTransactionsCount",
                                params=[account_test_tx["to"], "SENT"],
                                endpoint=endpoints[account_test_tx["shardID"]])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    assert response == 0, f"Expected account  {account_test_tx['to']} to have 0 sent transactions"

    # Check v2, SENT
    raw_response = base_request("hmyv2_getStakingTransactionsCount",
                                params=[account_test_tx["to"], "SENT"],
                                endpoint=endpoints[account_test_tx["shardID"]])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    assert response == 0, f"Expected account  {account_test_tx['to']} to have 0 sent transactions"

    # Check v1, RECEIVED
    raw_response = base_request("hmy_getStakingTransactionsCount",
                                params=[account_test_tx["to"], "RECEIVED"],
                                endpoint=endpoints[account_test_tx["shardID"]])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    assert response == 0, f"Expected account  {account_test_tx['to']} to have 1 received transactions"

    # Check v2, RECEIVED
    raw_response = base_request("hmyv2_getStakingTransactionsCount",
                                params=[account_test_tx["to"], "RECEIVED"],
                                endpoint=endpoints[account_test_tx["shardID"]])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    assert response == 0, f"Expected account  {account_test_tx['to']} to have 1 received transactions"

    # Check v1, ALL
    raw_response = base_request("hmy_getStakingTransactionsCount",
                                params=[account_test_tx["to"], "ALL"],
                                endpoint=endpoints[account_test_tx["shardID"]])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    assert response == 0, f"Expected account  {account_test_tx['to']} to have 1 received transactions"

    # Check v2, ALL
    raw_response = base_request("hmyv2_getStakingTransactionsCount",
                                params=[account_test_tx["to"], "ALL"],
                                endpoint=endpoints[account_test_tx["shardID"]])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    assert response == 0, f"Expected account  {account_test_tx['to']} to have 1 received transactions"


def test_get_staking_transaction_history_v1(account_test_tx):
    """
    No staking transactions for the 'to' account of `account_test_tx`.

    This method may not be implemented, skip if this is the case
    """
    reference_response = {
        "staking_transactions": []
    }

    try:
        raw_response = base_request("hmy_getStakingTransactionsHistory",
                                    params=[{
                                        "address": account_test_tx["from"],
                                        "pageIndex": 0,
                                        "pageSize": 1000,
                                        "fullTx": False,
                                        "txType": "ALL",
                                        "order": "ASC"
                                    }],
                                    endpoint=endpoints[initial_funding[0]["from-shard"]])
        response = check_and_unpack_rpc_response(raw_response, expect_error=False)
        assert_valid_json_structure(reference_response, response)

        raw_response = base_request("hmy_getStakingTransactionsHistory",
                                    params=[{
                                        "address": account_test_tx["from"],
                                        "pageIndex": 0,
                                        "pageSize": 1000,
                                        "fullTx": True,
                                        "txType": "ALL",
                                        "order": "ASC"
                                    }],
                                    endpoint=endpoints[initial_funding[0]["from-shard"]])
        response = check_and_unpack_rpc_response(raw_response, expect_error=False)
        assert_valid_json_structure(reference_response, response)

        raw_response = base_request("hmy_getStakingTransactionsHistory",
                                    params=[{
                                        "address": account_test_tx["from"],
                                        "pageIndex": 0,
                                        "pageSize": 1000,
                                        "fullTx": True,
                                        "txType": "ALL",
                                        "order": "DSC"
                                    }],
                                    endpoint=endpoints[initial_funding[0]["from-shard"]])
        response = check_and_unpack_rpc_response(raw_response, expect_error=False)
        assert_valid_json_structure(reference_response, response)
    except Exception as e:
        pytest.skip(traceback.format_exc())
        pytest.skip(f"Exception: {e}")


def test_get_staking_transaction_history_v2(account_test_tx):
    """
    No staking transactions for the 'to' account of `account_test_tx`.
    """
    reference_response = {
        "staking_transactions": []
    }

    raw_response = base_request("hmyv2_getStakingTransactionsHistory",
                                params=[{
                                    "address": account_test_tx["from"],
                                    "pageIndex": 0,
                                    "pageSize": 1000,
                                    "fullTx": False,
                                    "txType": "ALL",
                                    "order": "ASC"
                                }],
                                endpoint=endpoints[initial_funding[0]["from-shard"]])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)

    raw_response = base_request("hmyv2_getStakingTransactionsHistory",
                                params=[{
                                    "address": account_test_tx["from"],
                                    "pageIndex": 0,
                                    "pageSize": 1000,
                                    "fullTx": True,
                                    "txType": "ALL",
                                    "order": "ASC"
                                }],
                                endpoint=endpoints[initial_funding[0]["from-shard"]])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)

    raw_response = base_request("hmyv2_getStakingTransactionsHistory",
                                params=[{
                                    "address": account_test_tx["from"],
                                    "pageIndex": 0,
                                    "pageSize": 1000,
                                    "fullTx": True,
                                    "txType": "ALL",
                                    "order": "DSC"
                                }],
                                endpoint=endpoints[initial_funding[0]["from-shard"]])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)


def test_get_transactions_history_v1():
    reference_response_full = {
        "transactions": [
            {
                "blockHash": "0x28ddf57c43a3d91069d58be0e5cb8daac04261b97dd34d3c5c361f7bd941e657",
                "blockNumber": "0xf",
                "from": "one1zksj3evekayy90xt4psrz8h6j2v3hla4qwz4ur",
                "timestamp": "0x5f0d84e2",
                "gas": "0x5208",
                "gasPrice": "0x3b9aca00",
                "hash": "0x5718a2fda967f051611ccfaf2230dc544c9bdd388f5759a42b2fb0847fc8d759",
                "input": "0x",
                "nonce": "0x0",
                "to": "one1v92y4v2x4q27vzydf8zq62zu9g0jl6z0lx2c8q",
                "transactionIndex": "0x0",
                "value": "0x152d02c7e14af6800000",
                "shardID": 0,
                "toShardID": 0,
                "v": "0x28",
                "r": "0x76b6130bc018cedb9f8891343fd8982e0d7f923d57ea5250b8bfec9129d4ae22",
                "s": "0xfbc01c988d72235b4c71b21ce033d4fc5f82c96710b84685de0578cff075a0a"
            }
        ]
    }

    reference_response_short = {
        "transactions": [
            "0x5718a2fda967f051611ccfaf2230dc544c9bdd388f5759a42b2fb0847fc8d759",
        ]
    }

    address = initial_funding[0]["from"]  # Assumption made that this account has MULTIPLE transactions (to test order)

    # Check short tx
    raw_response = base_request("hmy_getTransactionsHistory",
                                params=[{
                                    "address": address,
                                    "pageIndex": 0,
                                    "pageSize": 1000,
                                    "fullTx": False,
                                    "txType": "ALL",
                                    "order": "ASC"
                                }],
                                endpoint=endpoints[initial_funding[0]["from-shard"]])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response_short, response)

    # Check long tx, ASC
    raw_response = base_request("hmy_getTransactionsHistory",
                                params=[{
                                    "address": address,
                                    "pageIndex": 0,
                                    "pageSize": 1000,
                                    "fullTx": True,
                                    "txType": "ALL",
                                    "order": "ASC"
                                }],
                                endpoint=endpoints[initial_funding[0]["from-shard"]])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response_full, response)
    transactions = response["transactions"]
    if len(transactions) > 1:
        for i in range(1, len(transactions)):
            prev_time, curr_time = int(transactions[i-1]["timestamp"], 16), int(transactions[i]["timestamp"], 16)
            assert prev_time >= curr_time, f"Transactions are not in ascending order for {json.dumps(response)}"

    # Check long tx, DSC
    raw_response = base_request("hmy_getTransactionsHistory",
                                params=[{
                                    "address": address,
                                    "pageIndex": 0,
                                    "pageSize": 1000,
                                    "fullTx": True,
                                    "txType": "ALL",
                                    "order": "DSC"
                                }],
                                endpoint=endpoints[initial_funding[0]["from-shard"]])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response_full, response)
    transactions = response["transactions"]
    if len(transactions) > 1:
        for i in range(1, len(transactions)):
            prev_time, curr_time = int(transactions[i-1]["timestamp"], 16), int(transactions[i]["timestamp"], 16)
            assert prev_time <= curr_time, f"Transactions are not in ascending order for {json.dumps(response)}"


def test_get_transactions_history_v2():
    reference_response_full = {
        "transactions": [
            {
                "blockHash": "0x28ddf57c43a3d91069d58be0e5cb8daac04261b97dd34d3c5c361f7bd941e657",
                "blockNumber": 15,
                "from": "one1zksj3evekayy90xt4psrz8h6j2v3hla4qwz4ur",
                "timestamp": 1594721506,
                "gas": 21000,
                "gasPrice": 1000000000,
                "hash": "0x5718a2fda967f051611ccfaf2230dc544c9bdd388f5759a42b2fb0847fc8d759",
                "input": "0x",
                "nonce": 0,
                "to": "one1v92y4v2x4q27vzydf8zq62zu9g0jl6z0lx2c8q",
                "transactionIndex": 0,
                "value": 100000000000000000000000,
                "shardID": 0,
                "toShardID": 0,
                "v": "0x28",
                "r": "0x76b6130bc018cedb9f8891343fd8982e0d7f923d57ea5250b8bfec9129d4ae22",
                "s": "0xfbc01c988d72235b4c71b21ce033d4fc5f82c96710b84685de0578cff075a0a"
            }
        ]
    }

    reference_response_short = {
        "transactions": [
            "0x5718a2fda967f051611ccfaf2230dc544c9bdd388f5759a42b2fb0847fc8d759",
        ]
    }

    address = initial_funding[0]["from"]  # Assumption made that this account has MULTIPLE transactions (to test order)

    # Check short tx
    raw_response = base_request("hmyv2_getTransactionsHistory",
                                params=[{
                                    "address": address,
                                    "pageIndex": 0,
                                    "pageSize": 1000,
                                    "fullTx": False,
                                    "txType": "ALL",
                                    "order": "ASC"
                                }],
                                endpoint=endpoints[initial_funding[0]["from-shard"]])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response_short, response)

    # Check long tx, ASC
    raw_response = base_request("hmyv2_getTransactionsHistory",
                                params=[{
                                    "address": address,
                                    "pageIndex": 0,
                                    "pageSize": 1000,
                                    "fullTx": True,
                                    "txType": "ALL",
                                    "order": "ASC"
                                }],
                                endpoint=endpoints[initial_funding[0]["from-shard"]])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response_full, response)
    transactions = response["transactions"]
    if len(transactions) > 1:
        for i in range(1, len(transactions)):
            prev_time, curr_time = transactions[i-1]["timestamp"], transactions[i]["timestamp"]
            assert prev_time >= curr_time, f"Transactions are not in ascending order for {json.dumps(response)}"

    # Check long tx, DSC
    raw_response = base_request("hmyv2_getTransactionsHistory",
                                params=[{
                                    "address": address,
                                    "pageIndex": 0,
                                    "pageSize": 1000,
                                    "fullTx": True,
                                    "txType": "ALL",
                                    "order": "DSC"
                                }],
                                endpoint=endpoints[initial_funding[0]["from-shard"]])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response_full, response)
    transactions = response["transactions"]
    if len(transactions) > 1:
        for i in range(1, len(transactions)):
            prev_time, curr_time = transactions[i-1]["timestamp"], transactions[i]["timestamp"]
            assert prev_time <= curr_time, f"Transactions are not in ascending order for {json.dumps(response)}"


def test_get_balances_by_block_number_v1(account_test_tx):
    reference_response = "0x3635c9adc5dea00000"

    raw_response = base_request("hmy_getBalanceByBlockNumber",
                                params=[account_test_tx["to"], account_test_tx["blockNumber"]],
                                endpoint=endpoints[account_test_tx["shardID"]])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    assert response == account_test_tx[
        "value"], f"Expected balance of {account_test_tx['to']} is {account_test_tx['value']}"


def test_get_balances_by_block_number_v2(account_test_tx):
    reference_response = 1000000000000000000000

    raw_response = base_request("hmyv2_getBalanceByBlockNumber",
                                params=[account_test_tx["to"], int(account_test_tx["blockNumber"], 16)],
                                endpoint=endpoints[account_test_tx["shardID"]])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    acc_tx_value = int(account_test_tx["value"], 16)
    assert response == acc_tx_value, f"Expected balance of {account_test_tx['to']} is {acc_tx_value}"

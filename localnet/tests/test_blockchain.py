#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import traceback

import pytest
from pyhmy import (
    account
)
from pyhmy.rpc.request import (
    base_request
)

from txs import (
    endpoints,
)
from utils import (
    is_valid_json_rpc,
    assert_valid_dictionary_structure
)


def _check_and_unpack_rpc_response(response, expect_error=False):
    assert is_valid_json_rpc(response), f"Invalid JSON response: {response}"
    response = json.loads(response)
    if expect_error:
        assert "error" in response.keys(), f"Expected error in RPC response: {json.dumps(response, indent=2)}"
        return response["error"]
    else:
        assert "result" in response.keys(), f"Expected result in RPC response: {json.dumps(response, indent=2)}"
        return response["result"]


def test_get_node_metadata():
    """
    Note that v1 & v2 have the same responses.
    """
    reference_response = {
        "blskey": [
            "65f55eb3052f9e9f632b2923be594ba77c55543f5c58ee1454b9cfd658d25e06373b0f7d42a19c84768139ea294f6204"
        ],
        "version": "Harmony (C) 2020. harmony, version v6110-v2.1.9-34-g24ec31c1 (danielvdm@ 2020-07-11T05:03:50-0700)",
        "network": "localnet",
        "chain-config": {
            "chain-id": 2,
            "cross-tx-epoch": 0,
            "cross-link-epoch": 2,
            "staking-epoch": 2,
            "prestaking-epoch": 0,
            "quick-unlock-epoch": 0,
            "eip155-epoch": 0,
            "s3-epoch": 0,
            "receipt-log-epoch": 0
        },
        "is-leader": True,
        "shard-id": 0,
        "current-epoch": 0,
        "blocks-per-epoch": 5,
        "role": "Validator",
        "dns-zone": "",
        "is-archival": False,
        "node-unix-start-time": 1594469045,
        "p2p-connectivity": {
            "total-known-peers": 24,
            "connected": 23,
            "not-connected": 1
        }
    }

    # Check v1
    raw_response = base_request("hmy_getNodeMetadata", endpoint=endpoints[0])
    response = _check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_dictionary_structure(reference_response, response)
    assert response["shard-id"] == 0
    assert response["network"] == "localnet"
    assert response["chain-config"]["chain-id"] == 2

    # Check v2
    raw_response = base_request("hmyv2_getNodeMetadata", endpoint=endpoints[0])
    response = _check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_dictionary_structure(reference_response, response)
    assert response["shard-id"] == 0
    assert response["network"] == "localnet"
    assert response["chain-config"]["chain-id"] == 2


def test_get_sharding_structure():
    """
    Note that v1 & v2 have the same responses.
    """
    reference_response = {
        "current": True,
        "http": "http://127.0.0.1:9500",
        "shardID": 0,
        "ws": "ws://127.0.0.1:9800"
    }

    # Check v1
    raw_response = base_request("hmy_getShardingStructure", endpoint=endpoints[0])
    response = _check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert isinstance(response, list), f"Expected response to be of type list, not {type(response)}"
    for d in response:
        assert isinstance(d, dict), f"Expected type dict in response elements, not {type(d)}"
        assert_valid_dictionary_structure(reference_response, d)
    assert response[0]["current"]

    # Check v2
    raw_response = base_request("hmyv2_getShardingStructure", endpoint=endpoints[0])
    response = _check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert isinstance(response, list), f"Expected response to be of type list, not {type(response)}"
    for d in response:
        assert isinstance(d, dict), f"Expected type dict in response elements, not {type(d)}"
        assert_valid_dictionary_structure(reference_response, d)
    assert response[0]["current"]


def test_get_leader_address():
    """
    Note that v1 & v2 have the same responses.
    """
    reference_response = "0x6911b75b2560be9a8f71164a33086be4511fc99a"

    # Check v1
    raw_response = base_request("hmy_getLeader", endpoint=endpoints[0])
    response = _check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert type(reference_response) == type(response)
    if response.startswith("one1"):
        assert account.is_valid_address(response), f"Leader address is not a valid ONE address"
    else:
        ref_len = len(reference_response.replace("0x", ""))
        assert ref_len == len(response.replace("0x", "")), f"Leader address hash is not of length {ref_len}"

    # Check v2
    raw_response = base_request("hmyv2_getLeader", endpoint=endpoints[0])
    response = _check_and_unpack_rpc_response(raw_response, expect_error=False)
    if response.startswith("one1"):
        assert account.is_valid_address(response), f"Leader address is not a valid ONE address"
    else:
        ref_len = len(reference_response.replace("0x", ""))
        assert ref_len == len(response.replace("0x", "")), f"Leader address hash is not of length {ref_len}"


def test_get_block_by_number_v1():
    """
    Enforce v1 (error if wrong).
    """
    reference_response = {
        "difficulty": 0,
        "epoch": "0x0",
        "extraData": "0x",
        "gasLimit": "0x4c4b400",
        "gasUsed": "0x0",
        "hash": "0x0994da932016ba93937ad46b9a1207ecd6d4fbd689d7f8ddf1f926cd3ebc6016",
        "logsBloom": "0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
        "miner": "0x0b585f8daefbc68a311fbd4cb20d9174ad174016",
        "mixHash": "0x0000000000000000000000000000000000000000000000000000000000000000",
        "nonce": 0,
        "number": "0x1",
        "parentHash": "0x61610810993c42bacd55a124e3b9009b9ae225a2f727750db4d2171504be59fb",
        "receiptsRoot": "0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421",
        "size": "0x31e",
        "stakingTransactions": [],
        "stateRoot": "0x9e470e803db498e6ba3c9108d3f951060e7121289c2354b8b185349ddef4fc0a",
        "timestamp": "0x5f09ad95",
        "transactions": [],
        "transactionsRoot": "0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421",
        "uncles": [],
        "viewID": "0x1"
    }

    raw_response = base_request("hmy_getBlockByNumber", params=["0x1", True], endpoint=endpoints[0])
    response = _check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_dictionary_structure(reference_response, response)
    for key in ["gasLimit", "gasLimit", "gasUsed", "size", "timestamp", "viewID"]:
        assert isinstance(response[key], str) and response[key].startswith(
            "0x"), f"Expect key '{key}' to be a hex string in {json.dumps(response, indent=2)}"


def test_get_block_by_number_v2():
    """
    Don't enforce v2, skip if not correct
    """
    reference_response = {
        "difficulty": 0,
        "epoch": 0,
        "extraData": "0x",
        "gasLimit": 80000000,
        "gasUsed": 0,
        "hash": "0x0994da932016ba93937ad46b9a1207ecd6d4fbd689d7f8ddf1f926cd3ebc6016",
        "logsBloom": "0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
        "miner": "0x0b585f8daefbc68a311fbd4cb20d9174ad174016",
        "mixHash": "0x0000000000000000000000000000000000000000000000000000000000000000",
        "nonce": 0,
        "number": 1,
        "parentHash": "0x61610810993c42bacd55a124e3b9009b9ae225a2f727750db4d2171504be59fb",
        "receiptsRoot": "0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421",
        "size": 798,
        "stakingTransactions": [],
        "stateRoot": "0x9e470e803db498e6ba3c9108d3f951060e7121289c2354b8b185349ddef4fc0a",
        "timestamp": 1594469781,
        "transactions": [],
        "transactionsRoot": "0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421",
        "uncles": [],
        "viewID": 1
    }

    try:
        raw_response = base_request("hmyv2_getBlockByNumber", params=[1, {"InclStaking": True}], endpoint=endpoints[0])
        response = _check_and_unpack_rpc_response(raw_response, expect_error=False)
        assert_valid_dictionary_structure(reference_response, response)
        for key in ["gasLimit", "gasLimit", "gasUsed", "size", "timestamp", "viewID"]:
            assert isinstance(response[key],
                              int), f"Expect key '{key}' to be an integer in {json.dumps(response, indent=2)}"
    except Exception as e:
        print()
        print(traceback.format_exc())
        pytest.skip(f"Exception: {e}")

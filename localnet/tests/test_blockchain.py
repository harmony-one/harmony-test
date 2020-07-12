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
    assert_valid_dictionary_structure,
    check_and_unpack_rpc_response
)


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
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_dictionary_structure(reference_response, response)
    assert response["shard-id"] == 0
    assert response["network"] == "localnet"
    assert response["chain-config"]["chain-id"] == 2

    # Check v2
    raw_response = base_request("hmyv2_getNodeMetadata", endpoint=endpoints[0])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
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
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert isinstance(response, list), f"Expected response to be of type list, not {type(response)}"
    for d in response:
        assert isinstance(d, dict), f"Expected type dict in response elements, not {type(d)}"
        assert_valid_dictionary_structure(reference_response, d)
    assert response[0]["current"]

    # Check v2
    raw_response = base_request("hmyv2_getShardingStructure", endpoint=endpoints[0])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert isinstance(response, list), f"Expected response to be of type list, not {type(response)}"
    for d in response:
        assert isinstance(d, dict), f"Expected type dict in response elements, not {type(d)}"
        assert_valid_dictionary_structure(reference_response, d)
    assert response[0]["current"]


def test_get_latest_header():
    """
    Note that v1 & v2 have the same responses.
    """
    reference_response = {
        "blockHash": "0x4e9faaf05bd7ed0ed392b3b5b19f2d2df993e60436c94b61b8afae6998b854b5",
        "blockNumber": 83,
        "shardID": 0,
        "leader": "0x6911b75b2560be9a8f71164a33086be4511fc99a",
        "viewID": 83,
        "epoch": 15,
        "timestamp": "2020-07-12 14:25:05 +0000 UTC",
        "unixtime": 1594563905,
        "lastCommitSig": "76e8365fdbd947f74d86f15072546f594f8aaf3f6bf0b085df1d81079b760e17da1666d8d07f5c744e200f81a5fa750901d0dc871a4dbe5461efa779553db3f95785d168701c774b23d2326f0d906e47d534a34c87f4ace5e4ed2242860bfc0e",
        "lastCommitBitmap": "3f",
        "crossLinks": [
            {
                "hash": "0x9dda6ad7fdec1e0f76b87bbea432e12c8668dbb2de9100e87442adfb1c7d1f70",
                "block-number": 80,
                "view-id": 80,
                "signature": "73f8e045c0cee4accfd259a78ea440ef2cf8c95d1c2e0e069725b35034c63e27f4db8ec5e1983d1c21831561967d0101ba556977e047a032e2c0f70bc3dc658ae245cb3392c837aed46119fa95ab39aad4ac926a206ab174304be15bb17df68a",
                "signature-bitmap": "3f",
                "shard-id": 1,
                "epoch-number": 14
            }
        ]
    }

    # Check v1
    raw_response = base_request("hmy_latestHeader", endpoint=endpoints[0])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_dictionary_structure(reference_response, response)
    assert response["shardID"] == 0

    # Check v2
    raw_response = base_request("hmyv2_latestHeader", endpoint=endpoints[0])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_dictionary_structure(reference_response, response)
    assert response["shardID"] == 0


def test_get_latest_chain_headers():
    """
    Note that v1 & v2 have the same responses.
    """
    reference_response = {
        "beacon-chain-header": {
            "shard-id": 0,
            "block-header-hash": "0x127437058641851cdfe10e9509aa060b169acbce79eb63d04e3be2cfbe596695",
            "block-number": 171,
            "view-id": 171,
            "epoch": 33
        },
        "shard-chain-header": {
            "shard-id": 1,
            "block-header-hash": "0x0ca6c681e128f47e35e4c578b6381f3f8dda8ec9fcb0a8935a0bf12a2e7a19a3",
            "block-number": 171,
            "view-id": 171,
            "epoch": 33
        }
    }

    # Check v1
    raw_response = base_request("hmy_getLatestChainHeaders", endpoint=endpoints[1])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_dictionary_structure(reference_response, response)
    assert response["beacon-chain-header"]["shard-id"] == 0
    assert response["shard-chain-header"]["shard-id"] == 1

    # Check v2
    raw_response = base_request("hmyv2_getLatestChainHeaders", endpoint=endpoints[1])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_dictionary_structure(reference_response, response)
    assert response["beacon-chain-header"]["shard-id"] == 0
    assert response["shard-chain-header"]["shard-id"] == 1


def test_get_leader_address():
    """
    Note that v1 & v2 have the same responses.
    """
    reference_response = "0x6911b75b2560be9a8f71164a33086be4511fc99a"

    # Check v1
    raw_response = base_request("hmy_getLeader", endpoint=endpoints[0])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert type(reference_response) == type(response)
    if response.startswith("one1"):
        assert account.is_valid_address(response), f"Leader address is not a valid ONE address"
    else:
        ref_len = len(reference_response.replace("0x", ""))
        assert ref_len == len(response.replace("0x", "")), f"Leader address hash is not of length {ref_len}"

    # Check v2
    raw_response = base_request("hmyv2_getLeader", endpoint=endpoints[0])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    if response.startswith("one1"):
        assert account.is_valid_address(response), f"Leader address is not a valid ONE address"
    else:
        ref_len = len(reference_response.replace("0x", ""))
        assert ref_len == len(response.replace("0x", "")), f"Leader address hash is not of length {ref_len}"


def test_get_block_number():
    """
    Note that v1 & v2 have DIFFERENT responses
    """
    # Check v1
    raw_response = base_request("hmy_blockNumber", endpoint=endpoints[0])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert isinstance(response, str) and response.startswith("0x")  # Must be a hex string

    # Check v2
    raw_response = base_request("hmyv2_blockNumber", endpoint=endpoints[0])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert isinstance(response, int) and int(response)  # Must be an integer in base 10


def test_get_epoch():
    """
    Note that v1 & v2 have DIFFERENT responses
    """
    # Check v1
    raw_response = base_request("hmy_getEpoch", endpoint=endpoints[0])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert isinstance(response, str) and response.startswith("0x")  # Must be a hex string

    # Check v2
    raw_response = base_request("hmyv2_getEpoch", endpoint=endpoints[0])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert isinstance(response, int)  # Must be an integer


def test_get_gas_price():
    """
    Note that v1 & v2 have DIFFERENT responses
    """
    # Check v1
    raw_response = base_request("hmy_gasPrice", endpoint=endpoints[0])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert isinstance(response, str) and response.startswith("0x")  # Must be a hex string

    # Check v2
    raw_response = base_request("hmyv2_gasPrice", endpoint=endpoints[0])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert isinstance(response, int) and int(response)  # Must be an integer in base 10


def test_get_protocol_version():
    """
    Note that v1 & v2 have DIFFERENT responses
    """
    # Check v1
    raw_response = base_request("hmy_protocolVersion", endpoint=endpoints[0])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert isinstance(response, str) and response.startswith("0x")  # Must be a hex string

    # Check v2
    raw_response = base_request("hmyv2_protocolVersion", endpoint=endpoints[0])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert isinstance(response, int) and int(response)  # Must be an integer in base 10


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
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_dictionary_structure(reference_response, response)
    for key in ["gasLimit", "gasLimit", "gasUsed", "size", "timestamp", "viewID"]:
        assert isinstance(response[key], str) and response[key].startswith(
            "0x"), f"Expect key '{key}' to be a hex string in {json.dumps(response, indent=2)}"


def test_get_block_by_number_v2():
    """
    Don't enforce v2 (for now), skip if not correct since input & output format could change.
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
        response = check_and_unpack_rpc_response(raw_response, expect_error=False)
        assert_valid_dictionary_structure(reference_response, response)
        for key in ["gasLimit", "gasLimit", "gasUsed", "size", "timestamp", "viewID"]:
            assert isinstance(response[key],
                              int), f"Expect key '{key}' to be an integer in {json.dumps(response, indent=2)}"
    except Exception as e:
        print()
        print(traceback.format_exc())
        pytest.skip(f"Exception: {e}")


def test_get_header_by_number():
    """
    Enforce v1 AND v2 (error if wrong) -- current behavior of v2 is correct.
    Only difference is param of RPC is hex string in v1 and decimal in v2
    """
    reference_response = {
        "blockHash": "0xb718a66ef2b7764fa75b40bfe7047d015197a65ae4a9c4f2007501825025564c",
        "blockNumber": 1,
        "shardID": 0,
        "leader": "one1pdv9lrdwl0rg5vglh4xtyrv3wjk3wsqket7zxy",
        "viewID": 1,
        "epoch": 0,
        "timestamp": "2020-07-12 14:14:17 +0000 UTC",
        "unixtime": 1594563257,
        "lastCommitSig": "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
        "lastCommitBitmap": "",
        "crossLinks": []
    }

    # Check v1
    raw_response = base_request("hmy_getHeaderByNumber", params=["0x1"], endpoint=endpoints[0])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_dictionary_structure(reference_response, response)
    assert response["shardID"] == 0

    # Check v2
    raw_response = base_request("hmy_getHeaderByNumber", params=["0x1"], endpoint=endpoints[0])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_dictionary_structure(reference_response, response)
    assert response["shardID"] == 0

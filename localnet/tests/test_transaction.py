#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests here are related to send a plain transaction & require a
feedback loop with the chain.

As with all tests, there are 2 JSON-RPC versions/namespaces (v1 & v2) where their difference
is only suppose to be in the types of their params & returns. v1 keeps everything in hex and
v2 uses decimal when possible. However, there are some (legacy) discrepancies that some tests
enforce. These tests are noted and should NOT be broken.
"""
import json
import time

import pytest
from pyhmy.rpc.request import (
    base_request
)
from pyhmy import account

import txs
from txs import (
    tx_timeout,
    endpoints,
    initial_funding,
    get_transaction,
    send_and_confirm_transaction,
)
from utils import (
    check_and_unpack_rpc_response,
    assert_valid_json_structure
)


@pytest.fixture(scope="module")
@txs.cross_shard
def cross_shard_txs():
    """
    Fixture for 2 cross shard transaction.

    Returned list has cx from s0 -> s1 as element 0, cx from s1 -> s0 as element 1.
    """
    s0_test_tx = {
        "from": "one1ue25q6jk0xk3dth4pxur9e742vcqfwulhwqh45",
        "to": "one1t40su52axu207vgc6ymcmwe0xmml4njrskk2vf",
        # erupt concert hat tree anger discover disease town gasp lemon gesture fiber spread season mixture host awake tennis issue orbit member film winter glass
        "amount": "1000",
        "from-shard": 0,
        "to-shard": 1,
        "hash": "0xc0a84ec15fc3391089f20fa6b9cc90c654eb8dd2f6815297de89eef38ce4fe2b",
        "nonce": "0x0",
        "signed-raw-tx": "0xf86e80843b9aca008252088001945d5f0e515d3714ff3118d1378dbb2f36f7face43893635c9adc5dea000008027a03b38081f3ece7725f0a7ed2e6892ec58fb906add07682b0deb3ecc1fab6643d7a050b56eef0037a135b48a2da72a93fd4ce3f32cb1e52ec01e1ab70c8888d9f10a",
    }
    s1_test_tx = {
        "from": "one1t40su52axu207vgc6ymcmwe0xmml4njrskk2vf",
        "to": "one1qljfd3pnfjwr86ll6d0s6khcqhw8969p9l7fw3",
        # faculty pave mad mind siren unfold invite avocado teach engine mimic mouse frown topple match thunder syrup fame material feed occur kit install clog
        "amount": "500",
        "from-shard": 1,
        "to-shard": 0,
        "hash": "0x819b0d7902134dadd07851edba0e8694e60c1aee057a96d2ceb4a9118cee0298",
        "nonce": "0x0",
        "signed-raw-tx": "0xf86e80843b9aca0082520801809407e496c4334c9c33ebffd35f0d5af805dc72e8a1891b1ae4d6e2ef5000008027a06650086393f005a04ca83fb59e228e8ebd642bc293d3698bfc46dc0ee5d872cda00cfca823a0bc32abe40a133345427b81d5382bbe0c4333227c1912dcddd89e99",
    }
    txs = [None, None]  # s0 -> s1 is element 0, s1 -> s0 is element 1

    in_initially_funded = False
    for tx in initial_funding:
        if tx["to"] == s0_test_tx["from"] and tx["to-shard"] == s0_test_tx["from-shard"]:
            in_initially_funded = True
            break
    if not in_initially_funded:
        raise AssertionError(f"Test transaction from address {s0_test_tx['from']} "
                             f"not found in set of initially funded accounts.")

    tx_response = get_transaction(s0_test_tx["hash"], s0_test_tx["from-shard"])
    txs[0] = send_and_confirm_transaction(s0_test_tx) if tx_response is None else tx_response
    start_time = time.time()
    while time.time() - start_time < tx_timeout:
        if account.get_balance(s1_test_tx["from"], endpoint=endpoints[s1_test_tx["from-shard"]]) >= 1e18:
            tx_response = get_transaction(s1_test_tx["hash"], s1_test_tx["from-shard"])
            txs[1] = send_and_confirm_transaction(s1_test_tx) if tx_response is None else tx_response
            return txs
    raise AssertionError(f"Could not confirm cross shard transaction on 'to-shard' "
                         f"(balance not updated) for tx: {json.dumps(s0_test_tx, indent=2)}")


def test_get_pool_stats():
    """
    Note that v1 & v2 have the same responses.
    """
    reference_response = {
        "executable-count": 0,
        "non-executable-count": 0
    }

    raw_response = base_request("hmy_getPoolStats", params=[],
                                endpoint=endpoints[0])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)

    raw_response = base_request("hmyv2_getPoolStats", params=[],
                                endpoint=endpoints[0])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)


@txs.cross_shard
def test_resend_cx(cross_shard_txs):
    """
    Note that v1 & v2 have the same responses.
    """
    reference_response = True

    for tx in cross_shard_txs:
        raw_response = base_request("hmy_resendCx", params=[tx["hash"]],
                                    endpoint=endpoints[tx["shardID"]])
        response = check_and_unpack_rpc_response(raw_response, expect_error=False)
        assert_valid_json_structure(reference_response, response)

        raw_response = base_request("hmyv2_resendCx", params=[tx["hash"]],
                                    endpoint=endpoints[tx["shardID"]])
        response = check_and_unpack_rpc_response(raw_response, expect_error=False)
        assert_valid_json_structure(reference_response, response)


@txs.cross_shard
def test_get_cx_receipt_by_hash_v1(cross_shard_txs):
    reference_response = {
        "blockHash": "0xf12f3aefd7f189286b6da30871a47946c11f9c1673b3b693f9d37d659f69e018",
        "blockNumber": "0x21",
        "hash": "0xc0a84ec15fc3391089f20fa6b9cc90c654eb8dd2f6815297de89eef38ce4fe2b",
        "from": "one1ue25q6jk0xk3dth4pxur9e742vcqfwulhwqh45",
        "to": "one1t40su52axu207vgc6ymcmwe0xmml4njrskk2vf",
        "shardID": 0,
        "toShardID": 1,
        "value": "0x3635c9adc5dea00000"
    }

    raw_response = base_request("hmy_getCXReceiptByHash", params=[cross_shard_txs[0]["hash"]],
                                endpoint=endpoints[cross_shard_txs[0]["toShardID"]])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)


@txs.cross_shard
def test_get_cx_receipt_by_hash_v2(cross_shard_txs):
    reference_response = {
        "blockHash": "0xf12f3aefd7f189286b6da30871a47946c11f9c1673b3b693f9d37d659f69e018",
        "blockNumber": 33,
        "hash": "0xc0a84ec15fc3391089f20fa6b9cc90c654eb8dd2f6815297de89eef38ce4fe2b",
        "from": "one1ue25q6jk0xk3dth4pxur9e742vcqfwulhwqh45",
        "to": "one1t40su52axu207vgc6ymcmwe0xmml4njrskk2vf",
        "shardID": 0,
        "toShardID": 1,
        "value": 1000000000000000000000
    }

    raw_response = base_request("hmyv2_getCXReceiptByHash", params=[cross_shard_txs[0]["hash"]],
                                endpoint=endpoints[cross_shard_txs[0]["toShardID"]])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)


@txs.cross_shard
def test_get_pending_cx_receipts():
    cx = {
        "from": "one19l4hghvh40fyldxfznn0a3ss7d5gk0dmytdql4",
        "to": "one1ds3fayprfl6j7yd6mpwfncj9c0ajmhvmvhnmpm",
        # erupt concert hat tree anger discover disease town gasp lemon gesture fiber spread season mixture host awake tennis issue orbit member film winter glass
        "amount": "1000",
        "from-shard": 0,
        "to-shard": 1,
        "hash": "0x0988bcaecba9cc731245ee7ae9595d1202448413bc6e517b4c0c8da9abb1e479",
        "nonce": "0x0",
        "signed-raw-tx": "0xf86e80843b9aca008252088001946c229e90234ff52f11bad85c99e245c3fb2ddd9b893635c9adc5dea000008027a0fc7e0c3790b7c507749f4286e5b6cc59357129586fc48a326442c27886e0236ba0587c72684d05fad0c1c2111d55d810bc086cd5adf129806a89a019b539b19d26",
    }
    reference_response = [
        {
            "receipts": [
                {
                    "txHash": "0x819b0d7902134dadd07851edba0e8694e60c1aee057a96d2ceb4a9118cee0298",
                    "from": "one1t40su52axu207vgc6ymcmwe0xmml4njrskk2vf",
                    "to": "one1qljfd3pnfjwr86ll6d0s6khcqhw8969p9l7fw3",
                    "shardID": 1,
                    "toShardID": 0,
                    "amount": 500000000000000000000
                }
            ],
            "merkleProof": {
                "blockNum": 35,
                "blockHash": "0xe07abb23824f658f452012f22e2d557a270c320058a39d6c6d5d2d53d1d7e427",
                "shardID": 1,
                "receiptHash": "0xb7f422b693a5cffd3d98b2fd4f9f833e10421bcd6d488e5cd8c2fcbcf1ecd13c",
                "shardIDs": [
                    0
                ],
                "shardHashes": [
                    "0x31db710789deaa5a1721f7bf66d3eabddfbb9e712b5ba6cdc7b183f5d9dc9b51"
                ]
            },
            "header": {
                "shard-id": 1,
                "block-header-hash": "0x2e0295f760bc69cdf840576636f61602f8b13ea5172562837c10a9b6f5fa711e",
                "block-number": 35,
                "view-id": 35,
                "epoch": 5
            },
            "commitSig": "G7oQCfiRJjl8s1i7B2xxPWZefCW5muiqyNY0PwcNOFt2QQkRC95ongKIGuIKCLMAVkDpkZRdC7B0cUoe3tKceT6/9++sxcwPRQ2NBWA/u6Gkl6UneKs4Xzhpuez2MoOG",
            "commitBitmap": "Pw=="
        }
    ]

    if get_transaction(cx["hash"], cx["from-shard"]) is not None:
        pytest.skip(f"Test cross shard transaction (hash {cx['hash']}) already present on chain...")

    response = base_request('hmy_sendRawTransaction', params=[cx["signed-raw-tx"]],
                            endpoint=endpoints[cx["from-shard"]])
    check_and_unpack_rpc_response(response, expect_error=False)

    start_time = time.time()
    v1_success, v2_success = False, False
    while time.time() - start_time <= tx_timeout * 2:  # Cross shards are generally slower...
        if not v1_success:
            raw_response = base_request("hmy_getPendingCXReceipts", endpoint=endpoints[cx["to-shard"]])
            response = check_and_unpack_rpc_response(raw_response, expect_error=False)
            assert_valid_json_structure(reference_response, response)
            for cx_receipt in response:
                for r in cx_receipt["receipts"]:
                    if r["txHash"] == cx["hash"]:
                        v1_success = True

        if not v2_success:
            raw_response = base_request("hmyv2_getPendingCXReceipts", endpoint=endpoints[cx["to-shard"]])
            response = check_and_unpack_rpc_response(raw_response, expect_error=False)
            assert_valid_json_structure(reference_response, response)
            for cx_receipt in response:
                for r in cx_receipt["receipts"]:
                    if r["txHash"] == cx["hash"]:
                        v2_success = True

        time.sleep(0.5)
        if v1_success and v2_success:
            return

    raise AssertionError(f"Timeout! Pending transactions not found for {json.dumps(cx)}")

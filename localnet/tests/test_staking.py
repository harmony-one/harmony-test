#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests here are related to staking functions & require a feedback loop with the chain.

As with all tests, there are 2 JSON-RPC versions/namespaces (v1 & v2) where their difference
is only suppose to be in the types of their params & returns. v1 keeps everything in hex and
v2 uses decimal when possible. However, there are some (legacy) discrepancies that some tests
enforce. These tests are noted and should NOT be broken.
"""
import traceback

import pytest
from pyhmy import (
    transaction,
    blockchain
)
from pyhmy.rpc.request import (
    base_request
)

import txs
from txs import (
    beacon_shard_id,
    initial_funding,
    endpoints,
    send_and_confirm_transaction,
    send_and_confirm_staking_transaction,
    get_transaction,
    get_staking_transaction
)
from utils import (
    check_and_unpack_rpc_response
)


@pytest.fixture(scope="module")
@txs.staking
def s0_validator():
    """
    Fixture for the shard 0 validator (with a running external node).

    Returns the validator's create validator transaction (`stx`)
    """
    stx = {
        "validator-addr": "one109r0tns7av5sjew7a7fkekg4fs3pw0h76pp45e",
        "name": "test",
        "identity": "test0",
        "website": "test",
        "security-contact": "test",
        "details": "test",
        "rate": 0.1,
        "max-rage": 0.9,
        "max-change-rate": 0.05,
        "min-self-delegation": 10000,
        "max-total-delegation": 10000000,
        "amount": 10000,
        "pub-bls-key": "4f41a37a3a8d0695dd6edcc58142c6b7d98e74da5c90e79b587b3b960b6a4f5e048e6d8b8a000d77a478d44cd640270c",
        "hash": "0xf80460f1ad041a0a0e841da717fc5b7959b1a7e9a0ce9a25cd70c0ce40d5ff26",
        "nonce": "0x0",
        "signed-raw-tx": "0xf9015780f90106947946f5ce1eeb290965deef936cd9154c22173efeda8474657374857465737430847465737484746573748474657374ddc988016345785d8a0000c9880c7d713b49da0000c887b1a2bc2ec500008a021e19e0c9bab24000008b084595161401484a000000f1b04f41a37a3a8d0695dd6edcc58142c6b7d98e74da5c90e79b587b3b960b6a4f5e048e6d8b8a000d77a478d44cd640270cf862b8606e1204740c90329827178361b635109e515a2334d970f44f29f3a98ff10bb351d8dd7fa03ceadcbe3e53be7b1bd0940c1e1fc58d2725e4bacf06831974edaf3291dfd5a0aa1e81c8a078e7e5e6cb9e58c750d6005afdd7b1548823804039a2118a021e19e0c9bab240000080843b9aca00835121c427a02348daabe696c4370379b9102dd85da6d4fed52f0f511ff0448a21c001ee75a7a01a67f9f40e0de02b50d5d7295f200fea7f950c1b59aa7efa8d225294c4fdbc5e"
    }

    in_initially_funded = False
    for tx in initial_funding:
        if tx["to"] == stx["validator-addr"] and tx["to-shard"] == beacon_shard_id:
            in_initially_funded = True
            break
    if not in_initially_funded:
        raise AssertionError(f"Test staking transaction from address {stx['validator-addr']} "
                             f"not found in set of initially funded accounts (or not founded on s{beacon_shard_id})")

    if get_staking_transaction(stx["hash"]) is None:
        tx = send_and_confirm_staking_transaction(stx)
        assert tx["hash"] == stx["hash"], f"Expected contract transaction hash to be {stx['hash']}, " \
                                          f"got {tx['hash']}"

    return stx


@pytest.fixture(scope="module")
@txs.staking
def s1_validator():
    """
    Fixture for the shard 1 validator (with a running external node).

    Returns the validator's create validator transaction (`stx`)
    """
    stx = {
        "validator-addr": "one1nmy8quw0924fss4r9km640pldzqegjk4wv4wts",
        "name": "test",
        "identity": "test1",
        "website": "test",
        "security-contact": "test",
        "details": "test",
        "rate": 0.1,
        "max-rage": 0.9,
        "max-change-rate": 0.05,
        "min-self-delegation": 10000,
        "max-total-delegation": 10000000,
        "amount": 10000,
        "pub-bls-key": "5e2f14abeadf0e759beb1286ed6095d9d1b2d64ad394316991161c6f95237710e0a4beda8adeaefde4844ab4c4b2bf98",
        "hash": "0x37743ed5a112e54134d610b18284ab8967c926a2d53eaf23ba836431cf9bd96a",
        "nonce": "0x0",
        "signed-raw-tx": "0xf9015780f90106949ec87071cf2aaa9842a32db7aabc3f6881944ad5da8474657374857465737431847465737484746573748474657374ddc988016345785d8a0000c9880c7d713b49da0000c887b1a2bc2ec500008a021e19e0c9bab24000008b084595161401484a000000f1b05e2f14abeadf0e759beb1286ed6095d9d1b2d64ad394316991161c6f95237710e0a4beda8adeaefde4844ab4c4b2bf98f862b860e8bc184c4d5779ab7ab9fb8902b157b1257b1c4fa7e39649b2d900f0415f3aec0701f89e6840d42854559620627e871862b7b5075fad456fb43bc9eb5811c5b305d1d82838332623b109fbc033fd144387bb402e3bd1626a640b58d0b3ae66098a021e19e0c9bab240000080843b9aca008351220427a0d9d4bfabdc1dd7c63c951e0353d0fdee583e9cf55dcd0253aa6eb2d1066ccb2aa0202841a6ebc536d04ca7ae2ea1d83d4d2c5d1ef1af879202613b60ee2304b27b"
    }

    in_initially_funded = False
    for tx in initial_funding:
        if tx["to"] == stx["validator-addr"] and tx["to-shard"] == beacon_shard_id:
            in_initially_funded = True
            break
    if not in_initially_funded:
        raise AssertionError(f"Test staking transaction from address {stx['validator-addr']} "
                             f"not found in set of initially funded accounts (or not founded on s{beacon_shard_id})")

    if get_staking_transaction(stx["hash"]) is None:
        tx = send_and_confirm_staking_transaction(stx)
        assert tx["hash"] == stx["hash"], f"Expected contract transaction hash to be {stx['hash']}, " \
                                          f"got {tx['hash']}"

    return stx

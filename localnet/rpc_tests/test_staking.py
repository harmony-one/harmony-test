#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests here are related to staking functions & require a feedback loop with the chain.

TODO: negative test cases

As with all tests, there are 2 JSON-RPC versions/namespaces (v1 & v2) where their difference
is only suppose to be in the types of their params & returns. v1 keeps everything in hex and
v2 uses decimal when possible. However, there are some (legacy) discrepancies that some tests
enforce. These tests are noted and should NOT be broken.
"""
import json
import time
import random
import traceback

import pytest
from flaky import flaky
from pyhmy import (
    blockchain,
    staking
)
from pyhmy.rpc.request import (
    base_request
)

import txs
from txs import (
    tx_timeout,
    beacon_shard_id,
    initial_funding,
    endpoints,
    send_and_confirm_staking_transaction,
    send_staking_transaction,
    get_staking_transaction
)
from utils import (
    check_and_unpack_rpc_response,
    assert_valid_json_structure,
    mutually_exclusive_test,
    rerun_delay_filter,
    assert_no_null_in_list
)

_mutex_scope = "staking"


def _assert_validator_info(validator_data, validator_info):
    """
    Helper function to check `validator_info` with the given `validator_data`.

    Validator data is expected to follow `stx` in s0_validator & s1_validator
    """
    val = validator_info["validator"]
    for attr in ["name", "identity", "website", "security-contact", "details"]:
        assert validator_data[attr] == val[attr], f"Expected {validator_data[attr]}, got {val[attr]}"
    for attr in ["rate", "max-rate", "max-change-rate"]:
        assert validator_data[attr] == float(val[attr]), f"Expected {validator_data[attr]}, got {val[attr]}"
    for attr in ["min-self-delegation", "max-total-delegation"]:
        assert validator_data[attr] * 1e18 == float(val[attr]), f"Expected {validator_data[attr]}, got {val[attr]}"
    assert validator_data["pub-bls-key"] in val[
        "bls-public-keys"], f"Expected pub-bls-key {validator_data['pub-bls-key']} " \
                            f"in {val['bls-public-keys']}"


@pytest.fixture(scope="module")
@txs.staking
def s0_validator():
    """
    Fixture for the shard 0 validator (with a running external node).

    Returns the validator's create validator transaction (`stx`)
    """
    stx = {
        "validator-addr": "one109r0tns7av5sjew7a7fkekg4fs3pw0h76pp45e",
        "delegator-addr": "one109r0tns7av5sjew7a7fkekg4fs3pw0h76pp45e",
        "name": "test",
        "identity": "test0",
        "website": "test",
        "security-contact": "test",
        "details": "test",
        "rate": 0.1,
        "max-rate": 0.9,
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
        assert tx["hash"] == stx["hash"], f"Expected create validator transaction hash to be {stx['hash']}, " \
                                          f"got {tx['hash']}"
        assert get_staking_transaction(stx["hash"]) is not None, f"Transaction (hash {stx['hash']}) not found on chain."

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
        "delegator-addr": "one1nmy8quw0924fss4r9km640pldzqegjk4wv4wts",
        "name": "test",
        "identity": "test1",
        "website": "test",
        "security-contact": "test",
        "details": "test",
        "rate": 0.1,
        "max-rate": 0.9,
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
        assert tx["hash"] == stx["hash"], f"Expected create validator transaction hash to be {stx['hash']}, " \
                                          f"got {tx['hash']}"
        assert get_staking_transaction(stx["hash"]) is not None, f"Transaction (hash {stx['hash']}) not found on chain."

    return stx


@txs.staking
@mutually_exclusive_test(scope=_mutex_scope)
@pytest.mark.run(after="test_get_validator_information")
def test_delegation(s1_validator):
    """
    Note that this is not an explicit RPC test. It just tests that delegation works.
    """
    stx = {
        "validator-addr": "one1nmy8quw0924fss4r9km640pldzqegjk4wv4wts",
        "delegator-addr": "one1v895jcvudcktswcmg2sldvmxvtvvdj2wuxj3hx",
        # web topple now acid repeat inspire tomato inside nominee reflect latin salmon garbage negative liberty win royal faith hammer lawsuit west toddler payment coffee
        "amount": 10000,
        "hash": "0x832e5af2305167d5d9a891c51eafc6510c89bbc76c01818e4ce02de0fc8c854e",
        "nonce": "0x0",
        "signed-raw-tx": "0xf88302f59461cb49619c6e2cb83b1b42a1f6b36662d8c6c94e949ec87071cf2aaa9842a32db7aabc3f6881944ad58a021e19e0c9bab240000080843b9aca00825fe027a0d8912da6a925af17701a2600df60e90fa4a61858b51758a03f57ac9d2797dc0ca004313c6865bde8704594be44d3ebbadfa6420922eef73d38ffba8ec42d8d3550"
    }

    assert stx["validator-addr"] == s1_validator["validator-addr"], f"Sanity check: Expected validator address " \
                                                                    f"to be {s1_validator['validator-addr']}"

    submitted_tx = False
    if get_staking_transaction(stx["hash"]) is None:
        tx = send_and_confirm_staking_transaction(stx)
        submitted_tx = True
        assert tx["hash"] == stx["hash"], f"Expected contract transaction hash to be {stx['hash']}, " \
                                          f"got {tx['hash']}"
        assert get_staking_transaction(stx["hash"]) is not None, f"Transaction (hash {stx['hash']}) not found on chain."

    validator_info = staking.get_validator_information(stx["validator-addr"], endpoint=endpoints[beacon_shard_id])
    for delegation in validator_info["validator"]["delegations"]:
        if delegation["delegator-address"] == stx["delegator-addr"]:
            if submitted_tx:
                assert delegation["amount"] == stx[
                    "amount"] * 1e18, f"Expected delegated amount to be {stx['amount']} ONE"
            return

    raise AssertionError(f"New delegation from {stx['delegator-addr']} not found on validator {stx['validator-addr']}")


@txs.staking
@mutually_exclusive_test(scope=_mutex_scope)
@pytest.mark.run(after="test_delegation")
@flaky(max_runs=6)
def test_undelegation(s1_validator):
    """
    Note that this is not an explicit RPC test. It just tests that undelegation works.
    """
    stx = {
        "validator-addr": "one1nmy8quw0924fss4r9km640pldzqegjk4wv4wts",
        "delegator-addr": "one1v895jcvudcktswcmg2sldvmxvtvvdj2wuxj3hx",
        # web topple now acid repeat inspire tomato inside nominee reflect latin salmon garbage negative liberty win royal faith hammer lawsuit west toddler payment coffee
        "amount": 10000,
        "hash": "0x79d27d042c157a4c1cdcbe931155515bfdd78d3162be79d348bab33113d8e08e",
        "nonce": "0x1",
        "signed-raw-tx": "0xf88203f49461cb49619c6e2cb83b1b42a1f6b36662d8c6c94e949ec87071cf2aaa9842a32db7aabc3f6881944ad5891b1ae4d6e2ef50000001843b9aca00825f9c28a0d12eb6e84a48356e079319642902b5c203806cba6960a3da2b5c43cf8021f510a00a73e7315c3ef773995eb3ebac033ab6c6b60b032f294af944f161d8e9ca2d4e"
    }

    assert stx["validator-addr"] == s1_validator["validator-addr"], f"Sanity check: Expected validator address " \
                                                                    f"to be {s1_validator['validator-addr']}"

    submitted_tx = False
    if get_staking_transaction(stx["hash"]) is None:
        tx = send_and_confirm_staking_transaction(stx)
        submitted_tx = True
        assert tx["hash"] == stx["hash"], f"Expected contract transaction hash to be {stx['hash']}, " \
                                          f"got {tx['hash']}"
        assert get_staking_transaction(stx["hash"]) is not None, f"Transaction (hash {stx['hash']}) not found on chain."

    validator_info = staking.get_validator_information(stx["validator-addr"], endpoint=endpoints[beacon_shard_id])
    for delegation in validator_info["validator"]["delegations"]:
        if delegation["delegator-address"] == stx["delegator-addr"]:
            if submitted_tx:
                assert len(
                    delegation["undelegations"]) > 0, f"Expected undelegations on validator {stx['validator-addr']}"
            return

    raise AssertionError(f"New delegation from {stx['delegator-addr']} not found on validator {stx['validator-addr']}")


@txs.staking
@pytest.mark.run('first')
def test_get_all_validator_addresses(s0_validator, s1_validator):
    """
    Note that v1 & v2 have the same responses.
    """
    reference_response = [
        'one109r0tns7av5sjew7a7fkekg4fs3pw0h76pp45e',
        'one1nmy8quw0924fss4r9km640pldzqegjk4wv4wts'
    ]

    # Check v1
    raw_response = base_request("hmy_getAllValidatorAddresses", params=[], endpoint=endpoints[beacon_shard_id])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    assert s0_validator["validator-addr"] in response, f"Expected validator {s0_validator['validator-addr']} " \
                                                       f"in validator list {response}"
    assert s1_validator["validator-addr"] in response, f"Expected validator {s1_validator['validator-addr']} " \
                                                       f"in validator list {response}"

    # Check v2
    raw_response = base_request("hmyv2_getAllValidatorAddresses", params=[], endpoint=endpoints[beacon_shard_id])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    assert s0_validator["validator-addr"] in response, f"Expected validator {s0_validator['validator-addr']} " \
                                                       f"in validator list {response}"
    assert s1_validator["validator-addr"] in response, f"Expected validator {s1_validator['validator-addr']} " \
                                                       f"in validator list {response}"


@txs.staking
def test_get_transaction_receipt_v1(s0_validator):
    reference_response = {
        "blockHash": "0x5890ceb902713f4f32f80764359e5b2ffec1fd84ad6f0bf75d5c22a6f1530d1d",
        "blockNumber": "0x7",
        "contractAddress": None,
        "cumulativeGasUsed": "0x5121c4",
        "gasUsed": "0x5121c4",
        "logs": [],
        "logsBloom": "0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
        "sender": "one109r0tns7av5sjew7a7fkekg4fs3pw0h76pp45e",
        "status": "0x1",
        "transactionHash": "0xf80460f1ad041a0a0e841da717fc5b7959b1a7e9a0ce9a25cd70c0ce40d5ff26",
        "transactionIndex": "0x0",
        "type": 0
    }

    raw_response = base_request("hmy_getTransactionReceipt",
                                params=[s0_validator["hash"]],
                                endpoint=endpoints[beacon_shard_id])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    assert response["transactionHash"] == s0_validator["hash"], f"Expected transaction {s0_validator['hash']}, " \
                                                                f"got {response['transactionHash']}"


@txs.staking
def test_get_transaction_receipt_v2(s0_validator):
    reference_response = {
        "blockHash": "0x5890ceb902713f4f32f80764359e5b2ffec1fd84ad6f0bf75d5c22a6f1530d1d",
        "blockNumber": 7,
        "contractAddress": None,
        "cumulativeGasUsed": 5317060,
        "gasUsed": 5317060,
        "logs": [],
        "logsBloom": "0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
        "sender": "one109r0tns7av5sjew7a7fkekg4fs3pw0h76pp45e",
        "status": 1,
        "transactionHash": "0xf80460f1ad041a0a0e841da717fc5b7959b1a7e9a0ce9a25cd70c0ce40d5ff26",
        "transactionIndex": 0,
        "type": 0
    }

    raw_response = base_request("hmyv2_getTransactionReceipt",
                                params=[s0_validator["hash"]],
                                endpoint=endpoints[beacon_shard_id])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    assert response["transactionHash"] == s0_validator["hash"], f"Expected transaction {s0_validator['hash']}, " \
                                                                f"got {response['transactionHash']}"


@txs.staking
def test_get_staking_transactions_count(s0_validator):
    """
    Note that v1 & v2 have the same responses.
    """
    reference_response = 0

    # Check v1, SENT
    raw_response = base_request("hmy_getStakingTransactionsCount",
                                params=[s0_validator["validator-addr"], "SENT"],
                                endpoint=endpoints[beacon_shard_id])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    assert response == 1, f"Expected account  {s0_validator['validator-addr']} to have 1 sent transactions"

    # Check v1, SENT
    raw_response = base_request("hmyv2_getStakingTransactionsCount",
                                params=[s0_validator["validator-addr"], "SENT"],
                                endpoint=endpoints[beacon_shard_id])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    assert response == 1, f"Expected account  {s0_validator['validator-addr']} to have 1 sent transactions"

    # Check v1, RECEIVED
    raw_response = base_request("hmy_getStakingTransactionsCount",
                                params=[s0_validator["validator-addr"], "RECEIVED"],
                                endpoint=endpoints[beacon_shard_id])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    assert response == 0, f"Expected account  {s0_validator['validator-addr']} to have 0 received transactions"

    # Check v1, RECEIVED
    raw_response = base_request("hmyv2_getStakingTransactionsCount",
                                params=[s0_validator["validator-addr"], "RECEIVED"],
                                endpoint=endpoints[beacon_shard_id])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    assert response == 0, f"Expected account  {s0_validator['validator-addr']} to have 0 received transactions"

    # Check v1, ALL
    raw_response = base_request("hmy_getStakingTransactionsCount",
                                params=[s0_validator["validator-addr"], "ALL"],
                                endpoint=endpoints[beacon_shard_id])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    assert response == 1, f"Expected account  {s0_validator['validator-addr']} to have 1 total transactions"

    # Check v1, ALL
    raw_response = base_request("hmyv2_getStakingTransactionsCount",
                                params=[s0_validator["validator-addr"], "ALL"],
                                endpoint=endpoints[beacon_shard_id])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    assert response == 1, f"Expected account  {s0_validator['validator-addr']} to have 1 total transactions"


@txs.staking
def test_get_all_validator_information(s0_validator, s1_validator):
    """
    Note that v1 & v2 have the same responses.
    """
    reference_response = [
        {
            "validator": {
                "bls-public-keys": [
                    "4f41a37a3a8d0695dd6edcc58142c6b7d98e74da5c90e79b587b3b960b6a4f5e048e6d8b8a000d77a478d44cd640270c"
                ],
                "last-epoch-in-committee": 0,
                "min-self-delegation": 10000000000000000000000,
                "max-total-delegation": 10000000000000000000000000,
                "rate": "0.100000000000000000",
                "max-rate": "0.900000000000000000",
                "max-change-rate": "0.050000000000000000",
                "update-height": 4,
                "name": "test",
                "identity": "test0",
                "website": "test",
                "security-contact": "test",
                "details": "test",
                "creation-height": 4,
                "address": "one109r0tns7av5sjew7a7fkekg4fs3pw0h76pp45e",
                "delegations": [
                    {
                        "delegator-address": "one109r0tns7av5sjew7a7fkekg4fs3pw0h76pp45e",
                        "amount": 10000000000000000000000,
                        "reward": 0,
                        "undelegations": []
                    }
                ]
            },
            "current-epoch-performance": {
                "current-epoch-signing-percent": {
                    "current-epoch-signed": 0,
                    "current-epoch-to-sign": 0,
                    "current-epoch-signing-percentage": "0.000000000000000000"
                }
            },
            "metrics": None,
            "total-delegation": 10000000000000000000000,
            "currently-in-committee": True,
            "epos-status": "currently elected",
            "epos-winning-stake": None,
            "booted-status": "not booted",
            "active-status": "active",
            "lifetime": {
                "reward-accumulated": 0,
                "blocks": {
                    "to-sign": 0,
                    "signed": 0
                },
                "apr": "0.000000000000000000",
                "epoch-apr": None
            }
        }
    ]

    # Check v1
    raw_response = base_request("hmy_getAllValidatorInformation", params=[0], endpoint=endpoints[beacon_shard_id])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    found_s0, found_s1 = False, False
    for validator in response:
        if validator["validator"]["address"] == s0_validator["validator-addr"]:
            found_s0 = True
            _assert_validator_info(s0_validator, validator)
        elif validator["validator"]["address"] == s1_validator["validator-addr"]:
            found_s1 = True
            _assert_validator_info(s1_validator, validator)
        for delegation in validator["validator"]["delegations"]:
            assert_no_null_in_list(delegation["undelegations"])
    assert found_s0 and found_s1, f"Expected to find validator information for " \
                                  f"{s0_validator['validator-addr']} and {s1_validator['validator-addr']}"

    # Check v2
    raw_response = base_request("hmyv2_getAllValidatorInformation", params=[0], endpoint=endpoints[beacon_shard_id])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    found_s0, found_s1 = False, False
    for validator in response:
        if validator["validator"]["address"] == s0_validator["validator-addr"]:
            found_s0 = True
            _assert_validator_info(s0_validator, validator)
        elif validator["validator"]["address"] == s1_validator["validator-addr"]:
            found_s1 = True
            _assert_validator_info(s1_validator, validator)
        for delegation in validator["validator"]["delegations"]:
            assert_no_null_in_list(delegation["undelegations"])
    assert found_s0 and found_s1, f"Expected to found validator information for " \
                                  f"{s0_validator['validator-addr']} and {s1_validator['validator-addr']}"


@txs.staking
def test_get_validator_information(s0_validator):
    """
    Note that v1 & v2 have the same responses.
    """
    reference_response = {
        "validator": {
            "bls-public-keys": [
                "4f41a37a3a8d0695dd6edcc58142c6b7d98e74da5c90e79b587b3b960b6a4f5e048e6d8b8a000d77a478d44cd640270c"
            ],
            "last-epoch-in-committee": 0,
            "min-self-delegation": 10000000000000000000000,
            "max-total-delegation": 10000000000000000000000000,
            "rate": "0.100000000000000000",
            "max-rate": "0.900000000000000000",
            "max-change-rate": "0.050000000000000000",
            "update-height": 4,
            "name": "test",
            "identity": "test0",
            "website": "test",
            "security-contact": "test",
            "details": "test",
            "creation-height": 4,
            "address": "one109r0tns7av5sjew7a7fkekg4fs3pw0h76pp45e",
            "delegations": [
                {
                    "delegator-address": "one109r0tns7av5sjew7a7fkekg4fs3pw0h76pp45e",
                    "amount": 10000000000000000000000,
                    "reward": 0,
                    "undelegations": []
                }
            ]
        },
        "current-epoch-performance": {
            "current-epoch-signing-percent": {
                "current-epoch-signed": 0,
                "current-epoch-to-sign": 0,
                "current-epoch-signing-percentage": "0.000000000000000000"
            }
        },
        "metrics": None,
        "total-delegation": 10000000000000000000000,
        "currently-in-committee": True,
        "epos-status": "currently elected",
        "epos-winning-stake": None,
        "booted-status": "not booted",
        "active-status": "active",
        "lifetime": {
            "reward-accumulated": 0,
            "blocks": {
                "to-sign": 0,
                "signed": 0
            },
            "apr": "0.000000000000000000",
            "epoch-apr": None
        }
    }

    # Check v1
    raw_response = base_request("hmy_getValidatorInformation", params=[s0_validator["validator-addr"]],
                                endpoint=endpoints[beacon_shard_id])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    _assert_validator_info(s0_validator, response)
    for delegation in response["validator"]["delegations"]:
        assert_no_null_in_list(delegation["undelegations"])

    # Check v2
    raw_response = base_request("hmyv2_getValidatorInformation", params=[s0_validator["validator-addr"]],
                                endpoint=endpoints[beacon_shard_id])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    _assert_validator_info(s0_validator, response)
    for delegation in response["validator"]["delegations"]:
        assert_no_null_in_list(delegation["undelegations"])


@txs.staking
def test_get_validator_information_by_block_number(s0_validator):
    """
    Note that v1 & v2 have the same responses.
    """
    reference_response = {
        "validator": {
            "bls-public-keys": [
                "4f41a37a3a8d0695dd6edcc58142c6b7d98e74da5c90e79b587b3b960b6a4f5e048e6d8b8a000d77a478d44cd640270c"
            ],
            "last-epoch-in-committee": 0,
            "min-self-delegation": 10000000000000000000000,
            "max-total-delegation": 10000000000000000000000000,
            "rate": "0.100000000000000000",
            "max-rate": "0.900000000000000000",
            "max-change-rate": "0.050000000000000000",
            "update-height": 4,
            "name": "test",
            "identity": "test0",
            "website": "test",
            "security-contact": "test",
            "details": "test",
            "creation-height": 4,
            "address": "one109r0tns7av5sjew7a7fkekg4fs3pw0h76pp45e",
            "delegations": [
                {
                    "delegator-address": "one109r0tns7av5sjew7a7fkekg4fs3pw0h76pp45e",
                    "amount": 10000000000000000000000,
                    "reward": 0,
                    "undelegations": []
                }
            ]
        },
        "current-epoch-performance": {
            "current-epoch-signing-percent": {
                "current-epoch-signed": 0,
                "current-epoch-to-sign": 0,
                "current-epoch-signing-percentage": "0.000000000000000000"
            }
        },
        "metrics": None,
        "total-delegation": 10000000000000000000000,
        "currently-in-committee": True,
        "epos-status": "currently elected",
        "epos-winning-stake": None,
        "booted-status": "not booted",
        "active-status": "active",
        "lifetime": {
            "reward-accumulated": 0,
            "blocks": {
                "to-sign": 0,
                "signed": 0
            },
            "apr": "0.000000000000000000",
            "epoch-apr": None
        }
    }
    curr_block = blockchain.get_block_number(endpoint=endpoints[beacon_shard_id])

    # Check v1
    raw_response = base_request("hmy_getValidatorInformationByBlockNumber",
                                params=[s0_validator["validator-addr"], hex(curr_block)],
                                endpoint=endpoints[beacon_shard_id])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    _assert_validator_info(s0_validator, response)

    # Check v2
    raw_response = base_request("hmyv2_getValidatorInformationByBlockNumber",
                                params=[s0_validator["validator-addr"], curr_block],
                                endpoint=endpoints[beacon_shard_id])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    _assert_validator_info(s0_validator, response)


@txs.staking
def test_get_all_validator_information_by_block_number(s0_validator, s1_validator):
    """
    Note that v1 & v2 have the same responses.
    """
    reference_response = [
        {
            "validator": {
                "bls-public-keys": [
                    "4f41a37a3a8d0695dd6edcc58142c6b7d98e74da5c90e79b587b3b960b6a4f5e048e6d8b8a000d77a478d44cd640270c"
                ],
                "last-epoch-in-committee": 0,
                "min-self-delegation": 10000000000000000000000,
                "max-total-delegation": 10000000000000000000000000,
                "rate": "0.100000000000000000",
                "max-rate": "0.900000000000000000",
                "max-change-rate": "0.050000000000000000",
                "update-height": 4,
                "name": "test",
                "identity": "test0",
                "website": "test",
                "security-contact": "test",
                "details": "test",
                "creation-height": 4,
                "address": "one109r0tns7av5sjew7a7fkekg4fs3pw0h76pp45e",
                "delegations": [
                    {
                        "delegator-address": "one109r0tns7av5sjew7a7fkekg4fs3pw0h76pp45e",
                        "amount": 10000000000000000000000,
                        "reward": 0,
                        "undelegations": []
                    }
                ]
            },
            "current-epoch-performance": {
                "current-epoch-signing-percent": {
                    "current-epoch-signed": 0,
                    "current-epoch-to-sign": 0,
                    "current-epoch-signing-percentage": "0.000000000000000000"
                }
            },
            "metrics": None,
            "total-delegation": 10000000000000000000000,
            "currently-in-committee": True,
            "epos-status": "currently elected",
            "epos-winning-stake": None,
            "booted-status": "not booted",
            "active-status": "active",
            "lifetime": {
                "reward-accumulated": 0,
                "blocks": {
                    "to-sign": 0,
                    "signed": 0
                },
                "apr": "0.000000000000000000",
                "epoch-apr": None
            }
        }
    ]
    curr_block = blockchain.get_block_number(endpoint=endpoints[beacon_shard_id])

    # Check v1
    raw_response = base_request("hmy_getAllValidatorInformationByBlockNumber", params=[0, hex(curr_block)],
                                endpoint=endpoints[beacon_shard_id])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    found_s0, found_s1 = False, False
    for validator in response:
        if validator["validator"]["address"] == s0_validator["validator-addr"]:
            found_s0 = True
            _assert_validator_info(s0_validator, validator)
        elif validator["validator"]["address"] == s1_validator["validator-addr"]:
            found_s1 = True
            _assert_validator_info(s1_validator, validator)
    assert found_s0 and found_s1, f"Expected to found validator information for " \
                                  f"{s0_validator['validator-addr']} and {s0_validator['validator-addr']}"

    # Check v2
    raw_response = base_request("hmyv2_getAllValidatorInformationByBlockNumber", params=[0, curr_block],
                                endpoint=endpoints[beacon_shard_id])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    found_s0, found_s1 = False, False
    for validator in response:
        if validator["validator"]["address"] == s0_validator["validator-addr"]:
            found_s0 = True
            _assert_validator_info(s0_validator, validator)
        elif validator["validator"]["address"] == s1_validator["validator-addr"]:
            found_s1 = True
            _assert_validator_info(s1_validator, validator)
    assert found_s0 and found_s1, f"Expected to found validator information for " \
                                  f"{s0_validator['validator-addr']} and {s0_validator['validator-addr']}"


@txs.staking
@flaky(max_runs=6, rerun_filter=rerun_delay_filter(delay=8))
@pytest.mark.run(after="test_get_validator_information")
def test_get_elected_validator_addresses(s0_validator, s1_validator):
    """
    Note that v1 & v2 have the same responses.
    """
    reference_response = [
        'one109r0tns7av5sjew7a7fkekg4fs3pw0h76pp45e',
        'one1nmy8quw0924fss4r9km640pldzqegjk4wv4wts'
    ]

    staking_epoch = blockchain.get_staking_epoch(endpoints[beacon_shard_id])
    curr_epoch = blockchain.get_latest_header(endpoint=endpoints[beacon_shard_id])["epoch"]
    val_0_info = staking.get_validator_information(s0_validator["validator-addr"], endpoint=endpoints[beacon_shard_id])
    val_1_info = staking.get_validator_information(s1_validator["validator-addr"], endpoint=endpoints[beacon_shard_id])
    s0_creation_epoch = int(blockchain.get_block_by_number(val_0_info["validator"]["creation-height"])["epoch"], 16)
    s1_creation_epoch = int(blockchain.get_block_by_number(val_1_info["validator"]["creation-height"])["epoch"], 16)

    while curr_epoch <= s0_creation_epoch or curr_epoch <= s1_creation_epoch or curr_epoch < staking_epoch:
        time.sleep(random.uniform(0.5, 1.5))  # Random to stop burst spam of RPC calls.
        curr_epoch = blockchain.get_latest_header(endpoint=endpoints[beacon_shard_id])["epoch"]

    # Check v1
    raw_response = base_request("hmy_getElectedValidatorAddresses", params=[], endpoint=endpoints[beacon_shard_id])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    assert s0_validator["validator-addr"] in response, f"Expected validator {s0_validator['validator-addr']} " \
                                                       f"in elected validator list {response}"
    assert s1_validator["validator-addr"] in response, f"Expected validator {s1_validator['validator-addr']} " \
                                                       f"in elected validator list {response}"

    # Check v2
    raw_response = base_request("hmyv2_getElectedValidatorAddresses", params=[], endpoint=endpoints[beacon_shard_id])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    assert s0_validator["validator-addr"] in response, f"Expected validator {s0_validator['validator-addr']} " \
                                                       f"in elected validator list {response}"
    assert s1_validator["validator-addr"] in response, f"Expected validator {s1_validator['validator-addr']} " \
                                                       f"in elected validator list {response}"


@txs.staking
@pytest.mark.run(after="test_delegation")
def test_get_delegations_by_delegator(s1_validator):
    """
    Note that v1 & v2 have the same responses.
    """
    reference_response = [
        {
            "validator_address": "one109r0tns7av5sjew7a7fkekg4fs3pw0h76pp45e",
            "delegator_address": "one109r0tns7av5sjew7a7fkekg4fs3pw0h76pp45e",
            "amount": 10000000000000000000000,
            "reward": 0,
            "Undelegations": []
        },
    ]
    val_addr = s1_validator["validator-addr"]
    validator_info = staking.get_validator_information(val_addr, endpoint=endpoints[beacon_shard_id])

    for delegator in validator_info["validator"]["delegations"]:
        # Check v1
        del_addr = delegator["delegator-address"]
        raw_response = base_request("hmy_getDelegationsByDelegator", params=[del_addr],
                                    endpoint=endpoints[beacon_shard_id])
        response = check_and_unpack_rpc_response(raw_response, expect_error=False)
        assert_valid_json_structure(reference_response, response)
        assert_no_null_in_list(response)
        found_validator = False
        for del_delegator in response:
            assert_no_null_in_list(del_delegator["Undelegations"])
            if del_delegator["validator_address"] == val_addr:
                found_validator = True
            assert del_addr == del_delegator["delegator_address"], f"Expected delegator address {del_addr}, " \
                                                                   f"got {del_delegator['delegator_address']}"
        assert found_validator, f"Expected to found validator {val_addr} in {json.dumps(response, indent=2)}"

        # Check v2
        raw_response = base_request("hmyv2_getDelegationsByDelegator", params=[del_addr],
                                    endpoint=endpoints[beacon_shard_id])
        response = check_and_unpack_rpc_response(raw_response, expect_error=False)
        assert_valid_json_structure(reference_response, response)
        assert_no_null_in_list(response)
        found_validator = False
        for del_delegator in response:
            assert_no_null_in_list(del_delegator["Undelegations"])
            if del_delegator["validator_address"] == val_addr:
                found_validator = True
            assert del_addr == del_delegator["delegator_address"], f"Expected delegator address {del_addr}, " \
                                                                   f"got {del_delegator['delegator_address']}"
        assert found_validator, f"Expected to found validator {val_addr} in {json.dumps(response, indent=2)}"


@txs.staking
@mutually_exclusive_test(scope=_mutex_scope)
@pytest.mark.run(after="test_delegation")
def test_get_delegations_by_delegator_by_block_number(s1_validator):
    """
    Note that v1 & v2 have the same responses.
    """
    reference_response = [
        {
            "validator_address": "one109r0tns7av5sjew7a7fkekg4fs3pw0h76pp45e",
            "delegator_address": "one109r0tns7av5sjew7a7fkekg4fs3pw0h76pp45e",
            "amount": 10000000000000000000000,
            "reward": 0,
            "Undelegations": []
        },
    ]
    curr_block = blockchain.get_block_number(endpoint=endpoints[beacon_shard_id])
    val_addr = s1_validator["validator-addr"]
    validator_info = staking.get_validator_information(val_addr, endpoint=endpoints[beacon_shard_id])

    for delegator in validator_info["validator"]["delegations"]:
        # Check v1
        del_addr = delegator["delegator-address"]
        raw_response = base_request("hmy_getDelegationsByDelegatorByBlockNumber", params=[del_addr, hex(curr_block)],
                                    endpoint=endpoints[beacon_shard_id])
        response = check_and_unpack_rpc_response(raw_response, expect_error=False)
        assert_valid_json_structure(reference_response, response)
        assert_no_null_in_list(response)
        found_validator = False
        for del_delegator in response:
            assert_no_null_in_list(del_delegator["Undelegations"])
            if del_delegator["validator_address"] == val_addr:
                found_validator = True
            assert del_addr == del_delegator["delegator_address"], f"Expected delegator address {del_addr}, " \
                                                                   f"got {del_delegator['delegator_address']}"
        assert found_validator, f"Expected to found validator {val_addr} in {json.dumps(response, indent=2)}"

        # Check v2
        raw_response = base_request("hmyv2_getDelegationsByDelegatorByBlockNumber", params=[del_addr, curr_block],
                                    endpoint=endpoints[beacon_shard_id])
        response = check_and_unpack_rpc_response(raw_response, expect_error=False)
        assert_valid_json_structure(reference_response, response)
        assert_no_null_in_list(response)
        found_validator = False
        for del_delegator in response:
            assert_no_null_in_list(del_delegator["Undelegations"])
            if del_delegator["validator_address"] == val_addr:
                found_validator = True
            assert del_addr == del_delegator["delegator_address"], f"Expected delegator address {del_addr}, " \
                                                                   f"got {del_delegator['delegator_address']}"
        assert found_validator, f"Expected to found validator {val_addr} in {json.dumps(response, indent=2)}"


@txs.staking
@mutually_exclusive_test(scope=_mutex_scope)
@pytest.mark.run(after="test_delegation")
def test_get_delegations_by_validator(s1_validator):
    """
    Note that v1 & v2 have the same responses.
    """
    reference_response = [
        {
            "validator_address": "one109r0tns7av5sjew7a7fkekg4fs3pw0h76pp45e",
            "delegator_address": "one109r0tns7av5sjew7a7fkekg4fs3pw0h76pp45e",
            "amount": 10000000000000000000000,
            "reward": 0,
            "Undelegations": []
        },
    ]
    val_addr = s1_validator["validator-addr"]
    validator_info = staking.get_validator_information(val_addr, endpoint=endpoints[beacon_shard_id])
    val_del_addrs = {d["delegator-address"] for d in validator_info["validator"]["delegations"]}

    # Check v1
    raw_response = base_request("hmy_getDelegationsByValidator", params=[val_addr],
                                endpoint=endpoints[beacon_shard_id])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    assert_no_null_in_list(response)
    for del_delegator in response:
        assert_no_null_in_list(del_delegator["Undelegations"])
        del_val_addr, del_del_addr = del_delegator["validator_address"], del_delegator["delegator_address"]
        assert del_val_addr == val_addr, f"Expected validator addr {val_addr}, got {del_val_addr}"
        assert del_del_addr in val_del_addrs, f"Expected delegator addr {val_addr} in {val_del_addrs}"

    # Check v2
    raw_response = base_request("hmyv2_getDelegationsByValidator", params=[val_addr],
                                endpoint=endpoints[beacon_shard_id])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    for del_delegator in response:
        del_val_addr, del_del_addr = del_delegator["validator_address"], del_delegator["delegator_address"]
        assert del_val_addr == val_addr, f"Expected validator addr {val_addr}, got {del_val_addr}"
        assert del_del_addr in val_del_addrs, f"Expected delegator addr {val_addr} in {val_del_addrs}"


@txs.staking
def test_get_current_utility_metrics(s0_validator):
    """
    Note that v1 & v2 have the same responses.
    """
    reference_response = {
        "AccumulatorSnapshot": 5768000000000000000000,
        "CurrentStakedPercentage": "0.000004311108610723",
        "Deviation": "0.349995688891389277",
        "Adjustment": "13999827555655571080.000000000000000000"
    }

    # Check v1
    raw_response = base_request("hmy_getCurrentUtilityMetrics", params=[],
                                endpoint=endpoints[beacon_shard_id])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)

    # Check v2
    raw_response = base_request("hmyv2_getCurrentUtilityMetrics", params=[],
                                endpoint=endpoints[beacon_shard_id])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)


@txs.staking
@flaky(max_runs=6, rerun_filter=rerun_delay_filter(delay=8))
@pytest.mark.run(after="test_get_validator_information")
def test_get_median_raw_stake_snapshot(s0_validator):
    """
    Note that v1 & v2 have the same responses.

    Use shard 0 endpoint, NOT beacon endpoint as we are checking with `s0_validator`
    """
    reference_response = {
        "epos-median-stake": "10000000000000000000000.000000000000000000",
        "max-external-slots": 6,
        "epos-slot-winners": [
            {
                "slot-owner": "one109r0tns7av5sjew7a7fkekg4fs3pw0h76pp45e",
                "bls-public-key": "4f41a37a3a8d0695dd6edcc58142c6b7d98e74da5c90e79b587b3b960b6a4f5e048e6d8b8a000d77a478d44cd640270c",
                "raw-stake": "10000000000000000000000.000000000000000000",
                "eposed-stake": "10000000000000000000000.000000000000000000"
            }
        ],
        "epos-slot-candidates": [
            {
                "stake": 10000000000000000000000,
                "keys-at-auction": [
                    "4f41a37a3a8d0695dd6edcc58142c6b7d98e74da5c90e79b587b3b960b6a4f5e048e6d8b8a000d77a478d44cd640270c"
                ],
                "percentage-of-total-auction-stake": "1.000000000000000000",
                "stake-per-key": 10000000000000000000000,
                "validator": "one109r0tns7av5sjew7a7fkekg4fs3pw0h76pp45e"
            }
        ]
    }

    staking_epoch = blockchain.get_staking_epoch(endpoints[beacon_shard_id])
    curr_epoch = blockchain.get_latest_header(endpoint=endpoints[0])["epoch"]
    val_0_info = staking.get_validator_information(s0_validator["validator-addr"], endpoint=endpoints[0])
    s0_creation_epoch = int(blockchain.get_block_by_number(val_0_info["validator"]["creation-height"])["epoch"], 16)

    while curr_epoch <= s0_creation_epoch or curr_epoch < staking_epoch:
        time.sleep(random.uniform(0.5, 1.5))  # Random to stop burst spam of RPC calls.
        curr_epoch = blockchain.get_latest_header(endpoint=endpoints[beacon_shard_id])["epoch"]

    # First block of an epoch does not have correct snapshot, wait for next block.
    curr_block = blockchain.get_latest_header(endpoint=endpoints[0])["blockNumber"]
    prev_block_epoch = int(blockchain.get_block_by_number(curr_block - 1)["epoch"], 16)
    while prev_block_epoch != curr_epoch:
        time.sleep(random.uniform(0.5, 1.5))  # Random to stop burst spam of RPC calls.
        curr_block = blockchain.get_latest_header(endpoint=endpoints[0])["blockNumber"]
        prev_block_epoch = int(blockchain.get_block_by_number(curr_block - 1)["epoch"], 16)

    # Check v1
    raw_response = base_request("hmy_getMedianRawStakeSnapshot", params=[], endpoint=endpoints[0])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    found_s0_winner, found_s0_candidate = False, False
    for val in response["epos-slot-winners"]:
        if val["slot-owner"] == s0_validator["validator-addr"]:
            found_s0_winner = True
            break
    assert found_s0_winner, f"Expected validator {s0_validator['validator-addr']} to win election"
    for val in response["epos-slot-candidates"]:
        if val["validator"] == s0_validator["validator-addr"]:
            found_s0_candidate = True
            break
    assert found_s0_candidate, f"Expected validator {s0_validator['validator-addr']} to be candidate for next epoch"

    # Check v2
    raw_response = base_request("hmyv2_getMedianRawStakeSnapshot", params=[], endpoint=endpoints[0])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    found_s0_winner, found_s0_candidate = False, False
    for val in response["epos-slot-winners"]:
        if val["slot-owner"] == s0_validator["validator-addr"]:
            found_s0_winner = True
            break
    assert found_s0_winner, f"Expected validator {s0_validator['validator-addr']} to win election"
    for val in response["epos-slot-candidates"]:
        if val["validator"] == s0_validator["validator-addr"]:
            found_s0_candidate = True
            break
    assert found_s0_candidate, f"Expected validator {s0_validator['validator-addr']} to be candidate for next epoch"


@txs.staking
@flaky(max_runs=6, rerun_filter=rerun_delay_filter(delay=8))
@pytest.mark.run(after="test_get_median_raw_stake_snapshot")
def test_get_super_committees(s0_validator):
    """
    Note that v1 & v2 have the same responses.
    """
    reference_response = {
        "previous": {
            "quorum-deciders": {
                "shard-0": {
                    "policy": "SuperMajorityStake",
                    "count": 7,
                    "external-validator-slot-count": 1,
                    "committee-members": [
                        {
                            "is-harmony-slot": True,
                            "earning-account": "one1spshr72utf6rwxseaz339j09ed8p6f8ke370zj",
                            "bls-public-key": "2d61379e44a772e5757e27ee2b3874254f56073e6bd226eb8b160371cc3c18b8c4977bd3dcb71fd57dc62bf0e143fd08",
                            "voting-power-unnormalized": "0.166666666666666666",
                            "voting-power-%": "0.113333333333333333"
                        },
                    ],
                    "hmy-voting-power": "0.679999999999999998",
                    "staked-voting-power": "0.320000000000000002",
                    "total-raw-stake": "10000000000000000000000.000000000000000000",
                    "total-effective-stake": "10000000000000000000000.000000000000000000"
                },
                "shard-1": {
                    "policy": "SuperMajorityStake",
                    "count": 6,
                    "external-validator-slot-count": 0,
                    "committee-members": [
                        {
                            "is-harmony-slot": True,
                            "earning-account": "one1m6m0ll3q7ljdqgmth2t5j7dfe6stykucpj2nr5",
                            "bls-public-key": "40379eed79ed82bebfb4310894fd33b6a3f8413a78dc4d43b98d0adc9ef69f3285df05eaab9f2ce5f7227f8cb920e809",
                            "voting-power-unnormalized": "0.166666666666666666",
                            "voting-power-%": "0.113333333333333333"
                        },
                    ],
                    "hmy-voting-power": "0.679999999999999998",
                    "staked-voting-power": "0.000000000000000000",
                    "total-raw-stake": "0.000000000000000000",
                    "total-effective-stake": "0.000000000000000000"
                }
            },
            "external-slot-count": 6,
            "epos-median-stake": "10000000000000000000000.000000000000000000"
        },
        "current": {
            "quorum-deciders": {
                "shard-0": {
                    "policy": "SuperMajorityStake",
                    "count": 7,
                    "external-validator-slot-count": 1,
                    "committee-members": [
                        {
                            "is-harmony-slot": True,
                            "earning-account": "one1pdv9lrdwl0rg5vglh4xtyrv3wjk3wsqket7zxy",
                            "bls-public-key": "65f55eb3052f9e9f632b2923be594ba77c55543f5c58ee1454b9cfd658d25e06373b0f7d42a19c84768139ea294f6204",
                            "voting-power-unnormalized": "0.166666666666666666",
                            "voting-power-%": "0.113333333333333333"
                        },
                    ],
                    "hmy-voting-power": "0.679999999999999998",
                    "staked-voting-power": "0.320000000000000002",
                    "total-raw-stake": "10000000000000000000000.000000000000000000",
                    "total-effective-stake": "10000000000000000000000.000000000000000000"
                },
                "shard-1": {
                    "policy": "SuperMajorityStake",
                    "count": 6,
                    "external-validator-slot-count": 0,
                    "committee-members": [
                        {
                            "is-harmony-slot": True,
                            "earning-account": "one1m6m0ll3q7ljdqgmth2t5j7dfe6stykucpj2nr5",
                            "bls-public-key": "40379eed79ed82bebfb4310894fd33b6a3f8413a78dc4d43b98d0adc9ef69f3285df05eaab9f2ce5f7227f8cb920e809",
                            "voting-power-unnormalized": "0.166666666666666666",
                            "voting-power-%": "0.113333333333333333"
                        },
                    ],
                    "hmy-voting-power": "0.679999999999999998",
                    "staked-voting-power": "0.000000000000000000",
                    "total-raw-stake": "0.000000000000000000",
                    "total-effective-stake": "0.000000000000000000"
                }
            },
            "external-slot-count": 6,
            "epos-median-stake": "10000000000000000000000.000000000000000000"
        }
    }

    staking_epoch = blockchain.get_staking_epoch(endpoints[beacon_shard_id])
    curr_epoch = blockchain.get_latest_header(endpoint=endpoints[beacon_shard_id])["epoch"]
    val_0_info = staking.get_validator_information(s0_validator["validator-addr"], endpoint=endpoints[beacon_shard_id])
    s0_creation_epoch = int(blockchain.get_block_by_number(val_0_info["validator"]["creation-height"])["epoch"], 16)

    while curr_epoch <= s0_creation_epoch or curr_epoch < staking_epoch:
        time.sleep(random.uniform(0.5, 1.5))  # Random to stop burst spam of RPC calls.
        curr_epoch = blockchain.get_latest_header(endpoint=endpoints[0])["epoch"]

    # Check v1
    raw_response = base_request("hmy_getSuperCommittees", params=[], endpoint=endpoints[beacon_shard_id])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    found_validator, found_key = False, False
    for member in response["current"]["quorum-deciders"]["shard-0"]["committee-members"]:
        if member["earning-account"] == s0_validator["validator-addr"]:
            found_validator = True
        if member["bls-public-key"] == s0_validator["pub-bls-key"]:
            found_key = True
    assert found_validator, f"Expected to find validator {s0_validator['validator-addr']} in current committee"
    assert found_key, f"Expected to pub bls key {s0_validator['bls-public-key']} in current committee"

    # Check v2
    raw_response = base_request("hmyv2_getSuperCommittees", params=[], endpoint=endpoints[beacon_shard_id])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    found_validator, found_key = False, False
    for member in response["current"]["quorum-deciders"]["shard-0"]["committee-members"]:
        if member["earning-account"] == s0_validator["validator-addr"]:
            found_validator = True
        if member["bls-public-key"] == s0_validator["pub-bls-key"]:
            found_key = True
    assert found_validator, f"Expected to find validator {s0_validator['validator-addr']} in current committee"
    assert found_key, f"Expected to pub bls key {s0_validator['bls-public-key']} in current committee"


@txs.staking
def test_get_staking_network_info(s0_validator):
    """
    Note that v1 & v2 have the same responses.
    """
    reference_response = {
        "total-supply": "12600000000.000000000000000000",
        "circulating-supply": "6842781705.882339000000000000",
        "epoch-last-block": 59,
        "total-staking": 10000000000000000000000,
        "median-raw-stake": "10000000000000000000000.000000000000000000"
    }

    # Check v1
    raw_response = base_request("hmy_getStakingNetworkInfo", params=[],
                                endpoint=endpoints[beacon_shard_id])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)

    # Check v2
    raw_response = base_request("hmyv2_getStakingNetworkInfo", params=[],
                                endpoint=endpoints[beacon_shard_id])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)


@txs.staking
@flaky(max_runs=6, rerun_filter=rerun_delay_filter(delay=8))
def test_get_validator_keys(s0_validator):
    """
    Note that v1 & v2 have the same responses.

    Use shard 0 endpoint, NOT beacon endpoint as we are checking with `s0_validator`
    """
    reference_response = [
        "65f55eb3052f9e9f632b2923be594ba77c55543f5c58ee1454b9cfd658d25e06373b0f7d42a19c84768139ea294f6204",
    ]

    staking_epoch = blockchain.get_staking_epoch(endpoints[beacon_shard_id])
    curr_epoch = blockchain.get_latest_header(endpoint=endpoints[0])["epoch"]
    val_0_info = staking.get_validator_information(s0_validator["validator-addr"], endpoint=endpoints[0])
    s0_creation_epoch = int(blockchain.get_block_by_number(val_0_info["validator"]["creation-height"])["epoch"], 16)

    while curr_epoch <= s0_creation_epoch or curr_epoch < staking_epoch:
        time.sleep(random.uniform(0.5, 1.5))  # Random to stop burst spam of RPC calls.
        curr_epoch = blockchain.get_latest_header(endpoint=endpoints[beacon_shard_id])["epoch"]

    # Check v1
    raw_response = base_request("hmy_getValidatorKeys", params=[curr_epoch],
                                endpoint=endpoints[0])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    assert s0_validator["pub-bls-key"] in response, f"Expected pub bls key {s0_validator['pub-bls-key']} in {response}"

    # Check v1
    raw_response = base_request("hmyv2_getValidatorKeys", params=[curr_epoch],
                                endpoint=endpoints[0])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    assert s0_validator["pub-bls-key"] in response, f"Expected pub bls key {s0_validator['pub-bls-key']} in {response}"


@txs.staking
@flaky(max_runs=6, rerun_filter=rerun_delay_filter(delay=8))
def test_get_validators_v1(s0_validator, s1_validator):
    reference_response = {
        "shardID": 0,
        "validators": [
            {
                "address": "one1pdv9lrdwl0rg5vglh4xtyrv3wjk3wsqket7zxy",
                "balance": "0x252c53eaca3b23bb3"
            },
        ]
    }

    staking_epoch = blockchain.get_staking_epoch(endpoints[beacon_shard_id])
    curr_epoch = blockchain.get_latest_header(endpoint=endpoints[beacon_shard_id])["epoch"]
    val_0_info = staking.get_validator_information(s0_validator["validator-addr"], endpoint=endpoints[beacon_shard_id])
    val_1_info = staking.get_validator_information(s1_validator["validator-addr"], endpoint=endpoints[beacon_shard_id])
    s0_creation_epoch = int(blockchain.get_block_by_number(val_0_info["validator"]["creation-height"])["epoch"], 16)
    s1_creation_epoch = int(blockchain.get_block_by_number(val_1_info["validator"]["creation-height"])["epoch"], 16)

    while curr_epoch <= s0_creation_epoch or curr_epoch <= s1_creation_epoch or curr_epoch < staking_epoch:
        time.sleep(random.uniform(0.5, 1.5))  # Random to stop burst spam of RPC calls.
        curr_epoch = blockchain.get_latest_header(endpoint=endpoints[beacon_shard_id])["epoch"]

    raw_response = base_request("hmy_getValidators", params=[curr_epoch],
                                endpoint=endpoints[beacon_shard_id])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    found_s0, found_s1 = False, False
    for val in response["validators"]:
        if val["address"] == s0_validator["validator-addr"]:
            found_s0 = True
        if val["address"] == s1_validator["validator-addr"]:
            found_s1 = True
    assert found_s0 and found_s1, f"Expected to find validator information for " \
                                  f"{s0_validator['validator-addr']} and {s0_validator['validator-addr']}"


@txs.staking
@flaky(max_runs=6, rerun_filter=rerun_delay_filter(delay=8))
def test_get_validators_v2(s0_validator, s1_validator):
    reference_response = {
        "shardID": 0,
        "validators": [
            {
                "address": "one1pdv9lrdwl0rg5vglh4xtyrv3wjk3wsqket7zxy",
                "balance": 42857730340142857139
            },
        ]
    }

    staking_epoch = blockchain.get_staking_epoch(endpoints[beacon_shard_id])
    curr_epoch = blockchain.get_latest_header(endpoint=endpoints[beacon_shard_id])["epoch"]
    val_0_info = staking.get_validator_information(s0_validator["validator-addr"], endpoint=endpoints[beacon_shard_id])
    val_1_info = staking.get_validator_information(s1_validator["validator-addr"], endpoint=endpoints[beacon_shard_id])
    s0_creation_epoch = int(blockchain.get_block_by_number(val_0_info["validator"]["creation-height"])["epoch"], 16)
    s1_creation_epoch = int(blockchain.get_block_by_number(val_1_info["validator"]["creation-height"])["epoch"], 16)

    while curr_epoch <= s0_creation_epoch or curr_epoch <= s1_creation_epoch or curr_epoch < staking_epoch:
        time.sleep(random.uniform(0.5, 1.5))  # Random to stop burst spam of RPC calls.
        curr_epoch = blockchain.get_latest_header(endpoint=endpoints[beacon_shard_id])["epoch"]

    raw_response = base_request("hmyv2_getValidators", params=[curr_epoch],
                                endpoint=endpoints[beacon_shard_id])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    found_s0, found_s1 = False, False
    for val in response["validators"]:
        if val["address"] == s0_validator["validator-addr"]:
            found_s0 = True
        if val["address"] == s1_validator["validator-addr"]:
            found_s1 = True
    assert found_s0 and found_s1, f"Expected to find validator information for " \
                                  f"{s0_validator['validator-addr']} and {s0_validator['validator-addr']}"


@txs.staking
@pytest.mark.run('first')
def test_pending_staking_transactions_v1():
    stx = {  # Create validator tx
        "validator-addr": "one13v9m45m6yk9qmmcgyq603ucy0wdw9lfsxzsj9d",
        "delegator-addr": "one13v9m45m6yk9qmmcgyq603ucy0wdw9lfsxzsj9d",
        "name": "test",
        "identity": "test1",
        "website": "test",
        "security-contact": "test",
        "details": "test",
        "rate": 0.1,
        "max-rate": 0.9,
        "max-change-rate": 0.05,
        "min-self-delegation": 10000,
        "max-total-delegation": 10000000,
        "amount": 10000,
        "pub-bls-key": "8596e18ce463e4d5faa62d669dd959101ca408f757489bc9bdb2f95c2cc7a521b4eeb6d55ff2befd8b220fce6939b408",
        "hash": "0xf16668d7e39f01fd15c40e515ece370af1c80f7588bffd7c53932768a0ebba2e",
        "nonce": "0x0",
        "signed-raw-tx": "0xf9015780f90106948b0bbad37a258a0def082034f8f3047b9ae2fd30da8474657374857465737432847465737484746573748474657374ddc988016345785d8a0000c9880c7d713b49da0000c887b1a2bc2ec500008a021e19e0c9bab24000008b084595161401484a000000f1b08596e18ce463e4d5faa62d669dd959101ca408f757489bc9bdb2f95c2cc7a521b4eeb6d55ff2befd8b220fce6939b408f862b860cc0dbe1c9ba4f352e44420af0bfa9019b604d46b9afb38eebf599e89c9da76101852426bcc3845075fe7f460f639e308b738ef904036fee9c95bfc8888d6eeabd5365d005f20f76fbbe165b4bc1452bb5f50dd91a8422c6d9a94bc846f3754968a021e19e0c9bab240000080843b9aca008351220427a02eeadff25df33d13eb95288006435e06a65ad979bf24b9cbd151c696df5b84e3a016e9fa32ddad438936ba2ac837cc8ac102aeec519198fa4516cfac7032df313c"
    }
    reference_response = [
        {
            "blockHash": "0x0000000000000000000000000000000000000000000000000000000000000000",
            "blockNumber": None,
            "from": "one13v9m45m6yk9qmmcgyq603ucy0wdw9lfsxzsj9d",
            "timestamp": "0x0",
            "gas": "0x512204",
            "gasPrice": "0x3b9aca00",
            "hash": "0xf16668d7e39f01fd15c40e515ece370af1c80f7588bffd7c53932768a0ebba2e",
            "nonce": "0x0",
            "transactionIndex": "0x0",
            "v": "0x27",
            "r": "0x2eeadff25df33d13eb95288006435e06a65ad979bf24b9cbd151c696df5b84e3",
            "s": "0x16e9fa32ddad438936ba2ac837cc8ac102aeec519198fa4516cfac7032df313c",
            "type": "CreateValidator",
            "msg": None
        }
    ]
    reference_create_validator_msg = {
        "amount": "0x21e19e0c9bab2400000",
        "commissionRate": "0x16345785d8a0000",
        "details": "test",
        "identity": "test2",
        "maxChangeRate": "0xb1a2bc2ec50000",
        "maxCommissionRate": "0xc7d713b49da0000",
        "maxTotalDelegation": "0x84595161401484a000000",
        "minSelfDelegation": "0x21e19e0c9bab2400000",
        "name": "test",
        "securityContact": "test",
        "slotPubKeys": [
            "8596e18ce463e4d5faa62d669dd959101ca408f757489bc9bdb2f95c2cc7a521b4eeb6d55ff2befd8b220fce6939b408"
        ],
        "validatorAddress": "one13v9m45m6yk9qmmcgyq603ucy0wdw9lfsxzsj9d",
        "website": "test"
    }

    in_initially_funded = False
    for tx in initial_funding:
        if tx["to"] == stx["validator-addr"] and tx["to-shard"] == beacon_shard_id:
            in_initially_funded = True
            break
    if not in_initially_funded:
        raise AssertionError(f"Test staking transaction from address {stx['validator-addr']} "
                             f"not found in set of initially funded accounts (or not founded on s{beacon_shard_id})")

    if get_staking_transaction(stx["hash"]) is not None:
        pytest.skip(f"Test staking transaction (hash {stx['hash']}) already present on chain...")

    send_staking_transaction(stx, confirm_submission=True)

    start_time = time.time()
    while time.time() - start_time <= tx_timeout:
        raw_response = base_request("hmy_pendingStakingTransactions", endpoint=endpoints[beacon_shard_id])
        response = check_and_unpack_rpc_response(raw_response, expect_error=False)
        assert_valid_json_structure(reference_response, response)
        for pending_tx in response:
            if pending_tx["hash"] == stx["hash"]:
                assert pending_tx["type"] == "CreateValidator"
                assert_valid_json_structure(reference_create_validator_msg, pending_tx["msg"])
                return

    raise AssertionError(f"Timeout! Pending transaction not found for {json.dumps(stx, indent=2)}")


@txs.staking
@pytest.mark.run('first')
def test_pending_staking_transactions_v2():
    stx = {  # Create validator tx
        "validator-addr": "one13muqj27fcd59gfrv7wzvuaupgkkwvwzlxun0ce",
        "delegator-addr": "one13muqj27fcd59gfrv7wzvuaupgkkwvwzlxun0ce",
        "name": "test",
        "identity": "test3",
        "website": "test",
        "security-contact": "test",
        "details": "test",
        "rate": 0.1,
        "max-rate": 0.9,
        "max-change-rate": 0.05,
        "min-self-delegation": 10000,
        "max-total-delegation": 10000000,
        "amount": 10000,
        "pub-bls-key": "29cdd2ea5ef25bfee0bbc649065ceb2d0e19cc25f42541154eca69c0ff923971e20352fbfeeac5d17f8f6c6fc5871e88",
        "hash": "0x6e54fc7102daa31372027912b7f441ab9b9acafb9fa93b72dc9380321bacdbe2",
        "nonce": "0x0",
        "signed-raw-tx": "0xf9015780f90106948ef8092bc9c36854246cf384ce778145ace6385fda8474657374857465737433847465737484746573748474657374ddc988016345785d8a0000c9880c7d713b49da0000c887b1a2bc2ec500008a021e19e0c9bab24000008b084595161401484a000000f1b029cdd2ea5ef25bfee0bbc649065ceb2d0e19cc25f42541154eca69c0ff923971e20352fbfeeac5d17f8f6c6fc5871e88f862b860413befdd8895ade3cadaf121cac888f47b73c0986a38dda3198f3821532278b992e413009c014bef52c59264d7b2eb13054377146a540751b3c3c6c5a21a2c7fac9639ef72d613167315df1ea6455cde42e53157d4b7cac0b3c8975e5d5eb2828a021e19e0c9bab240000080843b9aca008351220427a0e03993350ed72c70198bbb9b0c962eba1ba08c6c46f66c50a878f84970120941a0421342afa7dd527edadfb8fc0b3b80c41ba3fcd390cc2ff95bc18b89c58850ca"
    }
    reference_response = [
        {
            "blockHash": "0x0000000000000000000000000000000000000000000000000000000000000000",
            "blockNumber": None,
            "from": "one13muqj27fcd59gfrv7wzvuaupgkkwvwzlxun0ce",
            "timestamp": 0,
            "gas": 5317124,
            "gasPrice": 1000000000,
            "hash": "0x6e54fc7102daa31372027912b7f441ab9b9acafb9fa93b72dc9380321bacdbe2",
            "nonce": 0,
            "transactionIndex": 0,
            "v": "0x27",
            "r": "0xe03993350ed72c70198bbb9b0c962eba1ba08c6c46f66c50a878f84970120941",
            "s": "0x421342afa7dd527edadfb8fc0b3b80c41ba3fcd390cc2ff95bc18b89c58850ca",
            "type": "CreateValidator",
            "msg": None
        }
    ]
    reference_create_validator_msg = {
        "amount": 10000000000000000000000,
        "commissionRate": 100000000000000000,
        "details": "test",
        "identity": "test3",
        "maxChangeRate": 50000000000000000,
        "maxCommissionRate": 900000000000000000,
        "maxTotalDelegation": 10000000000000000000000000,
        "minSelfDelegation": 10000000000000000000000,
        "name": "test",
        "securityContact": "test",
        "slotPubKeys": [
            "29cdd2ea5ef25bfee0bbc649065ceb2d0e19cc25f42541154eca69c0ff923971e20352fbfeeac5d17f8f6c6fc5871e88"
        ],
        "validatorAddress": "one13muqj27fcd59gfrv7wzvuaupgkkwvwzlxun0ce",
        "website": "test"
    }

    in_initially_funded = False
    for tx in initial_funding:
        if tx["to"] == stx["validator-addr"] and tx["to-shard"] == beacon_shard_id:
            in_initially_funded = True
            break
    if not in_initially_funded:
        raise AssertionError(f"Test staking transaction from address {stx['validator-addr']} "
                             f"not found in set of initially funded accounts (or not founded on s{beacon_shard_id})")

    if get_staking_transaction(stx["hash"]) is not None:
        pytest.skip(f"Test staking transaction (hash {stx['hash']}) already present on chain...")

    send_staking_transaction(stx, confirm_submission=True)

    start_time = time.time()
    while time.time() - start_time <= tx_timeout:
        raw_response = base_request("hmyv2_pendingStakingTransactions", endpoint=endpoints[beacon_shard_id])
        response = check_and_unpack_rpc_response(raw_response, expect_error=False)
        assert_valid_json_structure(reference_response, response)
        for pending_tx in response:
            if pending_tx["hash"] == stx["hash"]:
                assert pending_tx["type"] == "CreateValidator"
                assert_valid_json_structure(reference_create_validator_msg, pending_tx["msg"])
                return

    raise AssertionError(f"Timeout! Pending transaction not found for {json.dumps(stx, indent=2)}")


@txs.staking
@mutually_exclusive_test(scope=_mutex_scope)
def test_get_blocks_v1(s0_validator):
    """
    Note: param options for 'withSigners' will NOT return any sensical data
    in staking epoch (since it returns ONE addresses) and is subject to removal, thus is not tested here.
    """
    reference_response_blk = {
        "difficulty": 0,
        "epoch": "0x1",
        "extraData": "0x",
        "gasLimit": "0x4c4b400",
        "gasUsed": "0x5121c4",
        "hash": "0xc0438fb59641cf000ddede158cf3707b6b96f2fbf7eaf40386eb91a0dc4305a4",
        "logsBloom": "0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
        "miner": "one1pdv9lrdwl0rg5vglh4xtyrv3wjk3wsqket7zxy",
        "mixHash": "0x0000000000000000000000000000000000000000000000000000000000000000",
        "nonce": 0,
        "number": "0xb",
        "parentHash": "0x57b4221951b61025eccea748c3a67dc2f1dafa9db278ac4d67135061432de6d0",
        "receiptsRoot": "0x37f9bea40135162a9eb2164266b2152a3909ee94dd2f908cdb091afb90724e1e",
        "size": "0x3fd",
        "stakingTransactions": [],
        "stateRoot": "0x33109119529b1d282909975ce846a3eeb1b76681d7beebfa5cf79adfe4a1c4d7",
        "timestamp": "0x5f11a7a2",
        "transactions": [],
        "transactionsRoot": "0xf4ab626bfc3bf9781ddef818f85cc81c345010b7b6abaeb27d0237c8a1ee1ac5",
        "uncles": [],
        "viewID": "0xb"
    }
    reference_staking_response = {
        "blockHash": "0xc0438fb59641cf000ddede158cf3707b6b96f2fbf7eaf40386eb91a0dc4305a4",
        "blockNumber": "0xb",
        "from": "one109r0tns7av5sjew7a7fkekg4fs3pw0h76pp45e",
        "timestamp": "0x5f11a7a2",
        "gas": "0x5121c4",
        "gasPrice": "0x3b9aca00",
        "hash": "0xf80460f1ad041a0a0e841da717fc5b7959b1a7e9a0ce9a25cd70c0ce40d5ff26",
        "nonce": "0x0",
        "transactionIndex": "0x0",
        "v": "0x27",
        "r": "0x2348daabe696c4370379b9102dd85da6d4fed52f0f511ff0448a21c001ee75a7",
        "s": "0x1a67f9f40e0de02b50d5d7295f200fea7f950c1b59aa7efa8d225294c4fdbc5e",
        "type": "CreateValidator",
        "msg": None
    }
    reference_create_validator_msg = {
        "amount": "0x21e19e0c9bab2400000",
        "commissionRate": "0x16345785d8a0000",
        "details": "test",
        "identity": "test0",
        "maxChangeRate": "0xb1a2bc2ec50000",
        "maxCommissionRate": "0xc7d713b49da0000",
        "maxTotalDelegation": "0x84595161401484a000000",
        "minSelfDelegation": "0x21e19e0c9bab2400000",
        "name": "test",
        "securityContact": "test",
        "slotPubKeys": [
            "4f41a37a3a8d0695dd6edcc58142c6b7d98e74da5c90e79b587b3b960b6a4f5e048e6d8b8a000d77a478d44cd640270c"
        ],
        "validatorAddress": "one109r0tns7av5sjew7a7fkekg4fs3pw0h76pp45e",
        "website": "test"
    }

    init_tx = get_staking_transaction(s0_validator["hash"])
    start_blk, end_blk = hex(max(0, int(init_tx["blockNumber"], 16) - 2)), init_tx["blockNumber"]
    raw_response = base_request("hmy_getBlocks",
                                params=[start_blk, end_blk, {
                                    "fullTx": True,
                                    "inclStaking": True
                                }],
                                endpoint=endpoints[beacon_shard_id])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    for blk in response:
        assert_valid_json_structure(reference_response_blk, blk)
        for stx in blk["stakingTransactions"]:
            assert_valid_json_structure(reference_staking_response, stx)
            if stx["hash"] == s0_validator["hash"]:
                assert stx["type"] == "CreateValidator"
                assert_valid_json_structure(reference_create_validator_msg, stx["msg"])
    assert len(response[-1]["stakingTransactions"]) > 0, "Expected staking transactions on last block"
    start_num, end_num = int(start_blk, 16), int(end_blk, 16)
    for blk in response:
        blk_num = int(blk["number"], 16)
        assert start_num <= blk_num <= end_num, f"Got block number {blk_num}, which is not in range [{start_num},{end_num}]"


@txs.staking
@mutually_exclusive_test(scope=_mutex_scope)
def test_get_blocks_v2(s0_validator):
    """
    Only difference in param of RPC is hex string in v1 and decimal in v2.

    Note: param options for 'withSigners' will NOT return any sensical data
    in staking epoch (since it returns ONE addresses) and is subject to removal, thus is not tested here.
    """
    reference_response_blk = {
        "difficulty": 0,
        "epoch": 1,
        "extraData": "0x",
        "gasLimit": 80000000,
        "gasUsed": 5317060,
        "hash": "0xc0438fb59641cf000ddede158cf3707b6b96f2fbf7eaf40386eb91a0dc4305a4",
        "logsBloom": "0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
        "miner": "one1pdv9lrdwl0rg5vglh4xtyrv3wjk3wsqket7zxy",
        "mixHash": "0x0000000000000000000000000000000000000000000000000000000000000000",
        "nonce": 0,
        "number": 11,
        "parentHash": "0x57b4221951b61025eccea748c3a67dc2f1dafa9db278ac4d67135061432de6d0",
        "receiptsRoot": "0x37f9bea40135162a9eb2164266b2152a3909ee94dd2f908cdb091afb90724e1e",
        "size": 1021,
        "stakingTransactions": [],
        "stateRoot": "0x33109119529b1d282909975ce846a3eeb1b76681d7beebfa5cf79adfe4a1c4d7",
        "timestamp": 1594992546,
        "transactions": [],
        "transactionsRoot": "0xf4ab626bfc3bf9781ddef818f85cc81c345010b7b6abaeb27d0237c8a1ee1ac5",
        "uncles": [],
        "viewID": 11
    }
    reference_staking_response = {
        "blockHash": "0x0000000000000000000000000000000000000000000000000000000000000000",
        "blockNumber": None,
        "from": "one13muqj27fcd59gfrv7wzvuaupgkkwvwzlxun0ce",
        "timestamp": 0,
        "gas": 5317124,
        "gasPrice": 1000000000,
        "hash": "0x6e54fc7102daa31372027912b7f441ab9b9acafb9fa93b72dc9380321bacdbe2",
        "nonce": 0,
        "transactionIndex": 0,
        "v": "0x27",
        "r": "0xe03993350ed72c70198bbb9b0c962eba1ba08c6c46f66c50a878f84970120941",
        "s": "0x421342afa7dd527edadfb8fc0b3b80c41ba3fcd390cc2ff95bc18b89c58850ca",
        "type": "CreateValidator",
        "msg": None
    }
    reference_create_validator_msg = {
        "amount": 10000000000000000000000,
        "commissionRate": 100000000000000000,
        "details": "test",
        "identity": "test3",
        "maxChangeRate": 50000000000000000,
        "maxCommissionRate": 900000000000000000,
        "maxTotalDelegation": 10000000000000000000000000,
        "minSelfDelegation": 10000000000000000000000,
        "name": "test",
        "securityContact": "test",
        "slotPubKeys": [
            "29cdd2ea5ef25bfee0bbc649065ceb2d0e19cc25f42541154eca69c0ff923971e20352fbfeeac5d17f8f6c6fc5871e88"
        ],
        "validatorAddress": "one13muqj27fcd59gfrv7wzvuaupgkkwvwzlxun0ce",
        "website": "test"
    }

    init_tx = get_staking_transaction(s0_validator["hash"])
    start_blk, end_blk = max(0, int(init_tx["blockNumber"], 16) - 2), int(init_tx["blockNumber"], 16)
    raw_response = base_request("hmyv2_getBlocks",
                                params=[start_blk, end_blk, {
                                    "fullTx": True,
                                    "inclStaking": True
                                }],
                                endpoint=endpoints[beacon_shard_id])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    for blk in response:
        assert_valid_json_structure(reference_response_blk, blk)
        for stx in blk["stakingTransactions"]:
            assert_valid_json_structure(reference_staking_response, stx)
            if stx["hash"] == s0_validator["hash"]:
                assert stx["type"] == "CreateValidator"
                assert_valid_json_structure(reference_create_validator_msg, stx["msg"])
    assert len(response[-1]["stakingTransactions"]) > 0, "Expected staking transactions on last block"
    for blk in response:
        assert start_blk <= blk[
            "number"] <= end_blk, f"Got block number {blk['number']}, which is not in range [{start_blk},{end_blk}]"


@txs.staking
def test_get_staking_transaction_history_v1(s0_validator):
    """
    No staking transactions for the 'to' account of `account_test_tx`.

    This method may not be implemented, skip if this is the case
    """
    reference_response = {
        "staking_transactions": [
            {
                "blockHash": "0xc0438fb59641cf000ddede158cf3707b6b96f2fbf7eaf40386eb91a0dc4305a4",
                "blockNumber": "0xb",
                "from": "one109r0tns7av5sjew7a7fkekg4fs3pw0h76pp45e",
                "timestamp": "0x5f11a7a2",
                "gas": "0x5121c4",
                "gasPrice": "0x3b9aca00",
                "hash": "0xf80460f1ad041a0a0e841da717fc5b7959b1a7e9a0ce9a25cd70c0ce40d5ff26",
                "nonce": "0x0",
                "transactionIndex": "0x0",
                "v": "0x27",
                "r": "0x2348daabe696c4370379b9102dd85da6d4fed52f0f511ff0448a21c001ee75a7",
                "s": "0x1a67f9f40e0de02b50d5d7295f200fea7f950c1b59aa7efa8d225294c4fdbc5e",
                "type": "CreateValidator",
                "msg": None
            },
        ]
    }
    reference_create_validator_msg = {
        "amount": "0x21e19e0c9bab2400000",
        "commissionRate": "0x16345785d8a0000",
        "details": "test",
        "identity": "test0",
        "maxChangeRate": "0xb1a2bc2ec50000",
        "maxCommissionRate": "0xc7d713b49da0000",
        "maxTotalDelegation": "0x84595161401484a000000",
        "minSelfDelegation": "0x21e19e0c9bab2400000",
        "name": "test",
        "securityContact": "test",
        "slotPubKeys": [
            "4f41a37a3a8d0695dd6edcc58142c6b7d98e74da5c90e79b587b3b960b6a4f5e048e6d8b8a000d77a478d44cd640270c"
        ],
        "validatorAddress": "one109r0tns7av5sjew7a7fkekg4fs3pw0h76pp45e",
        "website": "test"
    }
    reference_response_short = {
        "staking_transactions": [
            "0x5718a2fda967f051611ccfaf2230dc544c9bdd388f5759a42b2fb0847fc8d759",
        ]
    }

    try:
        raw_response = base_request("hmy_getStakingTransactionsHistory",
                                    params=[{
                                        "address": s0_validator["validator-addr"],
                                        "pageIndex": 0,
                                        "pageSize": 1000,
                                        "fullTx": False,
                                        "txType": "ALL",
                                        "order": "ASC"
                                    }],
                                    endpoint=endpoints[initial_funding[0]["from-shard"]])
        response = check_and_unpack_rpc_response(raw_response, expect_error=False)
        assert_valid_json_structure(reference_response_short, response)

        raw_response = base_request("hmy_getStakingTransactionsHistory",
                                    params=[{
                                        "address": s0_validator["validator-addr"],
                                        "pageIndex": 0,
                                        "pageSize": 1000,
                                        "fullTx": True,
                                        "txType": "ALL",
                                        "order": "ASC"
                                    }],
                                    endpoint=endpoints[initial_funding[0]["from-shard"]])
        response = check_and_unpack_rpc_response(raw_response, expect_error=False)
        assert_valid_json_structure(reference_response, response)
        for stx in response["staking_transactions"]:
            if stx["hash"] == s0_validator["hash"]:
                assert stx["type"] == "CreateValidator"
                assert_valid_json_structure(reference_create_validator_msg, stx["msg"])
    except Exception as e:
        pytest.skip(traceback.format_exc())
        pytest.skip(f"Exception: {e}")


@txs.staking
def test_get_staking_transaction_history_v2(s0_validator):
    """
    No staking transactions for the 'to' account of `account_test_tx`.
    """
    reference_response = {
        "staking_transactions": [
            {
                "blockHash": "0xc0438fb59641cf000ddede158cf3707b6b96f2fbf7eaf40386eb91a0dc4305a4",
                "blockNumber": 11,
                "from": "one109r0tns7av5sjew7a7fkekg4fs3pw0h76pp45e",
                "timestamp": 1594992546,
                "gas": 5317060,
                "gasPrice": 1000000000,
                "hash": "0xf80460f1ad041a0a0e841da717fc5b7959b1a7e9a0ce9a25cd70c0ce40d5ff26",
                "nonce": 0,
                "transactionIndex": 0,
                "v": "0x27",
                "r": "0x2348daabe696c4370379b9102dd85da6d4fed52f0f511ff0448a21c001ee75a7",
                "s": "0x1a67f9f40e0de02b50d5d7295f200fea7f950c1b59aa7efa8d225294c4fdbc5e",
                "type": "CreateValidator",
                "msg": None
            },
        ]
    }
    reference_create_validator_msg = {
        "amount": 10000000000000000000000,
        "commissionRate": 100000000000000000,
        "details": "test",
        "identity": "test0",
        "maxChangeRate": 50000000000000000,
        "maxCommissionRate": 900000000000000000,
        "maxTotalDelegation": 10000000000000000000000000,
        "minSelfDelegation": 10000000000000000000000,
        "name": "test",
        "securityContact": "test",
        "slotPubKeys": [
            "4f41a37a3a8d0695dd6edcc58142c6b7d98e74da5c90e79b587b3b960b6a4f5e048e6d8b8a000d77a478d44cd640270c"
        ],
        "validatorAddress": "one109r0tns7av5sjew7a7fkekg4fs3pw0h76pp45e",
        "website": "test"
    }
    reference_response_short = {
        "staking_transactions": [
            "0x5718a2fda967f051611ccfaf2230dc544c9bdd388f5759a42b2fb0847fc8d759",
        ]
    }

    raw_response = base_request("hmyv2_getStakingTransactionsHistory",
                                params=[{
                                    "address": s0_validator["validator-addr"],
                                    "pageIndex": 0,
                                    "pageSize": 1000,
                                    "fullTx": False,
                                    "txType": "ALL",
                                    "order": "ASC"
                                }],
                                endpoint=endpoints[initial_funding[0]["from-shard"]])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response_short, response)

    raw_response = base_request("hmyv2_getStakingTransactionsHistory",
                                params=[{
                                    "address": s0_validator["validator-addr"],
                                    "pageIndex": 0,
                                    "pageSize": 1000,
                                    "fullTx": True,
                                    "txType": "ALL",
                                    "order": "ASC"
                                }],
                                endpoint=endpoints[initial_funding[0]["from-shard"]])
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    for stx in response["staking_transactions"]:
        if stx["hash"] == s0_validator["hash"]:
            assert stx["type"] == "CreateValidator"
            assert_valid_json_structure(reference_create_validator_msg, stx["msg"])

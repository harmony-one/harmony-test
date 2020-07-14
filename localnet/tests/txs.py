#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stores all the transaction information used in the test suite.

INVARIANT: Each account only sends 1 plain transaction (per shard) except for initial transaction(s).
"""
import functools
import time
import json

from pyhmy import (
    account,
    blockchain
)
from pyhmy.rpc.request import (
    base_request
)

from utils import (
    check_and_unpack_rpc_response,
    is_valid_json_rpc
)

tx_timeout = 20  # In seconds

# Endpoints sorted by shard
endpoints = [
    "http://localhost:9599/",  # shard 0
    "http://localhost:9598/",  # shard 1
]

# ORDER MATERS: tx n cannot be sent without tx n-1 being sent first due to nonce
# Only exception on invariant.
initial_funding = [
    {
        # Used by: `account_test_tx`
        "from": "one1zksj3evekayy90xt4psrz8h6j2v3hla4qwz4ur",
        "to": "one1v92y4v2x4q27vzydf8zq62zu9g0jl6z0lx2c8q",
        # scissors matter runway reduce flush illegal ancient absurd scare young copper ticket direct wise person hobby tomato chest edge cost wine crucial vendor elevator
        "amount": "100000",
        "from-shard": 0,
        "to-shard": 0,
        "hash": "0x5718a2fda967f051611ccfaf2230dc544c9bdd388f5759a42b2fb0847fc8d759",
        "nonce": "0x0",
        "signed-raw-tx": "0xf86f80843b9aca0082520880809461544ab146a815e6088d49c40d285c2a1f2fe84f8a152d02c7e14af68000008028a076b6130bc018cedb9f8891343fd8982e0d7f923d57ea5250b8bfec9129d4ae22a00fbc01c988d72235b4c71b21ce033d4fc5f82c96710b84685de0578cff075a0a",
    },
    {
        # Used by: `cross_shard_txs`
        "from": "one1zksj3evekayy90xt4psrz8h6j2v3hla4qwz4ur",
        "to": "one1ue25q6jk0xk3dth4pxur9e742vcqfwulhwqh45",
        # obey scissors fiscal hood chaos grit all piano armed change general attract balcony hair cat outside hour quiz unhappy tattoo awful offer toddler invest
        "amount": "100000",
        "from-shard": 0,
        "to-shard": 0,
        "hash": "0x28c17c0a2736ba16930ad274e3ecbebea930e82553c7755e0b94c7d7cd1fd6f2",
        "nonce": "0x1",
        "signed-raw-tx": "0xf86f01843b9aca00825208808094e655406a5679ad16aef509b832e7d5533004bb9f8a152d02c7e14af68000008028a0c50737adb507870c2b6f3d9966f096526761730c6b80bd702c114e24aa094ac1a063c0463619123dbe7541687fba70952dab62ba639199750b04cd8902ccb6d615",
    },
    {
        # Used by: `test_get_pending_cx_receipts`
        "from": "one1zksj3evekayy90xt4psrz8h6j2v3hla4qwz4ur",
        "to": "one19l4hghvh40fyldxfznn0a3ss7d5gk0dmytdql4",
        # judge damage safe field faculty piece salon gentle riot unfair symptom sun exclude agree fantasy fossil catalog tool bounce tomorrow churn join very number
        "amount": "100000",
        "from-shard": 0,
        "to-shard": 0,
        "hash": "0x6bc3acc3b349edac6d3f563e78990a4566192d6fdab93814ea29ae9157d4085b",
        "nonce": "0x2",
        "signed-raw-tx": "0xf86f02843b9aca008252088080942feb745d97abd24fb4c914e6fec610f3688b3dbb8a152d02c7e14af68000008027a0abfa0480b878ca798a17e88251109761ed1d281f1da92faa21b6e456ad558774a016b460ec602b08f06a2845478269b1014b5491bdc0993988ca39f689b2405992",
    },
    {
        "from": "one1zksj3evekayy90xt4psrz8h6j2v3hla4qwz4ur",
        "to": "one1twhzfc2wr4j5ka7gs9pmllpnrdyaskcl5lq8ye",
        # science swim absent horse gas wink switch section soup pair chuckle rug paddle lottery message veteran poverty alone current prize spoil dune super crumble
        "amount": "100000",
        "from-shard": 0,
        "to-shard": 0,
        "hash": "0xdcd7870635acd3fb1e962c76f2e3cddbeb421238fcf702e3d1fa42ca6de434b2",
        "nonce": "0x3",
        "signed-raw-tx": "0xf86f03843b9aca008252088080945bae24e14e1d654b77c88143bffc331b49d85b1f8a152d02c7e14af68000008027a0356e6bfd8718c7102f0d94fdb8be1cba090daf44c71086f9817de3b264cb54c2a052c8781691dce63997ca4f765adec7b351a9a23a80a97bcf238ccbdf8a71f71f",
    },
    {
        "from": "one1zksj3evekayy90xt4psrz8h6j2v3hla4qwz4ur",
        "to": "one1u57rlv5q82deja6ew2l9hdy7ag3dwnw57x8s9t",
        # noble must all evoke core grass goose describe latin left because awful gossip tuna broccoli tomorrow piece enable theme comic below avoid dove high
        "amount": "100000",
        "from-shard": 0,
        "to-shard": 0,
        "hash": "0xa8a678243fffcfc16ff8f35315094aafc029175b962ec595f7c71efce4a47c8a",
        "nonce": "0x4",
        "signed-raw-tx": "0xf86f04843b9aca00825208808094e53c3fb2803a9b99775972be5bb49eea22d74dd48a152d02c7e14af68000008028a0d2f061075852ee5b2572b18e8879d5656e8660113d88f2b806961b25312e5ae1a078004b6b332f09b1a53c3cbad6fd427fa57b0b368ae2126e458b9622d1668edf",
    }
]


def cross_shard(fn):
    """
    Decorator for tests that requires a cross shard transaction
    """
    threshold_epoch = 1

    @functools.wraps(fn)
    def wrap(*args, **kwargs):
        while not all(blockchain.get_current_epoch(e) >= threshold_epoch for e in endpoints):
            time.sleep(1)
        return fn(*args, **kwargs)

    return wrap


def staking(fn):
    """
    Decorator for tests that requires staking epoch
    """
    threshold_epoch = blockchain.get_staking_epoch(endpoints[0])

    @functools.wraps(fn)
    def wrap(*args, **kwargs):
        while not all(blockchain.get_current_epoch(e) >= threshold_epoch for e in endpoints):
            time.sleep(1)
        return fn(*args, **kwargs)

    return wrap


def send_and_confirm_transaction(tx_data):
    """
    Send and confirm the given transaction (`tx_data`).
    Node that tx_data follow the format of one of the entries in `initial_funding`
    """
    assert isinstance(tx_data, dict), f"Sanity check: expected tx_data to be of type dict not {type(tx_data)}"
    for el in ["from", "from-shard", "signed-raw-tx", "hash"]:
        assert el in tx_data.keys(), f"Expected {el} as a key in {json.dumps(tx_data, indent=2)}"

    # Validate tx sender
    assert_valid_test_from_address(tx_data["from"], tx_data["from-shard"], is_staking=False)

    # Send tx
    response = base_request('hmy_sendRawTransaction', params=[tx_data["signed-raw-tx"]],
                            endpoint=endpoints[tx_data["from-shard"]])
    assert is_valid_json_rpc(response), f"Invalid JSON response: {response}"
    # Do not check for errors since resending initial txs is fine & failed txs will be caught in confirm timeout.

    # Confirm tx within timeout window
    start_time = time.time()
    while time.time() - start_time <= tx_timeout:
        tx_response = get_transaction(tx_data["hash"], tx_data["from-shard"])
        if tx_response is not None:
            return tx_response
    raise AssertionError("Could not confirm transactions on-chain.")


def get_transaction(tx_hash, shard):
    """
    Fetch the transaction for the given hash on the given shard.
    It also checks that the RPC response is valid.
    """
    assert isinstance(tx_hash, str), f"Sanity check: expect tx hash to be of type str not {type(tx_hash)}"
    assert isinstance(shard, int), f"Sanity check: expect shard to be of type int not {type(shard)}"
    raw_response = base_request('hmy_getTransactionByHash', params=[tx_hash], endpoint=endpoints[shard])
    return check_and_unpack_rpc_response(raw_response, expect_error=False)


def assert_valid_test_from_address(address, shard, is_staking=False):
    """
    Asserts that the given address is a valid 'from' address for a test transaction.

    Note that this considers the invariant for transactions.
    """
    assert isinstance(address, str), f"Sanity check: Expect address {address} as a string."
    assert isinstance(shard, int), f"Sanity check: Expect shard {shard} as am int."
    assert isinstance(is_staking, bool), f"Sanity check: Expect is_staking {is_staking} as a bool."
    assert account.is_valid_address(address), f"{address} is an invalid ONE address"
    if not account.get_balance(address, endpoint=endpoints[shard]) >= 1e18:
        raise AssertionError(f"Account {address} does not have at least 1 ONE on shard {shard}")
    if not is_staking and account.get_transaction_count(address, endpoint=endpoints[shard]) != 0:
        raise AssertionError(f"Account {address} has already sent a transaction, breaking the txs invariant")
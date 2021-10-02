#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stores all the transaction information used in the test suite.

INVARIANT: Each account only sends 1 plain transaction (per shard) except for initial transaction(s).
"""
import functools
import json
import time
import random

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
beacon_shard_id = 0
_is_cross_shard_era = False
_is_staking_era = False

# Endpoints sorted by shard
endpoints = [
    "http://localhost:9598/",  # shard 0
    "http://localhost:9596/",  # shard 1
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
        # Used by: `test_pending_transactions_v1`
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
        # Used by: `test_pending_transactions_v2`
        "from": "one1zksj3evekayy90xt4psrz8h6j2v3hla4qwz4ur",
        "to": "one1u57rlv5q82deja6ew2l9hdy7ag3dwnw57x8s9t",
        # noble must all evoke core grass goose describe latin left because awful gossip tuna broccoli tomorrow piece enable theme comic below avoid dove high
        "amount": "100000",
        "from-shard": 0,
        "to-shard": 0,
        "hash": "0xa8a678243fffcfc16ff8f35315094aafc029175b962ec595f7c71efce4a47c8a",
        "nonce": "0x4",
        "signed-raw-tx": "0xf86f04843b9aca00825208808094e53c3fb2803a9b99775972be5bb49eea22d74dd48a152d02c7e14af68000008028a0d2f061075852ee5b2572b18e8879d5656e8660113d88f2b806961b25312e5ae1a078004b6b332f09b1a53c3cbad6fd427fa57b0b368ae2126e458b9622d1668edf",
    },
    {
        # Used by: `test_send_raw_transaction_v1`
        "from": "one1zksj3evekayy90xt4psrz8h6j2v3hla4qwz4ur",
        "to": "one1p5x4t7mvd94jn5awxmhlvgqmlazx5egzz7rveg",
        # mushroom penalty pulse blouse horror into color call grace observe famous bridge consider universe uncle horror people tank useless alley uncover emotion next ke
        "amount": "100000",
        "from-shard": 0,
        "to-shard": 0,
        "hash": "0x1d0d4111d9f5d2d28e85d5ebd1460944e8d328df45a2bbfae1de309c3a6cf632",
        "nonce": "0x5",
        "signed-raw-tx": "0xf86f05843b9aca008252088080940d0d55fb6c696b29d3ae36eff6201bff446a65028a152d02c7e14af68000008027a06dee240ff456073c11fd093e24ba29eda88e00cd710c05d83c855cce1aff47a2a06bf74d512215a2ec02fb5034a1e344901706387e72ce08b5a37a2f434717f859",
    },
    {
        # Used by: `test_send_raw_transaction_v2`
        "from": "one1zksj3evekayy90xt4psrz8h6j2v3hla4qwz4ur",
        "to": "one13lu674f3jkfk2qhsngfc2vhcf372wprctdjvgu",
        # organ truly miss sell visual pulse maid element slab sugar bullet absorb digital space dance long another man cherry fruit effort pluck august flag
        "amount": "100000",
        "from-shard": 0,
        "to-shard": 0,
        "hash": "0x855e230866377e00a56ae6958c8acfe6f0d19f8e71a0c323d92794aeda5c6bc8",
        "nonce": "0x6",
        "signed-raw-tx": "0xf86f06843b9aca008252088080948ff9af553195936502f09a138532f84c7ca704788a152d02c7e14af68000008028a01a4c6dbc9177cf9057de09d4f654950a38aba83e98502d59b478f899b196c4aaa00652c34a53082aee876713954ce70a21288c3727c29fb9c729ce10f19d106370",
    },
    {
        # Used by: `test_get_current_transaction_error_sink`
        "from": "one1zksj3evekayy90xt4psrz8h6j2v3hla4qwz4ur",
        "to": "one1ujsjs4mhds75xnws0yx0v8l2rvyp67arwzqrvz",
        # video mind cash involve kitten mobile multiply shine foam citizen minimum busy slab keen under food swamp fortune dumb slice beyond piano forest call
        "amount": "100000",
        "from-shard": 0,
        "to-shard": 0,
        "hash": "0x718a7299e1591bd2eb7bea7de6efc044de3d1a6ce2d96e85b17f892f118d2455",
        "nonce": "0x7",
        "signed-raw-tx": "0xf86f07843b9aca00825208808094e4a12857776c3d434dd0790cf61fea1b081d7ba38a152d02c7e14af68000008028a0cdb715640768dbdbaa06b98ca8c346717b3c753a2ad70de81330f52cd6a1cbc1a05ced9fe853996e05216783fdab83ca91b6010605ad68d0153596b0fc35e8c40b",
    },
    {
        # Used by: `deployed_contract`
        "from": "one1zksj3evekayy90xt4psrz8h6j2v3hla4qwz4ur",
        "to": "one156wkx832t0nxnaq6hxawy4c3udmnpzzddds60a",
        # dove turkey fitness brush drip page senior lemon other climb govern fantasy entry reflect when biology hunt victory turkey volcano casino movie shed valve
        "amount": "100000",
        "from-shard": 0,
        "to-shard": 0,
        "hash": "0x6674d1223fdff897d74b3483da2086f8370da747e93b6f6c32fe59f518c2b777",
        "nonce": "0x8",
        "signed-raw-tx": "0xf86f08843b9aca00825208808094a69d631e2a5be669f41ab9bae25711e37730884d8a152d02c7e14af68000008027a03f1c0d190eec991d407848227cc0f4f75ba157f187f539dfa6050dd1cfa253a4a00cbc0eb6f81f3a0049db90496c62598d267c5c82b203ab12e969e49012d32be8",
    },
    {
        # Used by: `s0_validator`
        "from": "one1zksj3evekayy90xt4psrz8h6j2v3hla4qwz4ur",
        "to": "one109r0tns7av5sjew7a7fkekg4fs3pw0h76pp45e",
        # proud guide else desk renew leave fix post fat angle throw gain field approve year umbrella era axis horn unlock trip guide replace accident
        "amount": "100000",
        "from-shard": 0,
        "to-shard": 0,
        "hash": "0x5def784f5b9a8683e7c98b202a0e2ed303f84224900f95775d92be54e1bcb504",
        "nonce": "0x9",
        "signed-raw-tx": "0xf86f09843b9aca008252088080947946f5ce1eeb290965deef936cd9154c22173efe8a152d02c7e14af68000008027a0c991fab63ede6b83f7872020ac54fa9ba900cce8aa6b0dc07dbca1bfb840c97da029795861de7c6d839ce54903f960e3326f03a84c90deed384f7dcfc8d9703a16",
    },
    {
        # Used by: `s1_validator`
        "from": "one1zksj3evekayy90xt4psrz8h6j2v3hla4qwz4ur",
        "to": "one1nmy8quw0924fss4r9km640pldzqegjk4wv4wts",
        # aisle aware spatial sausage vibrant tennis useful admit junior light calm wear caution snack seven spoon yellow crater giraffe mirror spare educate result album
        "amount": "100000",
        "from-shard": 0,
        "to-shard": 0,
        "hash": "0xf66f6cb67ad9e1622ca77d50ec52a25be37bcd601606d7530711e58aca891245",
        "nonce": "0xa",
        "signed-raw-tx": "0xf86f0a843b9aca008252088080949ec87071cf2aaa9842a32db7aabc3f6881944ad58a152d02c7e14af68000008027a0efa56eae2e0457010ad57e46cf4332158e670aadee8586c586f74047fb6e4211a038827d2e57a50ca7b311c06d90426ddad659d68e598342f94a1b430f2adb39da",
    },
    {
        # Used by: `test_delegation` & `test_undelegation`
        "from": "one1zksj3evekayy90xt4psrz8h6j2v3hla4qwz4ur",
        "to": "one1v895jcvudcktswcmg2sldvmxvtvvdj2wuxj3hx",
        # web topple now acid repeat inspire tomato inside nominee reflect latin salmon garbage negative liberty win royal faith hammer lawsuit west toddler payment coffee
        "amount": "100000",
        "from-shard": 0,
        "to-shard": 0,
        "hash": "0xb6d3a97d472a5b0259de0cd3ad0d41c6cc7e7b98ee0c314c29d09261a92e2354",
        "nonce": "0xb",
        "signed-raw-tx": "0xf86f0b843b9aca0082520880809461cb49619c6e2cb83b1b42a1f6b36662d8c6c94e8a152d02c7e14af68000008028a00e1b96e61e8bb4c4bad89ed40d6cc43fcf003251fa5e9ed1cdf63e2a38ca110ca0675a1964ad3c32a2946f9bc86984b8910f81f752e2ef0ef9b1eb4cf9aec1032d",
    },
    {
        # Used by: `test_pending_staking_transactions_v1`
        "from": "one1zksj3evekayy90xt4psrz8h6j2v3hla4qwz4ur",
        "to": "one13v9m45m6yk9qmmcgyq603ucy0wdw9lfsxzsj9d",
        # grief comfort prefer wealth foam consider kingdom secret comfort brush kit cereal hello ripple choose follow mammal swap city pistol drip unfair glass jacket
        "amount": "100000",
        "from-shard": 0,
        "to-shard": 0,
        "hash": "0x85c7de662be7bbf0fd3be0bf8d0c5f910c4fd8d54ff8bc023725d09a9769fd6e",
        "nonce": "0xc",
        "signed-raw-tx": "0xf86f0c843b9aca008252088080948b0bbad37a258a0def082034f8f3047b9ae2fd308a152d02c7e14af68000008027a073fc972cfce2875a6ed11b9db264f4ceaf5ef87a073955f08af18d1d6c2a914ba07bcea61a65ad903a42ba06e369eedd784049b789058279c2b13a5c9065df2a76",
    },
    {
        # Used by: `test_pending_staking_transactions_v2`
        "from": "one1zksj3evekayy90xt4psrz8h6j2v3hla4qwz4ur",
        "to": "one13muqj27fcd59gfrv7wzvuaupgkkwvwzlxun0ce",
        # suit gate simple ship chicken labor twenty attend knee click quit emerge minimum veteran need group verify dish baby argue guard win tip swear
        "amount": "100000",
        "from-shard": 0,
        "to-shard": 0,
        "hash": "0xffe73340c5a6e411c74fb29875dcb84df3d9c36fbbdb16cd3c47a3399ff8b0b9",
        "nonce": "0xd",
        "signed-raw-tx": "0xf86f0d843b9aca008252088080948ef8092bc9c36854246cf384ce778145ace6385f8a152d02c7e14af68000008027a0269c69eef2be5633b297a93efa20bf6bf0e56c8dc9eb869a4af6864fcfc28c75a0188df392c87d1552cff6f54736cf6811efed7ea3464db4c0618de1bce6163be6",
    },
]


def is_cross_shard_era():
    """
    Returns if the network is in cross shard tx era...
    """
    global _is_cross_shard_era
    if _is_cross_shard_era:
        return True
    time.sleep(random.uniform(0.5, 1.5))  # Random to stop burst spam of RPC calls.
    if all(blockchain.get_current_epoch(e) >= 1 for e in endpoints):
        _is_cross_shard_era = True
        return True
    return False


def cross_shard(fn):
    """
    Decorator for tests that requires a cross shard transaction
    """

    @functools.wraps(fn)
    def wrap(*args, **kwargs):
        while not is_cross_shard_era():
            pass
        return fn(*args, **kwargs)

    return wrap


def is_staking_era():
    """
    Returns if the network is in staking era...
    """
    global _is_staking_era
    if _is_staking_era:
        return True
    time.sleep(random.uniform(0.5, 1.5))  # Random to stop burst spam of RPC calls.
    threshold_epoch = blockchain.get_prestaking_epoch(endpoints[beacon_shard_id])
    if all(blockchain.get_current_epoch(e) >= threshold_epoch for e in endpoints):
        _is_staking_era = True
    return False


def staking(fn):
    """
    Decorator for tests that requires staking epoch
    """

    @functools.wraps(fn)
    def wrap(*args, **kwargs):
        while not is_staking_era():
            pass
        return fn(*args, **kwargs)

    return wrap


def send_transaction(tx_data, confirm_submission=False):
    """
    Send the given transaction (`tx_data`), and check that it got submitted
    to tx pool if `confirm_submission` is enabled.

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
    if confirm_submission:
        tx_hash = check_and_unpack_rpc_response(response, expect_error=False)
        assert tx_hash == tx_data["hash"], f"Expected submitted transaction to get tx hash of {tx_data['hash']}, " \
                                           f"got {tx_hash}"
    else:
        assert is_valid_json_rpc(response), f"Invalid JSON response: {response}"


def send_staking_transaction(tx_data, confirm_submission=False):
    """
    Send the given staking transaction (`tx_data`), and check that it got submitted
    to tx pool if `confirm_submission` is enabled.

    Node that tx_data follow the format of one of the entries in `initial_funding`
    """
    assert isinstance(tx_data, dict), f"Sanity check: expected tx_data to be of type dict not {type(tx_data)}"
    for el in ["signed-raw-tx", "hash"]:
        assert el in tx_data.keys(), f"Expected {el} as a key in {json.dumps(tx_data, indent=2)}"

    # Send tx
    response = base_request('hmy_sendRawStakingTransaction', params=[tx_data["signed-raw-tx"]],
                            endpoint=endpoints[0])
    if confirm_submission:
        tx_hash = check_and_unpack_rpc_response(response, expect_error=False)
        assert tx_hash == tx_data["hash"], f"Expected submitted staking transaction to get tx hash " \
                                           f"of {tx_data['hash']}, got {tx_hash}"
    else:
        assert is_valid_json_rpc(response), f"Invalid JSON response: {response}"


def send_and_confirm_transaction(tx_data, timeout=tx_timeout):
    """
    Send and confirm the given transaction (`tx_data`) within the given `timeout`.

    Node that tx_data follow the format of one of the entries in `initial_funding`.

    Note that errored tx submission will not return an error early, instead, failed transactions will be
    caught by timeout. This is done because it is possible to submit the same transaction multiple times,
    thus causing the RPC to return an error, causing unwanted errors in tests that are ran in parallel.
    """
    assert isinstance(tx_data, dict), f"Sanity check: expected tx_data to be of type dict not {type(tx_data)}"
    for el in ["from-shard", "hash"]:
        assert el in tx_data.keys(), f"Expected {el} as a key in {json.dumps(tx_data, indent=2)}"

    send_transaction(tx_data, confirm_submission=False)
    # Do not check for errors since resending initial txs is fine & failed txs will be caught in confirm timeout.

    # Confirm tx within timeout window
    start_time = time.time()
    while time.time() - start_time <= timeout:
        tx_response = get_transaction(tx_data["hash"], tx_data["from-shard"])
        if tx_response is not None:
            if tx_response['blockNumber'] is not None:
                return tx_response
        time.sleep(random.uniform(0.2, 0.5))  # Random to stop burst spam of RPC calls.
    raise AssertionError("Could not confirm transactions on-chain.")


def send_and_confirm_staking_transaction(tx_data, timeout=tx_timeout * 2):
    """
    Send and confirm the given staking transaction (`tx_data`) within the given `timeout`.

    Node that tx_data follow the format of one of the entries in `initial_funding`.

    Note that errored tx submission will not return an error early, instead, failed transactions will be
    caught by timeout. This is done because it is possible to submit the same transaction multiple times,
    thus causing the RPC to return an error, causing unwanted errors in tests that are ran in parallel.
    """
    assert isinstance(tx_data, dict), f"Sanity check: expected tx_data to be of type dict not {type(tx_data)}"
    for el in ["hash"]:
        assert el in tx_data.keys(), f"Expected {el} as a key in {json.dumps(tx_data, indent=2)}"

    send_staking_transaction(tx_data, confirm_submission=False)
    # Do not check for errors since resending initial txs is fine & failed txs will be caught in confirm timeout.

    # Confirm tx within timeout window
    start_time = time.time()
    while time.time() - start_time <= timeout:
        tx_response = get_staking_transaction(tx_data["hash"])
        if tx_response is not None:
            if tx_response['blockNumber'] is not None:
                return tx_response
        time.sleep(random.uniform(0.2, 0.5))  # Random to stop burst spam of RPC calls.
    raise AssertionError("Could not confirm staking transaction on-chain.")


def get_transaction(tx_hash, shard):
    """
    Fetch the transaction for the given hash on the given shard.
    It also checks that the RPC response is valid.
    """
    assert isinstance(tx_hash, str), f"Sanity check: expect tx hash to be of type str not {type(tx_hash)}"
    assert isinstance(shard, int), f"Sanity check: expect shard to be of type int not {type(shard)}"
    raw_response = base_request('hmy_getTransactionByHash', params=[tx_hash], endpoint=endpoints[shard])
    return check_and_unpack_rpc_response(raw_response, expect_error=False)


def get_staking_transaction(tx_hash):
    """
    Fetch the staking transaction for the given hash on the given shard.
    It also checks that the RPC response is valid.
    """
    assert isinstance(tx_hash, str), f"Sanity check: expect tx hash to be of type str not {type(tx_hash)}"
    raw_response = base_request('hmy_getStakingTransactionByHash', params=[tx_hash], endpoint=endpoints[0])
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

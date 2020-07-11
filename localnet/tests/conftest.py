#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

from pyhmy import (
    util,
)
from pyhmy.rpc.request import (
    base_request
)
from txs import (
    endpoints,
    initial_funding
)


def pytest_sessionstart(session):
    """
    Start the test session by sending initial test funds.
    Will block until transactions are confirmed on-chain.
    """
    assert util.is_active_shard(endpoints[0], delay_tolerance=20), "Shard 0 is not making progress..."
    assert util.is_active_shard(endpoints[1], delay_tolerance=20), "Shard 1 is not making progress..."
    for tx in initial_funding:
        base_request('hmy_sendRawTransaction', params=[tx["signed-raw-tx"]], endpoint=endpoints[tx["from-shard"]])
    while True:
        assert util.is_active_shard(endpoints[0], delay_tolerance=20), "Shard 0 is not making progress..."
        assert util.is_active_shard(endpoints[1], delay_tolerance=20), "Shard 1 is not making progress..."
        sent_txs = []
        for tx in initial_funding:
            response = json.loads(base_request('hmy_getTransactionByHash',
                                               params=[tx["hash"]], endpoint=endpoints[tx["from-shard"]]))
            sent_txs.append(not response['result'] is None)
        if all(sent_txs):
            break

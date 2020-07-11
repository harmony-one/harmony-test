#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest


@pytest.mark.run(order=1)
def test_get_balance():
    assert 1 == 1


@pytest.mark.run(order=2)
def test_get_balance2():
    assert 1 == 1


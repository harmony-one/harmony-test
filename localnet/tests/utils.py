#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json


def is_valid_json_rpc(response):
    """
    Checks if the given `response` is a valid JSON RPC 2.0 response.
    """
    try:
        d = json.loads(response)
    except json.JSONDecodeError:
        return False
    if "jsonrpc" not in d.keys():
        return False
    if d["jsonrpc"] != "2.0":
        return False
    if 'result' in d.keys():
        if "id" not in d.keys():
            return False
        return True
    elif 'error' in d.keys():
        error = d['error']
        if not isinstance(error, dict):
            return False
        if "code" not in error.keys():
            return False
        if not isinstance(error["code"], int):
            return False
        if "message" not in error.keys():
            return False
        if not isinstance(error["message"], str):
            return False
        return True
    else:
        return False


def assert_valid_dictionary_structure(reference, candidate):
    """
    Asserts that the given `candidate` dict has the same keys and values as the `reference` dict.
    """
    assert isinstance(reference, dict), f"Sanity check, given reference type must be a dictionary, not {type(reference)}"
    assert isinstance(candidate, dict), f"Sanity check, given reference type must be a dictionary, not {type(candidate)}"
    for key in reference.keys():
        assert key in candidate.keys(), f"Expected key '{key}' in {json.dumps(candidate, indent=2)}"
        reference_type = type(reference[key])
        assert isinstance(candidate[key], reference_type), f"Expected type {reference_type} for key '{key}' in {json.dumps(candidate, indent=2)}, not {type(candidate[key])}"
        if reference_type == dict:
            assert_valid_dictionary_structure(reference[key], candidate[key])

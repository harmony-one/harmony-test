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


def assert_valid_json_structure(reference, candidate):
    """
    Asserts that the given `candidate` dict (from JSON format) has the
    same keys and values as the `reference` dict (from JSON format).

    Note that if there is a list, the OVERLAPPING elements are the ONLY elements checked.
    """
    assert type(reference) == type(candidate), f"Expected type {type(reference)} not {type(candidate)} in {candidate}"
    if type(reference) == list and reference and candidate:  # If no element in list to check, ignore...
        for i in range(min(len(reference), len(candidate))):
            assert_valid_json_structure(reference[i], candidate[i])
    elif type(reference) == dict:
        for key in reference.keys():
            assert key in candidate.keys(), f"Expected key '{key}' in {json.dumps(candidate, indent=2)}"
            reference_type = type(reference[key])
            assert isinstance(candidate[key], reference_type), f"Expected type {reference_type} for key '{key}' in {json.dumps(candidate, indent=2)}, not {type(candidate[key])}"
            if reference_type == dict or reference_type == list:
                assert_valid_json_structure(reference[key], candidate[key])


def check_and_unpack_rpc_response(response, expect_error=False):
    if not response:
        raise AssertionError("No response...")
    assert is_valid_json_rpc(response), f"Invalid JSON response: {response}"
    response = json.loads(response)
    if expect_error:
        assert "error" in response.keys(), f"Expected error in RPC response: {json.dumps(response, indent=2)}"
        return response["error"]
    else:
        assert "result" in response.keys(), f"Expected result in RPC response: {json.dumps(response, indent=2)}"
        return response["result"]

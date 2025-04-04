#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for debugging RPC operations using `debug_traceCall`.

This script contains unit tests that verify the behavior of Ethereum-compatible
`debug_traceCall` RPC operations with various overrides, such as:
- **Block Overrides:** Simulating different block parameters.
- **State Overrides:** Modifying contract state without on-chain effects.
- **Gas Usage Analysis:** Validating execution and calldata costs.
- **Struct Logs Verification:** Ensuring correct execution traces.

Each test function simulates contract execution under different scenarios and
validates that gas consumption, return values, and struct logs behave as expected.
"""

import pytest

from pyhmy.rpc.request import base_request

from txs import debug_endpoints

from utils import (
    check_and_unpack_rpc_response,
    assert_valid_json_structure,
    get_calldata_gas,
)

DEFAULT_GAS = 21000


def test_debug_traceCall_block_override():
    """
    Tests the `debug_traceCall` RPC method with block overrides.

    This function simulates a smart contract call using the `debug_traceCall`
    method, while overriding certain block parameters (e.g., gas limit, timestamp).
    It verifies that the response matches the expected gas usage and structure.

    **Test Details:**
    - Calls a contract with the **bytecode `0x6001600101`** (`PUSH1 1`, `PUSH1 1`, `ADD`).
    - Uses a reference response to validate the returned JSON structure.
    - Ensures the transaction does **not fail** and that `structLogs` remains empty.
    - Computes the **expected gas usage**, accounting for calldata cost.

    **Block Overrides:**
    - **Gas Limit:** `0xF424000`
    - **Timestamp:** `0x5F5E100`
    - **Block Number:** `0x10`
    - **Fee Recipient:** `0xBBBB...BBBB`

    **Assertions:**
    - The transaction **must not fail** (`failed` should be `False`).
    - **No opcode execution logs (`structLogs` must be empty)**.
    - **Gas usage must match the expected value**

    **Returns:**
    - None (raises an assertion error if the test fails).
    """
    reference_response = {
        "gas": 21080,
        "failed": False,
        "returnValue": "",
        "structLogs": [],
    }

    main_smart_contract_call = "0x6001600101"
    raw_response = base_request(
        "debug_traceCall",
        params=[
            {
                "from": "0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                "to": "0xBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
                "data": main_smart_contract_call,
            },
            "latest",
            {
                "blockOverrides": {
                    "gasLimit": "0xF424000",
                    "timestamp": "0x5F5E100",
                    "number": "0x10",
                    "feeRecipient": "0xBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
                }
            },
        ],
        endpoint=debug_endpoints[0],
    )
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    calldata_gas_used = get_calldata_gas(main_smart_contract_call)
    assert response["failed"] is False
    assert not response["structLogs"]
    assert response["gas"] == DEFAULT_GAS + calldata_gas_used


def test_debug_traceCall_state_override_same_simulated_call():
    """
    Tests `debug_traceCall` with `stateOverrides` where the overridden contract code
    matches the simulated contract call.

    This function:
    - Executes a contract call (`0x6003600401`) using `debug_traceCall`.
    - Overrides the contract's on-chain state by setting:
      - **Balance** (`0xDE0B6B3A7640000`)
      - **Nonce** (`0x1`)
      - **Code** (`0x6003600401`, same as transaction calldata).
    - Validates that the response structure matches an expected reference.
    - Computes the expected **gas usage** by summing:
      - The gas cost of calldata (based on `get_calldata_gas`).
      - The gas used during execution (sum of `gasCost` in `structLogs`).

    **Assertions:**
    - The transaction **must not fail** (`failed` should be `False`).
    - **Execution trace (`structLogs`) must be present**.
    - **Gas usage must match expectations**:
      ```
      response["gas"] == DEFAULT_GAS + calldata_gas_used + total_gas_used
      ```

    **Why This Test?**
    - Ensures that `stateOverrides` properly replaces the contract code.
    - Validates that `debug_traceCall` executes the modified code correctly.
    - Confirms that gas usage is correctly computed for overridden state.

    **Returns:**
    - None (raises assertion errors if the test fails).
    """
    reference_response = {
        "gas": 21089,
        "failed": False,
        "returnValue": "",
        "structLogs": [
            {
                "pc": 0,
                "op": "PUSH1",
                "callerAddress": "0xcccccccccccccccccccccccccccccccccccccccc",
                "contractAddress": "0xdddddddddddddddddddddddddddddddddddddddd",
                "gas": 9223372036854754727,
                "gasCost": 3,
                "depth": 1,
            },
            {
                "pc": 2,
                "op": "PUSH1",
                "callerAddress": "0xcccccccccccccccccccccccccccccccccccccccc",
                "contractAddress": "0xdddddddddddddddddddddddddddddddddddddddd",
                "gas": 9223372036854754724,
                "gasCost": 3,
                "depth": 1,
            },
            {
                "pc": 4,
                "op": "ADD",
                "callerAddress": "0xcccccccccccccccccccccccccccccccccccccccc",
                "contractAddress": "0xdddddddddddddddddddddddddddddddddddddddd",
                "gas": 9223372036854754721,
                "gasCost": 3,
                "depth": 1,
            },
            {
                "pc": 5,
                "op": "STOP",
                "callerAddress": "0xcccccccccccccccccccccccccccccccccccccccc",
                "contractAddress": "0xdddddddddddddddddddddddddddddddddddddddd",
                "gas": 9223372036854754718,
                "gasCost": 0,
                "depth": 1,
            },
        ],
    }
    main_smart_contract_call = "0x6003600401"
    raw_response = base_request(
        "debug_traceCall",
        params=[
            {
                "from": "0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC",
                "to": "0xDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD",
                "data": main_smart_contract_call,
            },
            "latest",
            {
                "stateOverrides": {
                    "0xDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD": {
                        "balance": "0xDE0B6B3A7640000",
                        "nonce": "0x1",
                        "code": main_smart_contract_call,
                    }
                }
            },
        ],
        endpoint=debug_endpoints[0],
    )
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    calldata_gas_used = get_calldata_gas(main_smart_contract_call)
    simulated_gas_used = sum(log["gasCost"] for log in response["structLogs"])
    assert response["failed"] is False
    assert response["structLogs"]
    assert response["gas"] == DEFAULT_GAS + calldata_gas_used + simulated_gas_used


def test_debug_traceCall_state_override_different_simulated_call():
    """
    Tests `debug_traceCall` with `stateOverrides`, where the simulated contract execution
    differs from the original transaction calldata.

    **Test Overview:**
    - The transaction executes **one contract call (`0x6003600401`)**.
    - However, the state override **modifies the contract's deployed code** to use
      a **different bytecode (`0x6001600052600260205260406000f3`)**.
    - This allows verification of gas usage, execution behavior, and return values.

    **Execution Steps:**
    1. **Send a transaction** to call a smart contract (`main_smart_contract_call`).
    2. **Override the contract code** using `stateOverrides` with a different bytecode (`simulated_smart_contract_call`).
    3. **Trace execution logs (`structLogs`)** to verify the instruction sequence.
    4. **Compute gas usage**, including:
       - **Calldata gas cost** (`get_calldata_gas()`).
       - **Gas used during execution** (sum of `gasCost` values in `structLogs`).
    5. **Validate return values** to ensure correct contract execution.

    **Assertions:**
    - The transaction **must not fail** (`failed` should be `False`).
    - Execution logs (`structLogs`) **must be present**.
    - **Gas consumption must match expectations**:
      ```
      response["gas"] == DEFAULT_GAS + calldata_gas_used + simulated_gas_used
      ```
    - The **expected return value** must match:
      ```
      0000000000000000000000000000000000000000000000000000000000000001
      0000000000000000000000000000000000000000000000000000000000000002
      ```
    **Why This Test?**
    - Ensures `debug_traceCall` correctly applies `stateOverrides`.
    - Verifies that execution **follows the overridden contract code**.
    - Confirms that gas computation is accurate when execution differs from calldata.

    **Returns:**
    - None (raises assertion errors if test conditions are not met).
    """

    reference_response = {
        "gas": 21110,
        "failed": False,
        "returnValue": "0000000000000000000000000000000000000000000000000000000000000001"
        + "0000000000000000000000000000000000000000000000000000000000000002",
        "structLogs": [
            {
                "pc": 0,
                "op": "PUSH1",
                "callerAddress": "0xcccccccccccccccccccccccccccccccccccccccc",
                "contractAddress": "0xdddddddddddddddddddddddddddddddddddddddd",
                "gas": 9223372036854754727,
                "gasCost": 3,
                "depth": 1,
            },
            {
                "pc": 2,
                "op": "PUSH1",
                "callerAddress": "0xcccccccccccccccccccccccccccccccccccccccc",
                "contractAddress": "0xdddddddddddddddddddddddddddddddddddddddd",
                "gas": 9223372036854754724,
                "gasCost": 3,
                "depth": 1,
            },
            {
                "pc": 4,
                "op": "MSTORE",
                "callerAddress": "0xcccccccccccccccccccccccccccccccccccccccc",
                "contractAddress": "0xdddddddddddddddddddddddddddddddddddddddd",
                "gas": 9223372036854754721,
                "gasCost": 6,
                "depth": 1,
            },
            {
                "pc": 5,
                "op": "PUSH1",
                "callerAddress": "0xcccccccccccccccccccccccccccccccccccccccc",
                "contractAddress": "0xdddddddddddddddddddddddddddddddddddddddd",
                "gas": 9223372036854754715,
                "gasCost": 3,
                "depth": 1,
            },
            {
                "pc": 7,
                "op": "PUSH1",
                "callerAddress": "0xcccccccccccccccccccccccccccccccccccccccc",
                "contractAddress": "0xdddddddddddddddddddddddddddddddddddddddd",
                "gas": 9223372036854754712,
                "gasCost": 3,
                "depth": 1,
            },
            {
                "pc": 9,
                "op": "MSTORE",
                "callerAddress": "0xcccccccccccccccccccccccccccccccccccccccc",
                "contractAddress": "0xdddddddddddddddddddddddddddddddddddddddd",
                "gas": 9223372036854754709,
                "gasCost": 6,
                "depth": 1,
            },
            {
                "pc": 10,
                "op": "PUSH1",
                "callerAddress": "0xcccccccccccccccccccccccccccccccccccccccc",
                "contractAddress": "0xdddddddddddddddddddddddddddddddddddddddd",
                "gas": 9223372036854754703,
                "gasCost": 3,
                "depth": 1,
            },
            {
                "pc": 12,
                "op": "PUSH1",
                "callerAddress": "0xcccccccccccccccccccccccccccccccccccccccc",
                "contractAddress": "0xdddddddddddddddddddddddddddddddddddddddd",
                "gas": 9223372036854754700,
                "gasCost": 3,
                "depth": 1,
            },
            {
                "pc": 14,
                "op": "RETURN",
                "callerAddress": "0xcccccccccccccccccccccccccccccccccccccccc",
                "contractAddress": "0xdddddddddddddddddddddddddddddddddddddddd",
                "gas": 9223372036854754697,
                "gasCost": 0,
                "depth": 1,
            },
        ],
    }

    main_smart_contract_call = "0x6003600401"
    simulated_smart_contract_call = "0x6001600052600260205260406000f3"
    raw_response = base_request(
        "debug_traceCall",
        params=[
            {
                "from": "0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC",
                "to": "0xDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD",
                "data": main_smart_contract_call,
            },
            "latest",
            {
                "stateOverrides": {
                    "0xDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD": {
                        "balance": "0xDE0B6B3A7640000",
                        "nonce": "0x1",
                        "code": simulated_smart_contract_call,
                    }
                }
            },
        ],
        endpoint=debug_endpoints[0],
    )
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    # calldata price will remain the same
    calldata_gas_used = get_calldata_gas(main_smart_contract_call)
    simulated_gas_used = sum(log["gasCost"] for log in response["structLogs"])
    assert response["failed"] is False
    assert response["structLogs"]
    assert response["gas"] == DEFAULT_GAS + calldata_gas_used + simulated_gas_used
    assert (
        response["returnValue"]
        == "0000000000000000000000000000000000000000000000000000000000000001"
        + "0000000000000000000000000000000000000000000000000000000000000002"
    )


def test_debug_traceCall_block_and_state_override():
    """
    Test `debug_traceCall` with both block-level and state-level overrides.

    This test simulates a smart contract call while applying `blockOverrides` and `stateOverrides`
    to alter the block context and contract/account state. It verifies that the call executes
    correctly under these conditions and that the resulting gas usage and execution trace are accurate.

    **Test Purpose:**
    - Ensure that overridden block metadata (e.g., block number, difficulty) is respected.
    - Ensure that overridden account state (balance, nonce, code) is applied.
    - Confirm that the call does not fail, produces correct return data, and logs the expected opcodes.
    - Validate gas accounting under overridden conditions.

    **Execution Flow:**
    1. Define a minimal contract that returns `1` using inline bytecode.
    2. Override the state for both the caller and callee accounts:
       - Assign sufficient balance and nonce to the caller.
       - Inject runtime bytecode into the callee.
    3. Override block-level parameters, including:
       - `difficulty`, `gasLimit`, `number`, and `feeRecipient`.
    4. Perform a `debug_traceCall` and inspect:
       - Return value
       - Gas usage
       - Opcode trace (`structLogs`)
    5. Compute expected gas:
       - `DEFAULT_GAS + calldata_gas + sum(structLogs[].gasCost)`
    6. Validate that all assertions pass.

    **Block Overrides Used:**
    - `difficulty`: `0x1234`
    - `gasLimit`: `0xF4240`
    - `number`: `0x1`
    - `feeRecipient`: `0xBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB`

    **State Overrides Used:**
    - Contract: `0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF`
      - `balance`: `0x8AC7230489E80000` (10 ONE)
      - `nonce`: `0x2`
      - `code`: Minimal contract returning `1`
    - Caller: `0xEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE`
      - `balance`: `0x8AC7230489E80000`
      - `nonce`: `0x2`

    **Assertions:**
    - The call does not fail (`failed` is `False`).
    - Opcode trace (`structLogs`) is present and valid.
    - Final gas usage is consistent with expectations:
      ```
      gas == DEFAULT_GAS + calldata_gas + execution_gas
      ```
    - Return value equals:
      ```
      0000000000000000000000000000000000000000000000000000000000000001
      ```

    **Why This Test?**
    - To confirm that block context (e.g., block number, fee recipient) affects execution.
    - To validate that contract bytecode and account state can be overridden dynamically.
    - To ensure gas accounting remains accurate with simultaneous overrides.

    **Returns:**
    - None. Raises `AssertionError` if any condition fails.
    """

    reference_response = {
        "gas": 21154,
        "failed": False,
        "returnValue": "0000000000000000000000000000000000000000000000000000000000000001",
        "structLogs": [
            {
                "pc": 0,
                "op": "PUSH1",
                "callerAddress": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
                "contractAddress": "0xffffffffffffffffffffffffffffffffffffffff",
                "gas": 999978864,
                "gasCost": 3,
                "depth": 1,
            },
            {
                "pc": 2,
                "op": "PUSH1",
                "callerAddress": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
                "contractAddress": "0xffffffffffffffffffffffffffffffffffffffff",
                "gas": 999978861,
                "gasCost": 3,
                "depth": 1,
            },
            {
                "pc": 4,
                "op": "MSTORE",
                "callerAddress": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
                "contractAddress": "0xffffffffffffffffffffffffffffffffffffffff",
                "gas": 999978858,
                "gasCost": 6,
                "depth": 1,
            },
            {
                "pc": 5,
                "op": "PUSH1",
                "callerAddress": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
                "contractAddress": "0xffffffffffffffffffffffffffffffffffffffff",
                "gas": 999978852,
                "gasCost": 3,
                "depth": 1,
            },
            {
                "pc": 7,
                "op": "PUSH1",
                "callerAddress": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
                "contractAddress": "0xffffffffffffffffffffffffffffffffffffffff",
                "gas": 999978849,
                "gasCost": 3,
                "depth": 1,
            },
            {
                "pc": 9,
                "op": "RETURN",
                "callerAddress": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
                "contractAddress": "0xffffffffffffffffffffffffffffffffffffffff",
                "gas": 999978846,
                "gasCost": 0,
                "depth": 1,
            },
        ],
    }
    main_smart_contract_call = "0x600160005260206000f3"
    initial_gas = "0x3B9ACA00"
    raw_response = base_request(
        "debug_traceCall",
        params=[
            {
                "from": "0xEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE",
                "to": "0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF",
                "data": main_smart_contract_call,
                "gas": initial_gas,
                "gasPrice": "0x174876",
            },
            "0x1",
            {
                "blockOverrides": {
                    "difficulty": "0x1234",
                    "gasLimit": "0xF4240",
                    "number": "0x1",
                    "feeRecipient": "0xBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
                },
                "stateOverrides": {
                    "0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF": {
                        "balance": "0x8AC7230489E80000",
                        "nonce": "0x2",
                        "code": main_smart_contract_call,
                    },
                    "0xEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE": {
                        "balance": "0x8AC7230489E80000",
                        "nonce": "0x2",
                    },
                },
            },
        ],
        endpoint=debug_endpoints[0],
    )
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    calldata_gas_used = get_calldata_gas(main_smart_contract_call)
    simulated_gas_used = sum(log["gasCost"] for log in response["structLogs"])
    final_gas = response["structLogs"][-1]["gas"]
    assert response["gas"] + final_gas == int(initial_gas, 16)
    assert response["failed"] is False
    assert response["structLogs"]
    assert response["gas"] == DEFAULT_GAS + calldata_gas_used + simulated_gas_used
    assert (
        response["returnValue"]
        == "0000000000000000000000000000000000000000000000000000000000000001"
    )


def test_debug_traceCall_override_faulty_from():
    """
    Tests `debug_traceCall` with an **invalid `from` address format** in the request.

    **Test Overview:**
    - This test intentionally provides a **malformed `from` address** (`"aaaaa"`)
      instead of a proper Ethereum address (`0x...` prefixed 20-byte hex string).
    - The RPC call should **fail with an error** because the Ethereum client expects
      `from` to be a valid hex-encoded address.

    **Expected Behavior:**
    - The Ethereum node should return a **JSON-RPC error**:
      ```
      {
        "code": -32602,
        "message": "invalid argument 0: json: cannot unmarshal hex string
                    without 0x prefix into Go struct field CallArgs.from
                    of type common.Address"
      }
      ```
    - The test verifies that this error response **matches the expected error message**.

    **Assertions:**
    - The response must contain **error code `-32602`** (Invalid argument error).
    - The error message must **match exactly**, confirming the issue is due to
      the incorrect `from` field format.

    **Why This Test?**
    - Ensures that `debug_traceCall` properly validates Ethereum addresses.
    - Prevents potential execution with malformed inputs.
    - Helps verify that RPC responses follow expected error handling.

    **Returns:**
    - None (raises assertion errors if test conditions are not met).
    """

    reference_response = {
        "code": -32602,
        "message": "invalid argument 0: json: cannot unmarshal hex string without 0x prefix into Go struct field CallArgs.from of type common.Address",
    }

    main_smart_contract_call = "0x6001600101"
    raw_response = base_request(
        "debug_traceCall",
        params=[
            {
                "from": "aaaaa",
                "to": "0xBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
                "data": main_smart_contract_call,
            },
            "latest",
            {
                "blockOverrides": {
                    "gasLimit": "0xF424000",
                    "timestamp": "0x5F5E100",
                    "number": "0x10",
                    "feeRecipient": "0xBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
                }
            },
        ],
        endpoint=debug_endpoints[0],
    )
    response = check_and_unpack_rpc_response(raw_response, expect_error=True)
    assert reference_response["code"] == response["code"], (
        f"Expected error code {reference_response['code']}, " f"got {response['code']}"
    )
    assert reference_response["message"] == response["message"], (
        f"Expected error code {reference_response['message']}, "
        f"got {response['message']}"
    )


def test_debug_traceCall_override_faulty_to():
    """
    Tests `debug_traceCall` with an **invalid `to` address format** in the request.

    **Test Overview:**
    - This test provides a **malformed `to` address** (`"aaaa"`) instead of a
      valid Ethereum address (`0x...` prefixed 20-byte hex string).
    - The RPC call should **fail with an error** because the Ethereum client
      requires `to` to be a valid hex-encoded address.

    **Expected Behavior:**
    - The Ethereum node should return a **JSON-RPC error**:
      ```
      {
        "code": -32602,
        "message": "invalid argument 0: json: cannot unmarshal hex string
                    without 0x prefix into Go struct field CallArgs.to
                    of type common.Address"
      }
      ```
    - The test verifies that this error response **matches the expected error message**.

    **Assertions:**
    - The response must contain **error code `-32602`** (Invalid argument error).
    - The error message must **match exactly**, confirming that the issue is
      due to the incorrect `to` field format.

    **Why This Test?**
    - Ensures that `debug_traceCall` properly validates Ethereum addresses.
    - Prevents execution with malformed inputs that could cause unexpected behavior.
    - Helps verify that RPC responses follow expected error handling.

    **Returns:**
    - None (raises assertion errors if test conditions are not met).
    """

    reference_response = {
        "code": -32602,
        "message": "invalid argument 0: json: cannot unmarshal hex string without 0x prefix into Go struct field CallArgs.to of type common.Address",
    }

    main_smart_contract_call = "0x6001600101"
    raw_response = base_request(
        "debug_traceCall",
        params=[
            {
                "from": "0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                "to": "aaaa",
                "data": main_smart_contract_call,
            },
            "latest",
            {
                "blockOverrides": {
                    "gasLimit": "0xF424000",
                    "timestamp": "0x5F5E100",
                    "number": "0x10",
                    "feeRecipient": "0xBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
                }
            },
        ],
        endpoint=debug_endpoints[0],
    )
    response = check_and_unpack_rpc_response(raw_response, expect_error=True)
    assert reference_response["code"] == response["code"], (
        f"Expected error code {reference_response['code']}, " f"got {response['code']}"
    )
    assert reference_response["message"] == response["message"], (
        f"Expected error code {reference_response['message']}, "
        f"got {response['message']}"
    )


def test_debug_traceCall_override_faulty_block_num():
    """
    Tests `debug_traceCall` with an **invalid block number format** in the request.

    **Test Overview:**
    - This test provides a **malformed block number** (`"aaaa"`) instead of a
      valid hexadecimal string prefixed with `0x`.
    - The RPC call should **fail with an error** because Ethereum clients expect
      block identifiers to be in valid hex format (`"0x..."`) or specific keywords
      like `"latest"`, `"earliest"`, or `"pending"`.

    **Expected Behavior:**
    - The Ethereum node should return a **JSON-RPC error**:
      ```
      {
        "code": -32602,
        "message": "invalid argument 1: hex string without 0x prefix"
      }
      ```
    - The test verifies that this error response **matches the expected error message**.

    **Assertions:**
    - The response must contain **error code `-32602`** (Invalid argument error).
    - The error message must **match exactly**, confirming that the issue is
      due to the incorrect block number format.

    **Why This Test?**
    - Ensures that `debug_traceCall` properly validates block number inputs.
    - Prevents execution with malformed inputs that could cause unexpected behavior.
    - Helps verify that RPC responses follow expected error handling.

    **Returns:**
    - None (raises assertion errors if test conditions are not met).
    """

    reference_response = {
        "code": -32602,
        "message": "invalid argument 1: hex string without 0x prefix",
    }

    main_smart_contract_call = "0x6001600101"
    raw_response = base_request(
        "debug_traceCall",
        params=[
            {
                "from": "0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                "to": "0xBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
                "data": main_smart_contract_call,
            },
            "aaaa",
            {
                "blockOverrides": {
                    "gasLimit": "0xF424000",
                    "timestamp": "0x5F5E100",
                    "number": "0x10",
                    "feeRecipient": "0xBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
                }
            },
        ],
        endpoint=debug_endpoints[0],
    )
    response = check_and_unpack_rpc_response(raw_response, expect_error=True)
    assert reference_response["code"] == response["code"], (
        f"Expected error code {reference_response['code']}, " f"got {response['code']}"
    )
    assert reference_response["message"] == response["message"], (
        f"Expected error code {reference_response['message']}, "
        f"got {response['message']}"
    )


def test_debug_traceCall_override_faulty_data():
    """
    Tests `debug_traceCall` with an **invalid `data` field format** in the request.

    **Test Overview:**
    - This test provides a **malformed `data` field** (`"something_special"`) instead of a
      valid hexadecimal string prefixed with `0x`.
    - The Ethereum client expects `data` to be **a valid hex-encoded byte string** (EVM bytecode or calldata).
    - The RPC call should **fail with an error** due to the incorrect data format.

    **Expected Behavior:**
    - The Ethereum node should return a **JSON-RPC error**:
      ```
      {
        "code": -32602,
        "message": "invalid argument 0: json: cannot unmarshal hex string
                    without 0x prefix into Go struct field CallArgs.data
                    of type hexutil.Bytes"
      }
      ```
    - The test verifies that this error response **matches the expected error message**.

    **Assertions:**
    - The response must contain **error code `-32602`** (Invalid argument error).
    - The error message must **match exactly**, confirming that the issue is
      due to the incorrect `data` field format.

    **Why This Test?**
    - Ensures that `debug_traceCall` properly validates transaction `data` inputs.
    - Prevents execution with malformed calldata, which could lead to unexpected behavior.
    - Helps verify that RPC responses follow expected error handling.

    **Returns:**
    - None (raises assertion errors if test conditions are not met).
    """

    reference_response = {
        "code": -32602,
        "message": "invalid argument 0: json: cannot unmarshal hex string without 0x prefix into Go struct field CallArgs.data of type hexutil.Bytes",
    }

    main_smart_contract_call = "something_special"
    raw_response = base_request(
        "debug_traceCall",
        params=[
            {
                "from": "0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                "to": "0xBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
                "data": main_smart_contract_call,
            },
            "latest",
            {
                "blockOverrides": {
                    "gasLimit": "0xF424000",
                    "timestamp": "0x5F5E100",
                    "number": "0x10",
                    "feeRecipient": "0xBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
                }
            },
        ],
        endpoint=debug_endpoints[0],
    )
    response = check_and_unpack_rpc_response(raw_response, expect_error=True)
    assert reference_response["code"] == response["code"], (
        f"Expected error code {reference_response['code']}, " f"got {response['code']}"
    )
    assert reference_response["message"] == response["message"], (
        f"Expected error code {reference_response['message']}, "
        f"got {response['message']}"
    )


def test_debug_traceCall_override_faulty_override():
    """
    Tests `debug_traceCall` with an **unrecognized override field** in the request.

    **Test Overview:**
    - This test provides an **invalid override field (`someStrangeField`)** instead of
      valid fields like `blockOverrides` or `stateOverrides`.
    - The Harmony node **ignores unknown fields** rather than rejecting them.
    - The transaction proceeds **as if no overrides were provided**.

    **Expected Behavior:**
    - The node **ignores the unexpected `someStrangeField`** and executes normally.
    - The transaction **must succeed** (`failed` should be `False`).
    - The execution trace (`structLogs`) **must be empty**, as the contract execution
      does not involve significant operations.
    - The gas usage **must match the expected base cost**, considering calldata.

    **Assertions:**
    - The transaction **must not fail** (`failed` should be `False`).
    - Execution logs (`structLogs`) **must be empty**.
    - The gas consumption must **match expectations**:
      ```
      response["gas"] == DEFAULT_GAS + calldata_gas_used
      ```
    - The response structure must **match the expected format**.

    **Why This Test?**
    - Confirms that `debug_traceCall` **ignores unknown override fields** instead of failing.
    - Ensures that unexpected parameters do **not affect transaction execution**.
    - Helps verify that only recognized override fields (`blockOverrides`, `stateOverrides`)
      impact execution behavior.

    **Returns:**
    - None (raises assertion errors if test conditions are not met).
    """

    reference_response = {
        "gas": 21080,
        "failed": False,
        "returnValue": "",
        "structLogs": [],
    }

    main_smart_contract_call = "0x6001600101"
    raw_response = base_request(
        "debug_traceCall",
        params=[
            {
                "from": "0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                "to": "0xBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
                "data": main_smart_contract_call,
            },
            "latest",
            {
                "someStrangeField": {
                    "gasLimit": "0xF424000",
                    "timestamp": "0x5F5E100",
                    "number": "0x10",
                    "feeRecipient": "0xBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
                }
            },
        ],
        endpoint=debug_endpoints[0],
    )
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    assert_valid_json_structure(reference_response, response)
    calldata_gas_used = get_calldata_gas(main_smart_contract_call)
    assert response["failed"] is False
    assert not response["structLogs"]
    assert response["gas"] == DEFAULT_GAS + calldata_gas_used


def test_debug_traceCall_override_sending_one_to_other_address():
    """
    Test `debug_traceCall` with state overrides simulating a simple ONE transfer.

    This test simulates sending 1 ONE from one account to another using `debug_traceCall`,
    with state overrides that assign sufficient balance to the sender and a zero balance
    to the recipient. It expects the transaction to succeed with no gas used, since the
    recipient is an EOA and no contract code is executed.

    Steps:
    - Define the expected reference response from the trace.
    - Create the ONE transfer request with a value of 1 ONE (in wei).
    - Override sender and receiver balances to control state.
    - Use `callTracer` to simulate the execution trace.
    - Validate that the result matches the expected structure and values.

    Assertions:
    - The trace result matches the expected reference structure.
    - The value transferred is exactly 1 ONE.
    - Gas used is 0, indicating no contract execution occurred.
    """
    reference_response = {
        "type": "CALL",
        "from": "0xaaaaaa0000000000000000000000000000000000",
        "to": "0xdddddddddddddddddddddddddddddddddddddddd",
        "value": "0xde0b6b3a7640000",
        "gas": "0x0",
        "gasUsed": "0x0",
        "input": "0x",
        "output": "0x",
        "time": "10.911µs",
    }

    one_to_send = "0xde0b6b3a7640000"
    raw_response = base_request(
        "debug_traceCall",
        params=[
            {
                "from": "0xaaaaaa0000000000000000000000000000000000",
                "to": "0xdddddddddddddddddddddddddddddddddddddddd",
                "value": one_to_send,
                "gas": "0x5208",
                "gasPrice": "0x174876e800",
            },
            "latest",
            {
                "stateOverrides": {
                    "0xaaaaaa0000000000000000000000000000000000": {
                        "balance": "0x1000000000000000000"
                    },
                    "0xdddddddddddddddddddddddddddddddddddddddd": {"balance": "0x0"},
                },
                "tracer": "callTracer",
                "timeout": "5s",
            },
        ],
        endpoint=debug_endpoints[0],
    )
    response = check_and_unpack_rpc_response(raw_response, expect_error=False)
    print(response)
    assert_valid_json_structure(reference_response, response)
    assert response["value"] == one_to_send
    assert response["gas"] == "0x0"
    assert response["gasUsed"] == "0x0"

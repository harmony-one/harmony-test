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
    Tests `debug_traceCall` with both **block-level** and **state-level** overrides.

    **Test Overview:**
    - This test executes a smart contract call while modifying both **block parameters**
      and the **contract’s state** using `blockOverrides` and `stateOverrides`.
    - It validates that gas consumption, execution logs, and return values behave as expected.

    **Execution Steps:**
    1. **Send a transaction** calling a smart contract (`main_smart_contract_call`).
    2. **Override block parameters (`blockOverrides`)**, modifying:
       - `difficulty`
       - `gasLimit`
       - `block number`
       - `fee recipient`
    3. **Override the contract state (`stateOverrides`)**, modifying:
       - `balance`
       - `nonce`
       - `code` (overriding contract bytecode)
    4. **Trace execution logs (`structLogs`)** to validate the opcode sequence.
    5. **Compute gas usage**, including:
       - **Calldata gas cost** (`get_calldata_gas()`).
       - **Gas used during execution** (sum of `gasCost` in `structLogs`).
    6. **Validate the return value** to ensure the overridden contract executes correctly.

    **Block Overrides:**
    - `difficulty`: `0x1234`
    - `gasLimit`: `0xF4240`
    - `number`: `0x1`
    - `feeRecipient`: `0xBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB`

    **State Overrides:**
    - Contract address: `0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF`
    - `balance`: `0x8AC7230489E80000`
    - `nonce`: `0x2`
    - `code`: Uses `main_smart_contract_call` as the overridden contract code.

    **Assertions:**
    - The transaction **must not fail** (`failed` should be `False`).
    - Execution logs (`structLogs`) **must be present**.
    - **Gas consumption must match expected calculations**:
      ```
      response["gas"] == DEFAULT_GAS + calldata_gas_used + simulated_gas_used
      ```
    - The **expected return value** must be:
      ```
      0000000000000000000000000000000000000000000000000000000000000001
      ```

    **Why This Test?**
    - Ensures that **block overrides modify transaction execution correctly**.
    - Verifies that **contract state can be overridden properly** using `stateOverrides`.
    - Confirms that gas calculations remain accurate under combined overrides.

    **Returns:**
    - None (raises assertion errors if test conditions are not met).
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
                "gas": 9223372036854754671,
                "gasCost": 3,
                "depth": 1,
            },
            {
                "pc": 2,
                "op": "PUSH1",
                "callerAddress": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
                "contractAddress": "0xffffffffffffffffffffffffffffffffffffffff",
                "gas": 9223372036854754668,
                "gasCost": 3,
                "depth": 1,
            },
            {
                "pc": 4,
                "op": "MSTORE",
                "callerAddress": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
                "contractAddress": "0xffffffffffffffffffffffffffffffffffffffff",
                "gas": 9223372036854754665,
                "gasCost": 6,
                "depth": 1,
            },
            {
                "pc": 5,
                "op": "PUSH1",
                "callerAddress": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
                "contractAddress": "0xffffffffffffffffffffffffffffffffffffffff",
                "gas": 9223372036854754659,
                "gasCost": 3,
                "depth": 1,
            },
            {
                "pc": 7,
                "op": "PUSH1",
                "callerAddress": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
                "contractAddress": "0xffffffffffffffffffffffffffffffffffffffff",
                "gas": 9223372036854754656,
                "gasCost": 3,
                "depth": 1,
            },
            {
                "pc": 9,
                "op": "RETURN",
                "callerAddress": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
                "contractAddress": "0xffffffffffffffffffffffffffffffffffffffff",
                "gas": 9223372036854754653,
                "gasCost": 0,
                "depth": 1,
            },
        ],
    }
    main_smart_contract_call = "0x600160005260206000f3"
    raw_response = base_request(
        "debug_traceCall",
        params=[
            {
                "from": "0xEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE",
                "to": "0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF",
                "data": main_smart_contract_call,
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
                    }
                },
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
    assert (
        response["returnValue"]
        == "0000000000000000000000000000000000000000000000000000000000000001"
    )

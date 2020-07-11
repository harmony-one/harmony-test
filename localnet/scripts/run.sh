#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
harmony_dir="$(go env GOPATH)/src/github.com/harmony-one/harmony"
localnet_config=$(realpath "$DIR/../configs/localnet_deploy.config")

function kill_localnet(){
  pushd "$(pwd)"
  cd "$harmony_dir" && bash ./test/kill_node.sh
  popd
}

function setup() {
  if [ ! -d "$harmony_dir" ]; then
    echo "Test setup FAILED: Missing harmony directory at $harmony_dir"
    exit 1
  fi
  if [ ! -f "$localnet_config" ]; then
    echo "Test setup FAILED: Missing localnet deploy config at $localnet_config"
    exit 1
  fi
  kill_localnet
}

function build_and_start_localnet() {
  local localnet_log="$harmony_dir/localnet_deploy.log"
  rm -rf "$harmony_dir/tmp_log*"
  rm -f "$localnet_log"
  rm -f "$harmony_dir/*.rlp"
  pushd "$(pwd)"
  cd "$harmony_dir"
  if [ "$BUILD" == "true" ]; then
    # Dynamic for faster build iterations
    bash ./scripts/go_executable_build.sh -S
  fi
  bash ./test/deploy.sh -B -D 60000 "$localnet_config"  2>&1 | tee "$localnet_log"
  popd
}

function wait_for_localnet_boot() {
  timeout=70
  if [ -n "$1" ]; then
    timeout=$1
  fi
  i=0
  until curl --silent --location --request POST "localhost:9500" \
    --header "Content-Type: application/json" \
    --data '{"jsonrpc":"2.0","method":"net_version","params":[],"id":1}' >/dev/null; do
    echo "Trying to connect to localnet..."
    if ((i > timeout )); then
      echo "TIMEOUT REACHED"
      exit 1
    fi
    sleep 3
    i=$((i + 1))
  done

  valid=false
  until $valid; do
    result=$(curl --silent --location --request POST "localhost:9500" \
      --header "Content-Type: application/json" \
      --data '{"jsonrpc":"2.0","method":"hmy_blockNumber","params":[],"id":1}' | jq '.result')
    if [ "$result" = "\"0x0\"" ]; then
      echo "Waiting for localnet to boot..."
      if ((i > timeout )); then
        echo "TIMEOUT REACHED"
        exit 1
      fi
      sleep 3
      i=$((i + 1))
    else
      valid=true
    fi
  done

  echo "Localnet booted."
}

trap kill_localnet SIGINT SIGTERM EXIT

BUILD=true
while getopts "B" option; do
  case ${option} in
  B) BUILD=false;;
  *) echo "
Integration tester for localnet

Option:      Help:
-B           Do NOT build binray before testing
"
  esac
done


setup
build_and_start_localnet || exit 1 &
sleep 30
wait_for_localnet_boot 100

echo -e "== \e[38;5;0;48;5;255mSTARTING TESTS\e[0m =="
cd "$DIR/../" && python3 -u -m py.test -r s -s tests
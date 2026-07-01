ARG MAIN_REPO_BRANCH=dev
ARG MAIN_REPO_ORG=harmony-one
ARG HMY_VERSION=v2026.0.0

FROM golang:1.24.2

ARG MAIN_REPO_BRANCH
ARG MAIN_REPO_ORG
ARG HMY_VERSION

ENV BRANCH=${MAIN_REPO_BRANCH}
ENV MAIN_REPO=${MAIN_REPO_ORG}
ENV HMY_VERSION=${HMY_VERSION}

WORKDIR "$GOPATH/src/github.com/harmony-one"

SHELL ["/bin/bash", "-c"]

ENV DEBIAN_FRONTEND=noninteractive

# hadolint ignore=DL3008
RUN apt-get clean > /dev/null 2>&1 && \
    echo "Running apt-get update" && \
    apt-get update > /dev/null 2>&1 && \
    echo "Installing bash" && apt-get install -y --no-install-recommends bash > /dev/null 2>&1 && \
    echo "Installing curl" && apt-get install -y --no-install-recommends curl > /dev/null 2>&1 && \
    echo "Installing git" && apt-get install -y --no-install-recommends git > /dev/null 2>&1 && \
    echo "Installing jq" && apt-get install -y --no-install-recommends jq > /dev/null 2>&1 && \
    echo "Installing make" && apt-get install -y --no-install-recommends make > /dev/null 2>&1 && \
    echo "Installing python3" && apt-get install -y --no-install-recommends python3 > /dev/null 2>&1 && \
    echo "Installing python3-pip" && apt-get install -y --no-install-recommends python3-pip > /dev/null 2>&1 && \
    echo "Installing unzip" && apt-get install -y --no-install-recommends unzip > /dev/null 2>&1 && \
    echo "Cleaning up" && \
    apt-get clean > /dev/null 2>&1 && \
    rm -rf /var/lib/apt/lists/*

# The Harmony repo is mounted at runtime from CI:
# /go/src/github.com/harmony-one/harmony
# Fix complaints about Docker / root / user ownership for Golang "VCS stamping"
# https://github.com/golang/go/blob/3900ba4baf0e3b309a55b5ac4dd25f709df09772/src/cmd/go/internal/vcs/vcs.go
RUN git clone --depth=1 --single-branch https://github.com/harmony-one/pyhmy.git > /dev/null 2>&1 && \
    git config --global --add safe.directory "$GOPATH/src/github.com/harmony-one/harmony" > /dev/null 2>&1 && \
    git config --global --add safe.directory "$GOPATH/src/github.com/harmony-one/pyhmy" > /dev/null 2>&1

WORKDIR "$GOPATH/src/github.com/coinbase/mesh-cli"

# dpkg is only a Debian way to get the architecture, change it if you swich to alpine
RUN set -euo pipefail && \
    case "$(dpkg --print-architecture)" in \
      amd64) HMY_ASSET="hmy-amd64" ;; \
      arm64) HMY_ASSET="hmy-arm64" ;; \
      *) echo "Unsupported architecture: ${TARGETARCH:-$(dpkg --print-architecture)}" >&2; exit 1 ;; \
    esac && \
    curl -fsSL \
      -o /go/bin/hmy \
      "https://github.com/harmony-one/go-sdk/releases/download/${HMY_VERSION}/${HMY_ASSET}" && \
    chmod +x /go/bin/hmy && \
    git clone --depth=1 --single-branch https://github.com/coinbase/mesh-cli.git . > /dev/null 2>&1 && \
    make install > /dev/null 2>&1

WORKDIR "$GOPATH/src/github.com/harmony-one/harmony-test/localnet"

COPY scripts/ scripts/
COPY rpc_tests/ rpc_tests/
COPY configs/ configs/
COPY requirements.txt requirements.txt

RUN python3 -m pip install -r requirements.txt --break-system-packages --no-cache-dir > /dev/null 2>&1 && \
    rm requirements.txt && \
    chmod +x "scripts/run.sh"

WORKDIR "$GOPATH/src/github.com/harmony-one/pyhmy"

RUN python3 -m pip install . --break-system-packages --no-cache-dir > /dev/null 2>&1

WORKDIR "$GOPATH/src/github.com/harmony-one/harmony"

ENTRYPOINT ["/go/src/github.com/harmony-one/harmony-test/localnet/scripts/run.sh"]

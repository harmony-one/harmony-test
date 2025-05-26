ARG MAIN_REPO_BRANCH=dev
ARG MAIN_REPO_ORG=harmony-one

FROM golang:1.24.2

ARG MAIN_REPO_BRANCH
ARG MAIN_REPO_ORG

ENV BRANCH=${MAIN_REPO_BRANCH}
ENV MAIN_REPO=${MAIN_REPO_ORG}

WORKDIR "$GOPATH/src/github.com/harmony-one"

SHELL ["/bin/bash", "-c"]

ENV DEBIAN_FRONTEND=noninteractive

# NOTE: This instruction is needed to understand which version user
#   by the apt package
# RUN apt-cache policy your_package

# NOTE: we are not using the pinned versions here, because this is just testing
#   image in the  CI, not  a production one, it will be easier to debug
#   problematic package one version than constantly update dependencies
#   Reference: https://github.com/harmony-one/harmony-test/issues/45
# hadolint ignore=DL3008
RUN apt-get clean > /dev/null 2>&1 && \
    echo "Running apt-get update" && \
    apt-get update > /dev/null 2>&1 && \
    echo "Running apt-get upgrade" && \
    apt-get upgrade -y > /dev/null 2>&1 && \
    echo "Installing bash" && apt-get install -y --no-install-recommends bash > /dev/null 2>&1 && \
    echo "Installing curl" && apt-get install -y --no-install-recommends curl > /dev/null 2>&1 && \
    echo "Installing g++" && apt-get install -y --no-install-recommends g++ > /dev/null 2>&1 && \
    echo "Installing gcc" && apt-get install -y --no-install-recommends gcc > /dev/null 2>&1 && \
    echo "Installing git" && apt-get install -y --no-install-recommends git > /dev/null 2>&1 && \
    echo "Installing jq" && apt-get install -y --no-install-recommends jq > /dev/null 2>&1 && \
    echo "Installing libgmp-dev" && apt-get install -y --no-install-recommends libgmp-dev > /dev/null 2>&1 && \
    echo "Installing libssl-dev" && apt-get install -y --no-install-recommends libssl-dev > /dev/null 2>&1 && \
    echo "Installing make" && apt-get install -y --no-install-recommends make > /dev/null 2>&1 && \
    echo "Installing python3" && apt-get install -y --no-install-recommends python3 > /dev/null 2>&1 && \
    echo "Installing python3-pip" && apt-get install -y --no-install-recommends python3-pip > /dev/null 2>&1 && \
    echo "Installing sudo" && apt-get install -y --no-install-recommends sudo > /dev/null 2>&1 && \
    echo "Installing unzip" && apt-get install -y --no-install-recommends unzip > /dev/null 2>&1 && \
    echo "Cleaning up" && \
    apt-get clean > /dev/null 2>&1 && \
    rm -rf /var/lib/apt/lists/*

# Fix complaints about Docker / root / user ownership for Golang "VCS stamping"
# https://github.com/golang/go/blob/3900ba4baf0e3b309a55b5ac4dd25f709df09772/src/cmd/go/internal/vcs/vcs.go
RUN git clone --branch ${BRANCH} https://github.com/${MAIN_REPO}/harmony.git > /dev/null 2>&1 && \
    git clone https://github.com/harmony-one/bls.git > /dev/null 2>&1 && \
    git clone https://github.com/harmony-one/mcl.git > /dev/null 2>&1 && \
    git clone https://github.com/harmony-one/pyhmy.git > /dev/null 2>&1 && \
    git config --global --add safe.directory "$GOPATH/src/github.com/harmony-one/harmony" > /dev/null 2>&1 && \
    git config --global --add safe.directory "$GOPATH/src/github.com/harmony-one/bls" > /dev/null 2>&1 && \
    git config --global --add safe.directory "$GOPATH/src/github.com/harmony-one/mcl" > /dev/null 2>&1 && \
    git config --global --add safe.directory "$GOPATH/src/github.com/harmony-one/pyhmy" > /dev/null 2>&1

WORKDIR "$GOPATH/src/github.com/harmony-one/harmony"
# Build to fetch all dependencies for faster test builds
RUN go mod tidy > /dev/null 2>&1 && \
    bash scripts/install_build_tools.sh > /dev/null 2>&1 && \
    make > /dev/null 2>&1
WORKDIR "$GOPATH/src/github.com/coinbase/mesh-cli"
RUN rm -rf "$GOPATH/src/github.com/harmony-one/harmony"

# Install testing tools
RUN curl -L -o /go/bin/hmy https://harmony.one/hmycli > /dev/null 2>&1 && \
    chmod +x /go/bin/hmy > /dev/null 2>&1

RUN git clone https://github.com/coinbase/mesh-cli.git . > /dev/null 2>&1 && \
    make install > /dev/null 2>&1

WORKDIR "$GOPATH/src/github.com/harmony-one/harmony-test/localnet"

COPY scripts/ scripts/
COPY rpc_tests/ rpc_tests/
COPY configs/ configs/
COPY requirements.txt requirements.txt

# Since we are running as root in Docker, `--break-system-packages` is required
RUN python3 -m pip install -r requirements.txt --break-system-packages --no-cache-dir > /dev/null 2>&1 && \
    rm requirements.txt && \
    chmod +x "scripts/run.sh"
WORKDIR $GOPATH/src/github.com/harmony-one/pyhmy
RUN python3 -m pip install . --break-system-packages --no-cache-dir > /dev/null 2>&1

WORKDIR $GOPATH/src/github.com/harmony-one/harmony
ENTRYPOINT ["/go/src/github.com/harmony-one/harmony-test/localnet/scripts/run.sh"]

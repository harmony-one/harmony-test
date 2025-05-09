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

RUN apt-get clean > /dev/null 2>&1 && \
    apt-get update > /dev/null 2>&1 && \
    apt-get upgrade -y > /dev/null 2>&1 && \
    apt-get install -y --no-install-recommends \
        bash=5.2.15-2+b7 \
        curl=7.88.1-10+deb12u12 \
        g++=4:12.2.0-3 \
        gcc=4:12.2.0-3 \
        git=1:2.39.5-0+deb12u2 \
        jq=1.6-2.1 \
        libgmp-dev=2:6.2.1+dfsg1-1.1 \
        libssl-dev=3.0.15-1~deb12u1 \
        make=4.3-4.1 \
        python3=3.11.2-1+b1 \
        python3-pip=23.0.1+dfsg-1 \
        sudo=1.9.13p3-1+deb12u1 \
        unzip=6.0-28 > /dev/null 2>&1 && \
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

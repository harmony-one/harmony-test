FROM golang:1.19

WORKDIR $GOPATH/src/github.com/harmony-one

SHELL ["/bin/bash", "-c"]

# These are split into multiple lines to allow debugging the error message that I cannot reproduce locally
# The command `xxx` returned a non-zero code: 100
RUN apt clean > /dev/null 2>1
RUN apt update > /dev/null 2>1
RUN apt upgrade -y > /dev/null 2>1
RUN apt update -y > /dev/null 2>1
RUN apt install -y unzip libgmp-dev libssl-dev curl git jq make gcc g++ bash sudo python3 python3-pip > /dev/null 2>1

RUN git clone https://github.com/harmony-one/harmony.git > /dev/null 2>1 \
    && git clone https://github.com/harmony-one/bls.git > /dev/null 2>1 \
    && git clone https://github.com/harmony-one/mcl.git > /dev/null 2>1

# Fix complaints about Docker / root / user ownership for Golang "VCS stamping"
# https://github.com/golang/go/blob/3900ba4baf0e3b309a55b5ac4dd25f709df09772/src/cmd/go/internal/vcs/vcs.go
RUN git config --global --add safe.directory $GOPATH/src/github.com/harmony-one/harmony > /dev/null 2>1 \
    && git config --global --add safe.directory $GOPATH/src/github.com/harmony-one/bls > /dev/null 2>1 \
    && git config --global --add safe.directory $GOPATH/src/github.com/harmony-one/mcl > /dev/null 2>1

# Build to fetch all dependencies for faster test builds
RUN cd harmony > /dev/null 2>1 && go mod tidy > /dev/null 2>1 && go get github.com/pborman/uuid > /dev/null 2>1 && go get github.com/rjeczalik/notify > /dev/null 2>1 \
    && go get github.com/cespare/cp > /dev/null 2>1 && go get github.com/libp2p/go-libp2p-crypto > /dev/null 2>1 && go get github.com/kr/pretty > /dev/null 2>1 \
    && go get github.com/kr/text > /dev/null 2>1 && go get gopkg.in/check.v1 > /dev/null 2>1 && bash scripts/install_build_tools.sh > /dev/null 2>1 && make > /dev/null 2>1
RUN rm -rf harmony

# Install testing tools
RUN curl -L -o /go/bin/hmy https://harmony.one/hmycli > /dev/null 2>1 && chmod +x /go/bin/hmy > /dev/null 2>1

WORKDIR $GOPATH/src/github.com/coinbase

RUN git clone https://github.com/coinbase/rosetta-cli.git > /dev/null 2>1
RUN cd rosetta-cli && make install > /dev/null 2>1

WORKDIR $GOPATH/src/github.com/harmony-one/harmony-test/localnet

COPY scripts scripts
COPY rpc_tests rpc_tests
COPY configs configs
COPY requirements.txt requirements.txt

# Since we are running as root in Docker, `--break-system-packages` is required
RUN python3 -m pip install -r requirements.txt --break-system-packages > /dev/null 2>1 && rm requirements.txt
RUN chmod +x $GOPATH/src/github.com/harmony-one/harmony-test/localnet/scripts/run.sh

WORKDIR $GOPATH/src/github.com/harmony-one/harmony
ENTRYPOINT ["/go/src/github.com/harmony-one/harmony-test/localnet/scripts/run.sh"]

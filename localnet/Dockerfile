FROM golang:1.14

WORKDIR $GOPATH/src/github.com/harmony-one

SHELL ["/bin/bash", "-c"]

RUN apt update && apt upgrade -y && apt update -y && apt install unzip \
libgmp-dev libssl-dev curl git jq make gcc g++ bash sudo python3 python3-pip -y

RUN git clone https://github.com/harmony-one/harmony.git

RUN git clone https://github.com/harmony-one/bls.git

RUN git clone https://github.com/harmony-one/mcl.git

# Build to fetch all dependencies for faster test builds
RUN cd harmony && go get github.com/pborman/uuid && go get github.com/rjeczalik/notify \
    && go get github.com/cespare/cp && go get github.com/libp2p/go-libp2p-crypto && go get github.com/kr/pretty \
    && go get github.com/kr/text && go get gopkg.in/check.v1 && bash scripts/install_build_tools.sh && make

RUN rm -rf harmony

# Install testing tools
WORKDIR $GOPATH/src/github.com/harmony-one/harmony-tests/localnet

COPY scripts scripts

COPY tests tests

COPY configs configs

COPY requirements.txt requirements.txt

RUN python3 -m pip install -r requirements.txt && rm requirements.txt

RUN chmod +x $GOPATH/src/github.com/harmony-one/harmony-tests/localnet/scripts/run.sh

ENTRYPOINT ["/go/src/github.com/harmony-one/harmony-tests/localnet/scripts/run.sh"]
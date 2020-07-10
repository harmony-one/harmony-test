FROM golang:1.14

WORKDIR $GOPATH/src/github.com/harmony-one

SHELL ["/bin/bash", "-c"]

RUN apt update && apt upgrade -y && apt update -y && apt install \
libgmp-dev libssl-dev curl git jq make gcc g++ bash sudo python3 python3-pip -y

RUN python3 -m pip install pyhmy==20.5.16

RUN python3 -m pip install pytest==5.4.3

RUN git clone https://github.com/harmony-one/harmony.git

RUN git clone https://github.com/harmony-one/bls.git

RUN git clone https://github.com/harmony-one/mcl.git

# Build to fetch all dependencies for faster test builds
RUN cd harmony && make

# Clear out lib builds for compatability
RUN rm -rf harmony bls mcl

RUN git clone https://github.com/harmony-one/bls.git

RUN git clone https://github.com/harmony-one/mcl.git

# Install testing tools
WORKDIR $GOPATH/src/github.com/harmony-one/harmony-tests/localnet

COPY scripts scripts

COPY tests tests

COPY configs configs

RUN chmod +x $GOPATH/src/github.com/harmony-one/harmony-tests/localnet/scripts/run.sh

ENTRYPOINT ["/go/src/github.com/harmony-one/harmony-tests/localnet/scripts/run.sh"]
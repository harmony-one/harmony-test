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

RUN cd harmony && make

RUN rm -rf harmony

WORKDIR /root

COPY scripts scripts

COPY tests tests

# TODO: add entrypoint for localnet launch and test...

RUN pwd && ls -a
FROM ubuntu:22.04

ARG TARGETARCH
ARG TARGETVARIANT

COPY intdash-edge-agent2_*.deb /var/tmp/target/

SHELL ["/bin/bash", "-c"]

RUN deb=$(find /var/tmp/target -name "*${TARGETARCH}${TARGETVARIANT/v7/hf}.deb" -exec readlink -f {} \;) \
    && apt-get update && apt-get -y install \
    "${deb}" \
    && apt-get clean && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/tmp/target

USER intdash

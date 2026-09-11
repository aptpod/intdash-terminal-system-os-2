FROM ubuntu:22.04

ARG TARGETARCH
ARG TARGETVARIANT

SHELL ["/bin/bash", "-c"]

RUN --mount=type=bind,target=/var/tmp/target \
    deb=$(find /var/tmp/target -name "*${TARGETARCH}${TARGETVARIANT/v7/hf}.deb" -exec readlink -f {} \;) \
    && apt-get update && DEBIAN_FRONTEND=noninteractive apt-get -y install \
    "${deb}" \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

USER intdash

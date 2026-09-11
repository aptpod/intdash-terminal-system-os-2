ARG TS_BASE_IMAGE_DEVICE_CONNECTOR

FROM ${TS_BASE_IMAGE_DEVICE_CONNECTOR} AS build

# build apt-usbtrx tools (by postinst script)
COPY apt-usbtrx-dkms_*_all.deb /tmp/
RUN apt-get update && apt-get install -y \
    /tmp/apt-usbtrx-dkms_*_all.deb \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

FROM ${TS_BASE_IMAGE_DEVICE_CONNECTOR}
COPY --from=build /usr/local/bin/apt_usbtrx* /usr/bin/
COPY --from=build /usr/local/bin/ep1_cf02a* /usr/bin/

ARG TARGETARCH
ARG TARGETVARIANT
ARG TS_INSTALL_PACKAGES_DEVICE_CONNECTOR

# install device-connector-intdash
SHELL ["/bin/bash", "-c"]
ARG DEBIAN_FRONTEND=noninteractive
RUN --mount=type=bind,target=/mnt/ctx \
    apt-get update && apt-get install -y \
    /mnt/ctx/device-connector-intdash_*_all.deb \
    /mnt/ctx/device-connector-*${TARGETARCH}${TARGETVARIANT/v7/hf}.deb \
    /mnt/ctx/dc-*${TARGETARCH}${TARGETVARIANT/v7/hf}.deb \
    /mnt/ctx/libdc-*${TARGETARCH}${TARGETVARIANT/v7/hf}.deb \
    $(echo "${TS_INSTALL_PACKAGES_DEVICE_CONNECTOR}" | sed 's/,/ /g') \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
RUN rm -rf /tmp/*

ENTRYPOINT ["/usr/bin/device-connector-intdash"]

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
ARG TS_INSTALL_PACKAGES_DEVICE_CONNECTOR
ARG TS_APT_EXTRA_REPO_KEY_DEVICE_CONNECTOR
ARG TS_APT_EXTRA_REPO_DEVICE_CONNECTOR
ARG TS_APT_EXTRA_REPO_PIN_PACKAGES_DEVICE_CONNECTOR

SHELL ["/bin/bash", "-c"]
ARG DEBIAN_FRONTEND=noninteractive

# Optional: Add extra APT repository with package-specific pinning
# TS_APT_EXTRA_REPO_DEVICE_CONNECTOR format: URL,distribution,component (comma-separated)
# TS_APT_EXTRA_REPO_PIN_PACKAGES_DEVICE_CONNECTOR: comma-separated package patterns (e.g., "libcamera*,gstreamer1.0-libcamera")
# Pin-Priority 600 > 500 (default) ensures specified packages from extra repo are preferred
RUN if [ -n "${TS_APT_EXTRA_REPO_KEY_DEVICE_CONNECTOR}" ] && [ -n "${TS_APT_EXTRA_REPO_DEVICE_CONNECTOR}" ]; then \
        REPO_URL=$(echo "${TS_APT_EXTRA_REPO_DEVICE_CONNECTOR}" | cut -d, -f1) && \
        REPO_DISTRO=$(echo "${TS_APT_EXTRA_REPO_DEVICE_CONNECTOR}" | cut -d, -f2) && \
        REPO_COMPONENT=$(echo "${TS_APT_EXTRA_REPO_DEVICE_CONNECTOR}" | cut -d, -f3) && \
        apt-get update && apt-get install -y curl gnupg && \
        curl -fsSL "${TS_APT_EXTRA_REPO_KEY_DEVICE_CONNECTOR}" | gpg --dearmor -o /usr/share/keyrings/extra-repo.gpg && \
        echo "deb [signed-by=/usr/share/keyrings/extra-repo.gpg] ${REPO_URL} ${REPO_DISTRO} ${REPO_COMPONENT}" > /etc/apt/sources.list.d/extra-repo.list && \
        ORIGIN=$(echo "${REPO_URL}" | sed -n 's|https\?://\([^/]*\)/.*|\1|p') && \
        PIN_PACKAGES=$(echo "${TS_APT_EXTRA_REPO_PIN_PACKAGES_DEVICE_CONNECTOR:-*}" | sed 's/,/ /g') && \
        printf "Package: %s\nPin: origin %s\nPin-Priority: 600\n" "$PIN_PACKAGES" "$ORIGIN" > /etc/apt/preferences.d/extra-repo && \
        apt-get clean && rm -rf /var/lib/apt/lists/*; \
    fi

# Optional: Install device-specific packages (low change frequency)
RUN if [ -n "${TS_INSTALL_PACKAGES_DEVICE_CONNECTOR}" ]; then \
        apt-get update && apt-get install -y \
        $(echo "${TS_INSTALL_PACKAGES_DEVICE_CONNECTOR}" | sed 's/,/ /g') \
        && apt-get clean && rm -rf /var/lib/apt/lists/*; \
    fi

# Layer: Core libraries (low change frequency)
RUN --mount=type=bind,target=/mnt/ctx \
    apt-get update && apt-get install -y \
    /mnt/ctx/dc-*${TARGETARCH}.deb \
    /mnt/ctx/libdc-*${TARGETARCH}.deb \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Layer: Applications (high change frequency)
RUN --mount=type=bind,target=/mnt/ctx \
    apt-get update && apt-get install -y \
    /mnt/ctx/device-connector-intdash_*_all.deb \
    /mnt/ctx/device-connector-*${TARGETARCH}.deb \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

ENTRYPOINT ["/usr/bin/device-connector-intdash"]

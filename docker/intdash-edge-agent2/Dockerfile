FROM ubuntu:24.04

ARG TARGETARCH

RUN --mount=type=bind,target=/var/tmp/target \
    deb=$(find /var/tmp/target -name "*${TARGETARCH}.deb" -exec readlink -f {} \;) \
    && apt-get update && DEBIAN_FRONTEND=noninteractive apt-get -y install \
    "${deb}" \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Pin intdash user/group to UID/GID 101 for persistent volume compatibility.
# The deb package creates the intdash user via adduser --system (dynamic UID),
# but rebuilding with a different base image can shift the UID.
# UID/GID 101 is the value used in 2024R1/2025R1 images (ubuntu:22.04 based).
RUN old_uid=$(id -u intdash) && old_gid=$(id -g intdash) && \
    usermod -u 101 intdash && groupmod -g 101 intdash && \
    find / -xdev -user "$old_uid" -exec chown intdash {} + 2>/dev/null ; \
    find / -xdev -group "$old_gid" -exec chgrp intdash {} + 2>/dev/null || true

USER intdash

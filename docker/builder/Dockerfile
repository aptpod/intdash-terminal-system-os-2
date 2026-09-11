FROM ubuntu:22.04

# install package
RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections
ENV DEBCONF_NOWARNINGS=yes
RUN apt-get update && apt-get install -y \
    # Yocto - Required Packages for the Build Host
    # https://docs.yoctoproject.org/ref-manual/system-requirements.html#ubuntu-and-debian
    gawk wget git diffstat unzip texinfo gcc build-essential chrpath socat cpio python3 python3-pip python3-pexpect xz-utils debianutils iputils-ping python3-git python3-jinja2 libegl1-mesa libsdl1.2-dev python3-pytest-pylint xterm python3-subunit mesa-common-dev zstd liblz4-tool \
    tmux \
    # poky
    make sudo file locales \
    # develop tool
    vim nano curl jq whois \
    # docker (rootless mode)
    # fuse-overlayfs: Without this, docker-ce/docker-moby recipe's "docker buildx bake"
    # (Docker Compose cross-build) fails with "overlay mount: invalid argument" due to
    # overlay-on-overlay nesting. fuse-overlayfs is selected over kernel overlayfs
    # in rootless mode, avoiding the nesting limitation.
    uidmap iproute2 fuse-overlayfs \
    && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# install mender-tools (via APT repository)
# https://docs.mender.io/downloads/workstation-tools
RUN curl -fsSL https://downloads.mender.io/repos/debian/gpg | tee /etc/apt/trusted.gpg.d/mender.asc && \
    echo "deb [arch=$(dpkg --print-architecture)] https://downloads.mender.io/repos/workstation-tools ubuntu/$(. /etc/os-release && echo $VERSION_CODENAME)/stable main" \
        > /etc/apt/sources.list.d/mender.list && \
    apt-get update && \
    apt-get install -y mender-artifact mender-cli && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# install yq
ENV YQ_VERSION v4.52.5
RUN wget -qO /usr/local/bin/yq https://github.com/mikefarah/yq/releases/download/${YQ_VERSION}/yq_linux_amd64
RUN chmod +x /usr/local/bin/yq

# set locale
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# add new sudo user
ENV USERNAME builder
ENV HOME /home/$USERNAME
RUN useradd -m $USERNAME && \
        passwd -d $USERNAME && \
        usermod --shell /bin/bash $USERNAME && \
        usermod -aG sudo $USERNAME && \
        mkdir -p /etc/sudoers.d && \
        echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/$USERNAME && \
        chmod 0440 /etc/sudoers.d/$USERNAME && \
        # Replace 1000 with your user/group id
        usermod  --uid 1000 $USERNAME && \
        groupmod --gid 1000 $USERNAME
USER $USERNAME
WORKDIR /home/$USERNAME/work

# ssh known_hosts settings
RUN mkdir ~/.ssh && \
    chmod 700 ~/.ssh && \
    chown "$USERNAME:$USERNAME" ~/.ssh && \
    echo "StrictHostKeyChecking no" >> ~/.ssh/config

# install docker (rootless mode)
ENV DOCKER_VERSION 29.3.0
RUN cd $HOME && curl -fsSL https://get.docker.com -o get-docker.sh && \
    sudo sh get-docker.sh --version ${DOCKER_VERSION}
# Use fuse-overlayfs for rootless Docker to avoid overlay-on-overlay nesting issues.
# Without this, docker-ce/docker-moby recipe's "docker buildx bake" fails with
# "overlay mount: invalid argument" when building Docker Compose.
RUN mkdir -p $HOME/.config/docker && \
    echo '{"storage-driver": "fuse-overlayfs"}' > $HOME/.config/docker/daemon.json
RUN echo "export XDG_RUNTIME_DIR=/home/$USERNAME/.docker/run" >> $HOME/.bashrc && \
    echo "export PATH=/usr/bin:$PATH" >> ~/.bashrc && \
    echo "export DOCKER_HOST=unix:///home/$USERNAME/.docker/run/docker.sock" >> ~/.bashrc
RUN dockerd-rootless-setuptool.sh --skip-iptables install --force

# install aws-cli
RUN cd $HOME && curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && rm awscliv2.zip && \
    sudo ./aws/install

COPY entrypoint.sh /
ENTRYPOINT ["bash", "-i", "/entrypoint.sh"]
CMD ["/bin/bash"]
#!/bin/bash

user=builder
uid=$(stat -c "%u" .)
gid=$(stat -c "%g" .)

function start_docker_daemon() {
    echo "start docker-in-docker (rootless mode)"
    source /home/$user/.bashrc
    sudo -Eu $user PATH=/usr/bin:/sbin:/usr/sbin:$PATH dockerd-rootless.sh >/dev/null 2>&1 &
}

echo "Launching..."

if [ "$(id -u)" -eq 0 ]; then
    # run by launch.sh (user:root)

    # change builder UID:GID
    if [ "$(id -g $user)" -ne $gid ]; then
        groupmod -g $gid $user
    fi
    if [ "$(id -u $user)" -ne $uid ]; then
        usermod -u $uid $user
    fi
    start_docker_daemon
    exec setpriv --reuid=$uid --regid=$gid --init-groups "$@"
else
    # run by ci (user:builder)
    start_docker_daemon
    exec "$@"
fi

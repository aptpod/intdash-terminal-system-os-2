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
    # NOTE: Using sed instead of usermod/groupmod to avoid slow OverlayFS copy-up
    # usermod/groupmod changes file ownership, triggering copy-up for all user-owned files
    current_uid=$(id -u $user)
    current_gid=$(id -g $user)
    if [ "$current_gid" -ne "$gid" ]; then
        sed -i "s/^$user:x:$current_gid:/$user:x:$gid:/" /etc/group
    fi
    if [ "$current_uid" -ne "$uid" ]; then
        sed -i "s/^$user:x:$current_uid:$current_gid:/$user:x:$uid:$gid:/" /etc/passwd
        # Update ownership of home directory and essential subdirectories only
        chown $uid:$gid /home/$user
        chown -R $uid:$gid /home/$user/.docker /home/$user/.ssh 2>/dev/null || true
    fi
    start_docker_daemon
    exec setpriv --reuid=$uid --regid=$gid --init-groups "$@"
else
    # run by ci (user:builder)
    start_docker_daemon
    exec "$@"
fi

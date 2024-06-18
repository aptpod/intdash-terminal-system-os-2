#!/bin/bash -e

echo "Artifacts to be uploaded:"
for artifact in $(find . -maxdepth 2 -mindepth 2 -type f -name "*.mender"); do
    echo "  $(readlink -f $artifact)"
done

read -p "Do you wish to continue? (Y/N): " answer
answer=$(echo "$answer" | tr '[:upper:]' '[:lower:]')

if [[ "$answer" == "y" ]]; then
    for artifact in $(find . -maxdepth 2 -mindepth 2 -type f -name "*.mender"); do
        echo "Upload $(basename $artifact)"
        mender-cli artifacts upload $artifact
    done
elif [[ "$answer" == "n" ]]; then
    exit 0
else
    echo "Invalid input. Please enter Y or N."
    exit 1
fi

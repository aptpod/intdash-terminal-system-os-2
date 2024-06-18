# Terminal System Artifact Template

This is a template project for generating application update artifacts for Terminal System 2.

## Generating an Artifact

Execute the following command to generate an artifact:

```bash
./generate.sh
```

This will initially create an empty artifact. Refer to the following sections to understand how to customize it.

## Customizing the Artifact

Modify `config.sh`, `custom` directory, and `metadata.json`.

### Configuring Artifact information (`config.sh`)

This file contains basic information about the artifact.

| Variable | Description | Example |
| --- | --- | --- |
| ARTIFACT_NAME | Name of the artifact | `sample` |
| DEVICE_TYPES | Array of supported devices (The default value is all devices) | `("edgeplant-t1" "raspberrypi4-64")` |
| ARTIFACT_VERSION | Version of the artifact (leave blank to omit version information) | `1.0.0` |
| SOFTWARE_FILESYSTEM | File system destination for the artifact installation (comment out if installing to the data partition; the version will be maintained through OS updates) | `data-partition` |

### Custom Directory (`custom`)

This directory contains scripts executed by the custom update module and the file/folder contents to be included in the artifact.

| Path | Description |
| --- | --- |
| custom/custom_script.sh | Custom script |
| custom/contents | Directory for storing files/folders to be included in the artifact |

#### Custom Script (`custom_script.sh`)

This script runs when the artifact is deployed to a device using Mender.

Implement installation processes within the `custom_artifact_install` function. The path to the custom/contents directory is stored in `CUSTOM_CONTENTS_DIR`, so use this variable as needed to describe your installation processes.

`CUSTOM_TMP_DIR` is a temporary directory available during the update process, which gets deleted post-deployment.

Each function within the script is called based on the various states of the update process. This includes potential implementation of reboot and rollback procedures during the update. For more details, please refer to the [Mender documentation](https://docs.mender.io/artifact-creation/create-a-custom-update-module).

### Metadata (`metadata.json`)

This file should contain the metadata to be included in the artifact, formatted in JSON.

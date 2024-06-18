# apt-usbtrx-updater

## Description

EDGEPLANT Peripherals製品のファームウェアを更新するアップデートモジュールです。

### Specification

|||
| --- | --- |
|Module name| apt-usbtrx-updater |
|Supports rollback|no|
|Requires restart|no|
|Artifact generation script|yes|
|Full system updater|no|

### Create artifact

以下コマンドでアップデートモジュールを生成します。

    ./generate.sh

### Customize artifact

内容をカスタマイズする場合は、`config.sh`、`custom`ディレクトリ、`metadata.json`を変更します。

同梱するファームウェアは `custom/contents/firmware` に配置します。


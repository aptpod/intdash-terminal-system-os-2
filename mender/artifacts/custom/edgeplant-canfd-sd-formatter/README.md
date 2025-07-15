# edgeplant-canfd-sd-formatter

## Description

EDGEPLANT CAN FD USB Interfaceに搭載されている、CANデータ一時保存用データストレージをフォーマットします。

## Specification

|||
| --- | --- |
| Module name | edgeplant-canfd-sd-formatter |
| Supports rollback | no |
| Requires restart | no |
| Artifact generation script | yes |
| Full system updater | no |

## Create artifact

以下コマンドでアップデートモジュールを生成します。

    ./generate.sh

## Customize artifact

内容をカスタマイズする場合は、`config.sh`、`custom`ディレクトリ、`metadata.json`を変更します。

同梱するファームウェアは `custom/contents/firmware` に配置します。

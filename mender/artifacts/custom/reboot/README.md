# reboot

## Description

再起動するアップデートモジュールです。

## Specification

|||
| --- | --- |
| Module name | reboot |
| Supports rollback | no |
| Requires restart | yes |
| Artifact generation script | yes |
| Full system updater | no |

## Create artifact

以下コマンドでアップデートモジュールを生成します。

    ./generate.sh

## Customize artifact

内容をカスタマイズする場合は、`config.sh`、`custom`ディレクトリ、`metadata.json`を変更します。
# terminal-display-updater

## Description

Terminal Displayのファームウェアを更新するアップデートモジュールです。

## Specification

|||
| --- | --- |
| Module name | terminal-display-updater |
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
バージョンファイルも `custom/contents/firmware/firmware_version` に同梱してください。

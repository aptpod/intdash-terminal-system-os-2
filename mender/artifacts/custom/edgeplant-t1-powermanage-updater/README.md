# edgeplant-t1-powermanage-updater

## Description

EDGEPLANT T1の電源マイコンファームウェアを更新するアップデートモジュールです。

アップデートした電源マイコンファームウェアは、電源オフまたは以下のコマンドを実行した後に更新されます。

    systemctl poweroff

## Specification

|||
| --- | --- |
| Module name | edgeplant-t1-powermanage-updater |
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

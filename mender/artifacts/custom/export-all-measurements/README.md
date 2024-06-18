# delete-all-measurements

## Description

全ての計測をエクスポートします。

エクスポートは条件を満たした外部ディスクのパーティションに対して実行されます。
エクスポートが行われる条件は、外部ディスクの書き込み可能なパーティションがマウントされ、そのマウントディレクトリに 'export-all-measurements' というファイルが存在する場合です。

## Specification

|                            |                         |
| -------------------------- | ----------------------- |
| Module name                | export-all-measurements |
| Supports rollback          | no                      |
| Requires restart           | no                      |
| Artifact generation script | yes                     |
| Full system updater        | no                      |

## Create artifact

以下コマンドでアップデートモジュールを生成します。

    ./generate.sh

## Customize artifact

内容をカスタマイズする場合は、`config.sh`、`custom`ディレクトリ、`metadata.json`を変更します。
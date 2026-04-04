# 大学オープンキャンパス情報（univ_info_cursor）

このサイトは **GitHub リポジトリ [mtakahashi1150/univ_info_cursor](https://github.com/mtakahashi1150/univ_info_cursor)** 上のデータからビルドされた **静的ページ** です。

- [累積表（Markdown 生成）](opencampus.md)

## 運用

- 対象大学の整理（早慶上理・G-MARCH・情報系・キャンパス）は `config/target_catalog.yaml` です。
- 取得 URL は `config/sources.yaml` に **手動で検証したものだけ** を列挙します。
- 定期実行（GitHub Actions またはローカル）で取得し、`data/snapshots/` と累積表を更新します。
- 更新があった場合のみメール通知（SMTP 設定時）します。

詳細はリポジトリの `README.md` を参照してください。

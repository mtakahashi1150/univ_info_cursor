# 大学オープンキャンパス情報アグリゲータ（univ_info_cursor）

GitHub ユーザー **`mtakahashi1150`** 配下のリポジトリ **`univ_info_cursor`** 用のプロジェクトです。既存の `univ_info` などと区別するため、この名前で管理します。

検証済み URL からオープンキャンパス情報を取得し、`data/snapshots/` に JSON を累積、`docs/opencampus.md` に表を出力します。静的サイトは **MkDocs Material** でビルドし、**GitHub Pages**（`gh-pages` ブランチ）に公開します。更新があったときだけ **Gmail SMTP** で通知できます。

- **リポジトリ**: `https://github.com/mtakahashi1150/univ_info_cursor`
- **GitHub Pages（想定）**: `https://mtakahashi1150.github.io/univ_info_cursor/`

## 前提

- Python 3.9+
- 対象 URL は **`config/sources.yaml` に手動で検証したものだけ** を追加する（推測 URL は禁止）

## セットアップ

```bash
git clone https://github.com/mtakahashi1150/univ_info_cursor.git
cd univ_info_cursor
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
pip install -r requirements-docs.txt
```

## 実行

CLI コマンドは **`univ-oc-cursor`** です。

```bash
univ-oc-cursor run
univ-oc-cursor run --notify
univ-oc-cursor verify-urls
univ-oc-cursor run --dry-run
```

モジュールとしては `python -m univ_oc` でも起動できます。

## 静的サイト（ローカル）

```bash
mkdocs serve
```

`mkdocs.yml` の `site_url` / `repo_url` は上記の GitHub 向けに設定済みです。リポジトリ名やユーザー名を変える場合のみ編集してください。

## GitHub Actions

`.github/workflows/oc-sync.yml` が定期実行します（`univ-oc-cursor run --notify`）。

### Secrets（任意・メール用）

| Name | 説明 |
|------|------|
| `SMTP_USER` | Gmail アドレス |
| `SMTP_PASSWORD` | アプリパスワード |
| `EMAIL_TO` | 宛先（省略時は SMTP_USER） |
| `SMTP_HOST` | 省略時 `smtp.gmail.com` |
| `SMTP_PORT` | 省略時 `587` |
| `PAGES_BASE_URL` | 省略時は `.env.example` 同様 `https://mtakahashi1150.github.io/univ_info_cursor/` を推奨 |

### GitHub Pages

リポジトリ **Settings → Pages** で **Branch: gh-pages / / (root)** を有効にします。

## 新しい大学を追加する

1. ブラウザで公式（または信頼できる）案内ページを開き、内容を確認する。
2. `config/sources.yaml` にエントリを追加する。
3. `src/univ_oc/parsers/` にパーサーを追加し、`PARSERS` に登録する。
4. `univ-oc-cursor verify-urls` で HTTP 確認する。

## 開発

```bash
pip install -e ".[dev]"
pytest
ruff check src tests
```

## ライセンス

MIT（必要に応じて変更してください）

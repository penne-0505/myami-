# Git 運用基準

## 目的
- **Traceability**: `TODO.md` のタスク、ドキュメント、そしてコード変更の完全な追跡可能性を担保する。
- **Quality**: コミット粒度とメッセージの標準化により、レビュー効率と履歴の可読性を維持する。
- **Automation**: LLMやCIツールが履歴を解析しやすい形式を徹底する。

## 1. ブランチ戦略

### ブランチ命名規則
ブランチ名は、`TODO.md` で採番された **タスクID** を必ず含めること。
形式: `{Prefix}/{Task-ID}-{Description}`

| Prefix | 対応する TODO Category | 用途 |
| :--- | :--- | :--- |
| `feature/` | `Feat` / `Enhance` | 新機能・機能改善 |
| `fix/` | `Bug` | バグ修正 |
| `refactor/` | `Refactor` / `Perf` | リファクタリング・パフォーマンス改善 |
| `docs/` | `Doc` | ドキュメントのみの変更 |
| `test/` | `Test` | テストコードの変更 |
| `chore/` | `Chore` / その他 | ビルド設定、雑務 |

### 命名例
- **Good**: `feature/Core-Feat-25-auth-login` (タスクIDが含まれている)
- **Good**: `fix/UI-Bug-26-typo`
- **Bad**: `feature/login` (どのタスクか不明)
- **Bad**: `Core-Feat-25` (何をするのか不明)

### ベースブランチ
- **`main`**: プロダクション用（常にデプロイ可能な状態）。
- **`dev`**: 開発用ベースブランチ。通常、PRはここに向けて作成する。

## 2. コミットメッセージ

[Conventional Commits](https://www.conventionalcommits.org/) に準拠する。

### フォーマット
```text
<type>(<scope>): <subject>

<body>
```

  - **Header**: 必須。50-72文字程度。
  - **Body**: 必須（`chore` や `docs` などの自明な変更を除く）。"Why" と "What" を記述する。
  - **Scope**: 任意。`TODO.md` の `Area` (例: `Core`, `UI`) を指定すると可読性が上がる。

### Type 一覧

  - `feat`: 新機能 (minor version up)
  - `fix`: バグ修正 (patch version up)
  - `docs`: ドキュメントのみの変更
  - `style`: コードの動作に影響しない変更（フォーマット等）
  - `refactor`: バグ修正も機能追加も行わないコード変更
  - `perf`: パフォーマンスを向上させる変更
  - `test`: テストの追加・修正
  - `build`: ビルドシステムや外部依存の変更
  - `ci`: CI設定ファイルの変更
  - `chore`: その他の変更

### 記述例

```text
feat(Core): implement user authentication logic

- Add JWT token generation service
- Create login API endpoint
- Update user schema for password hash

Ref: Core-Feat-25
```

## 3\. プルリクエスト (PR) 運用

### タイトル

コミットメッセージの Header と同様の形式を使用する。タスクIDを含めることを推奨する。

  - 例: `feat(Core): implement auth logic (Core-Feat-25)`

### Description 必須項目

PR作成時は以下の情報を必ず記載する（テンプレート利用を推奨）。

1.  **Related Task**: `TODO.md` のタスクID (例: `Core-Feat-25`)
2.  **Documentation**:
      - **Large Change**: 関連する `_docs/plan/` または `_docs/intent/` へのリンク。
      - **Small Change**: 「ドキュメント変更なし」の明記、または `TODO.md` の手順準拠である旨。
3.  **Changes**: 変更内容の要約。
4.  **Verification**: 動作確認手順やテスト結果のスクリーンショット。

### レビュー基準

  - CI がパスしていること。
  - `TODO.md` の `Steps` に記載された項目が達成されていること。
  - 新機能・仕様変更の場合、ドキュメント（`guide` / `reference`）の更新が含まれていること。

## 4\. LLM / AI Agent 利用ガイドライン

AIエージェントがコードを生成・コミットする場合の特記事項。

  - **Atomic Commits**: 複数の異なる修正を1つのコミットにまとめないこと。論理的な単位で分割する。
  - **No Hallucinated Types**: 上記 `Type 一覧` にないプレフィックス（例: `update:`, `mod:`）を使用しない。
  - **Language**: コミットメッセージ、PRの説明は **英語** で記述する。（ドキュメント本文は日本語でよい）


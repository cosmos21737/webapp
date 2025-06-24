# Render.com デプロイガイド

## 🚀 Render.comへの移行手順

### 1. 準備作業

#### GitHubリポジトリの準備
1. 現在のコードをGitHubにプッシュ
2. リポジトリが公開されていることを確認

#### Render.comアカウントの準備
1. [Render.com](https://render.com)にアクセス
2. GitHubアカウントでサインアップ/ログイン

### 2. Render.comでのデプロイ

#### 新しいWeb Serviceの作成
1. Render.comダッシュボードで「New +」をクリック
2. 「Web Service」を選択
3. GitHubリポジトリを連携
4. リポジトリを選択

#### 設定の入力
- **Name**: `baseball-team-app` (任意)
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python -m flask run --host=0.0.0.0 --port=$PORT`
- **Plan**: `Free`

#### 環境変数の設定
Render.comのダッシュボードで以下の環境変数を設定：

```
FLASK_APP=app.app
FLASK_ENV=production
SECRET_KEY=<自動生成または手動設定>
SECURITY_PASSWORD_SALT=<自動生成または手動設定>
DATABASE_URL=sqlite:///baseball_team.db
```

### 3. デプロイの実行

1. 「Create Web Service」をクリック
2. 自動ビルド・デプロイが開始
3. デプロイ完了まで待機（通常5-10分）

### 4. 動作確認

1. 提供されたURLにアクセス
2. アプリケーションが正常に動作することを確認
3. データベースの初期化が正常に行われることを確認

### 5. カスタムドメインの設定（オプション）

1. Render.comダッシュボードで「Settings」タブ
2. 「Custom Domains」セクション
3. 独自ドメインを追加

## 🔧 トラブルシューティング

### よくある問題

#### 1. ビルドエラー
- `requirements.txt`の依存関係を確認
- Python 3.11の互換性を確認

#### 2. データベースエラー
- SQLiteファイルの権限を確認
- データベース初期化スクリプトの実行

#### 3. 環境変数エラー
- 必要な環境変数が設定されているか確認
- 値の形式が正しいか確認

### ログの確認方法

1. Render.comダッシュボードで「Logs」タブ
2. リアルタイムログを確認
3. エラーメッセージを特定

## 📊 Railway.comとの比較

| 機能 | Railway | Render |
|------|---------|--------|
| 無料プラン | ✅ | ✅ |
| 自動デプロイ | ✅ | ✅ |
| カスタムドメイン | ✅ | ✅ |
| SSL証明書 | ✅ | ✅ |
| 環境変数 | ✅ | ✅ |
| ログ管理 | ✅ | ✅ |
| データベース | ✅ | ✅ |

## 🎯 移行のメリット

1. **無料プランの充実**: 月500時間の無料利用
2. **簡単な設定**: `render.yaml`で設定を管理
3. **自動スケーリング**: トラフィックに応じた自動調整
4. **優れたドキュメント**: 詳細なガイドとサポート

## 📞 サポート

問題が発生した場合は：
1. Render.comのドキュメントを確認
2. コミュニティフォーラムを利用
3. サポートチケットを作成 
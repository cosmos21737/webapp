# Railway デプロイ手順

このドキュメントでは、野球チーム管理アプリケーションをRailwayにデプロイする手順を説明します。

## Railwayの特徴

- **無料プラン**: 月500時間まで無料
- **SQLiteサポート**: 現在のデータベース構造をそのまま使用可能
- **ファイル永続化**: アップロードされたファイルも保持
- **簡単デプロイ**: GitHubリポジトリと連携して自動デプロイ
- **カスタムドメイン**: 無料でカスタムドメイン設定可能

## デプロイ手順

### 1. Railwayアカウントの作成

1. [Railway](https://railway.app/) にアクセス
2. GitHubアカウントでサインアップ
3. 新しいプロジェクトを作成

### 2. GitHubリポジトリの準備

```bash
# リポジトリをGitHubにプッシュ
git add .
git commit -m "Add Railway deployment configuration"
git push origin main
```

### 3. Railwayでのデプロイ

1. **プロジェクト作成**:
   - Railwayダッシュボードで「New Project」をクリック
   - 「Deploy from GitHub repo」を選択
   - リポジトリを選択

2. **環境変数の設定**:
   - プロジェクト設定で以下の環境変数を設定：
   ```
   FLASK_ENV=production
   FLASK_APP=app.app
   SECRET_KEY=your_secure_secret_key_here
   ```

3. **デプロイ実行**:
   - Railwayが自動的にDockerfileを検出してビルド
   - デプロイが完了するとURLが生成される

### 4. カスタムドメインの設定（オプション）

1. Railwayダッシュボードで「Settings」タブを開く
2. 「Domains」セクションでカスタムドメインを追加
3. DNSレコードを設定

## 重要な設定

### 環境変数

Railwayダッシュボードで以下の環境変数を設定してください：

```
FLASK_ENV=production
FLASK_APP=app.app
SECRET_KEY=your_secure_secret_key_here
SQLALCHEMY_DATABASE_URI=sqlite:///instance/baseball_team.db
```

### データベースの永続化

Railwayでは以下のディレクトリが永続化されます：
- `/app/instance/` - SQLiteデータベースファイル
- `/app/uploads/` - アップロードされたファイル

## デプロイ後の確認

### 1. アプリケーションの動作確認

デプロイ完了後、提供されたURLにアクセスして以下を確認：
- ログインページが表示される
- データベースが正常に初期化される
- ファイルアップロード機能が動作する

### 2. ログの確認

Railwayダッシュボードでログを確認：
- デプロイログ
- アプリケーションログ
- エラーログ

### 3. パフォーマンスの監視

Railwayダッシュボードで以下を確認：
- CPU使用率
- メモリ使用率
- ネットワーク使用量

## 更新手順

アプリケーションを更新する場合：

1. **コードの変更**:
   ```bash
   git add .
   git commit -m "Update application"
   git push origin main
   ```

2. **自動デプロイ**:
   - Railwayが自動的にGitHubの変更を検出
   - 新しいバージョンが自動デプロイされる

## トラブルシューティング

### よくある問題

1. **デプロイエラー**:
   - Dockerfileの構文エラーを確認
   - requirements.txtの依存関係を確認
   - ログで詳細なエラーを確認

2. **アプリケーションエラー**:
   - 環境変数の設定を確認
   - データベースファイルの権限を確認
   - アプリケーションログを確認

3. **パフォーマンス問題**:
   - メモリ使用量を確認
   - 不要なファイルを削除
   - データベースの最適化を検討

### ログの確認方法

```bash
# Railway CLIを使用してログを確認
railway login
railway link
railway logs
```

## コスト管理

### 無料プランの制限

- **月500時間**: 通常の使用では十分
- **ストレージ**: 1GBまで無料
- **帯域幅**: 月100GBまで無料

### 使用量の確認

Railwayダッシュボードで以下を確認：
- 使用時間
- ストレージ使用量
- 帯域幅使用量

## セキュリティ

### 推奨事項

1. **SECRET_KEY**: 強力なランダム文字列を使用
2. **環境変数**: 機密情報は環境変数で管理
3. **HTTPS**: Railwayは自動的にHTTPSを提供
4. **アクセス制御**: 必要に応じて認証を実装

## バックアップ

### データベースのバックアップ

```bash
# Railway CLIを使用してデータベースをダウンロード
railway run sqlite3 instance/baseball_team.db ".backup backup.db"
```

### ファイルのバックアップ

重要なファイルは定期的にバックアップを取得することを推奨します。

## サポート

- **Railway Docs**: https://docs.railway.app/
- **Railway Discord**: https://discord.gg/railway
- **GitHub Issues**: プロジェクト固有の問題はGitHubで報告 
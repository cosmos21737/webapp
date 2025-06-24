# Cloud Run デプロイ手順

このドキュメントでは、野球チーム管理アプリケーションをGoogle Cloud Runにデプロイする手順を説明します。

## 前提条件

1. Google Cloud Platform アカウント
2. Google Cloud CLI (gcloud) のインストール
3. Docker のインストール
4. プロジェクトの設定

## 1. Google Cloud プロジェクトの設定

```bash
# Google Cloud CLI にログイン
gcloud auth login

# プロジェクトを設定
gcloud config set project YOUR_PROJECT_ID

# 必要なAPIを有効化
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

## 2. ローカルでのDockerイメージビルドとテスト

```bash
# Dockerイメージをビルド
docker build -t baseball-team-app .

# ローカルでテスト実行
docker run -p 8080:8080 baseball-team-app
```

## 3. Cloud Run へのデプロイ

### 方法1: Cloud Build を使用した自動デプロイ

```bash
# Cloud Build を実行
gcloud builds submit --config cloudbuild.yaml
```

### 方法2: 手動デプロイ

```bash
# DockerイメージをContainer Registryにプッシュ
docker tag baseball-team-app gcr.io/YOUR_PROJECT_ID/baseball-team-app
docker push gcr.io/YOUR_PROJECT_ID/baseball-team-app

# Cloud Run にデプロイ
gcloud run deploy baseball-team-app \
  --image gcr.io/YOUR_PROJECT_ID/baseball-team-app \
  --platform managed \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --max-instances 10
```

## 4. 環境変数の設定（必要に応じて）

```bash
gcloud run services update baseball-team-app \
  --region asia-northeast1 \
  --set-env-vars "FLASK_ENV=production,FLASK_APP=app.app"
```

## 5. カスタムドメインの設定（オプション）

```bash
# カスタムドメインをマッピング
gcloud run domain-mappings create \
  --service baseball-team-app \
  --domain your-domain.com \
  --region asia-northeast1
```

## 6. 監視とログの確認

```bash
# ログを確認
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=baseball-team-app" --limit 50

# メトリクスを確認
gcloud run services describe baseball-team-app --region asia-northeast1
```

## 重要な注意事項

### データベースについて
- 現在のアプリケーションはSQLiteを使用しています
- Cloud Runはステートレスなため、データベースファイルは永続化されません
- 本番環境では以下のいずれかの対応が必要です：
  1. Cloud SQL (PostgreSQL/MySQL) への移行
  2. Cloud Firestore への移行
  3. 外部ストレージ（Cloud Storage）へのデータ保存

### セキュリティ
- 本番環境では `SECRET_KEY` を環境変数で設定してください
- データベースのパスワードも環境変数で管理してください

### スケーラビリティ
- Cloud Runは自動スケーリングされます
- 必要に応じて `--max-instances` を調整してください

## トラブルシューティング

### よくある問題

1. **ポートエラー**
   - Cloud Runは8080ポートを使用する必要があります
   - `app.py`の`app.run()`でポート8080を指定してください

2. **メモリ不足**
   - デフォルトで512Miに設定しています
   - 必要に応じて `--memory` を増やしてください

3. **タイムアウト**
   - デフォルトで300秒に設定されています
   - 必要に応じて `--timeout` を調整してください

### ログの確認

```bash
# リアルタイムでログを確認
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=baseball-team-app"
```

## 更新手順

アプリケーションを更新する場合：

```bash
# 新しいバージョンをビルドしてデプロイ
gcloud builds submit --config cloudbuild.yaml
```

または

```bash
# 手動で更新
docker build -t gcr.io/YOUR_PROJECT_ID/baseball-team-app .
docker push gcr.io/YOUR_PROJECT_ID/baseball-team-app
gcloud run deploy baseball-team-app --image gcr.io/YOUR_PROJECT_ID/baseball-team-app --region asia-northeast1
``` 
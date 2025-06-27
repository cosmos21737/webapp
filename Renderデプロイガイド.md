# Render.com デプロイガイド

### 1. 準備

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
Environment Variablesに以下の環境変数を設定：

```
FLASK_APP=app.app
FLASK_ENV=production
SECRET_KEY='baseball_team_2024_secure_key_32chars_long_for_test'
SECURITY_PASSWORD_SALT='baseball_team_2024_salt_16chars'
DATABASE_URL=sqlite:///baseball_team.db
```

### 3. デプロイの実行

1. 「Create Web Service」をクリック
2. 自動ビルド・デプロイが開始
3. デプロイ完了まで待機（通常5-10分）

### 4. 動作確認

1. 提供されたURLにアクセス



問題が発生した場合は：
1. Githubのアカウント、参照するレポジトリが適切か確認する。
2. 設定の入力が適切か確認する。
3. 環境変数が適切に設定されているか確認する。

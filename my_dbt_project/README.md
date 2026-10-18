# Cloud Run Jobs での dbt 自動実行手順

このドキュメントでは、Google Cloud Platform (GCP) の **Cloud Run Jobs** と **Docker** を用いて、dbt（dbt-bigquery）のデータパイプライン構築（`dbt build`）を自動実行するまでの手順をまとめています。

---

## 1. 事前準備：サービスアカウントの作成と権限付与

Cloud Run Jobs が BigQuery や Google Cloud Storage (GCS) にアクセスするための専用サービスアカウントを作成し、必要な権限を付与します。

1. **サービスアカウントの作成**
   * 名前例: `dbt-job-sa`
2. **IAM ロールの付与（プロジェクトレベル）**
   * **BigQuery データ編集者**（データセットの作成・編集権限）
   * **BigQuery ユーザー**（クエリの実行権限）

---

## 2. GCS バケットへのサービスアカウントの追加

クエリ内で参照する GCS バケットからデータを読み込めるよう、作成したサービスアカウントにストレージの権限を追加します。

1. 対象の GCS バケットの詳細画面を開く。
2. 「権限」タブを開き、**「+ アクセスを許可」** をクリックする。
3. 新しいプリンシパルとして作成したサービスアカウント（例: `dbt-job-sa@project-id.iam.gserviceaccount.com`）を指定する。
4. ロールとして **「ストレージ オブジェクト閲覧者」** を選択して保存する。

---

## 3. dbt プロジェクトおよび不要ファイル除外の設定

### ① `profiles.yml` の設定
Cloud Run 上のサービスアカウントのデフォルト認証情報（OAuth / Application Default Credentials）を利用するため、`method: oauth` を指定します。また、トップレベルのキー名は `dbt_project.yml` の `name:` と完全に一致させます。

```yaml
my_dbt_project:
  target: dev
  outputs:
    dev:
      type: bigquery
      method: oauth
      project: "{{ env_var('DBT_PROJECT_ID') }}"
      dataset: "{{ env_var('DBT_DATASET') }}"
      threads: 4  # 同時並列実行数（依存関係のないモデルを最大4つまで同時に並列処理）
      timeout_seconds: 300
      priority: interactive
```

### ② `.gitignore` の設定
ローカル環境で生成される一時ファイルや環境変数が Git 管理に入らないように除外します。

```text
target/
dbt_packages/
logs/
.env
```

### ③ `.dockerignore` の設定
Docker イメージのビルド時に、不要なローカルキャッシュや生成物をコンテナへコピーしないように除外します（ビルドの高速化・軽量化）。

```text
.git
.gitignore
target/
dbt_packages/
logs/
.env
README.md
```

---

## 4. コンテナ化とビルド設定

### `Dockerfile` の作成
Python 環境をベースに `dbt-bigquery` をインストールし、外部パッケージ（`packages.yml`）のインストール（`dbt deps`）を含めた構成にします。

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir dbt-bigquery

# プロジェクトファイルをすべてコピー
COPY . .

# 外部パッケージのインストール
RUN dbt deps

# 実行コマンド
CMD ["dbt", "build"]
```

---

## 5. デプロイと実行の自動化

### Python デプロイ用スクリプト (`deploy.py`)
Cloud Build を使ったイメージのビルドと、Cloud Run Jobs の登録・更新を自動化するスクリプトを用意します。環境変数（`DBT_PROJECT_ID`, `DBT_DATASET`）やサービスアカウントを指定してデプロイを実行します。
```bash
python deploy.py
```


---

## 6. 実行確認

Cloud Run コンソール画面、または以下のコマンドからジョブを実行し、ログに `Completed successfully` および `Done. PASS=4 ...` が表示されれば成功です。

```bash
gcloud run jobs execute dbt-power-job --region=asia-northeast1
```



## 🚀 実行コマンド

### プロジェクトの場所を指定してビルドする場合

`--project-dir`で`dbt_project.yml`があるフォルダーを指定すると、そのプロジェクトのフォルダーへ移動せずにビルドできます。
相対パスはコマンドを実行したときの現在のフォルダーを基準にするため、次の例はリポジトリのルートフォルダーで実行します。

```bash
dbt build --project-dir "my_dbt_project"
```

### 中間層（Intermediate層）のみをビルドする場合
```bash
dbt build --select intermediate

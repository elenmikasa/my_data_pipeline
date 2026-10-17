# Google Cloud（Workflows / Cloud Run Jobs）を活用したサーバーレスデータパイプライン

本ドキュメントでは、Cloud Workflows を用いたデータパイプライン（`power-csv-fetcher-job` および `power-csv-transformer-job` の逐次実行）の構築手順とデプロイ方法について説明します。

---
## 処理フロー図

```mermaid
flowchart TD
    subgraph External["外部サイト"]
        WEB["一般送配電事業者 WEBサイト<br>(エリア需給実績CSV)"]
    end

    subgraph GCP["Google Cloud Platform"]
        WF["Cloud Workflows<br>(power-etl-workflow)"]

        subgraph CloudRun["Cloud Run Jobs"]
            Fetcher["power-csv-fetcher-job<br>(HTTPクライアントによるCSV自動ダウンロード)"]
            Transformer["power-csv-transformer-job<br>(BigQuery用にヘッダー加工)"]
        end

        subgraph Storage["Cloud Storage (GCS)"]
            RawGCS[("GCS (raw/)\n未加工CSVファイル")]
            ProcessedGCS[("GCS (eria_jukyu_last_month/)\n加工済みCSVファイル")]
        end
    end

    WF -->|1. 起動呼び出し| Fetcher
    Fetcher -->|2. CSV取得| WEB
    Fetcher -->|3. 保存| RawGCS
    
    WF -->|4. Fetcher完了後に起動| Transformer
    RawGCS -->|5. 読み込み| Transformer
    Transformer -->|6. 加工済みCSV出力| ProcessedGCS
```
## 1. 事前準備 (IAM 権限の設定)

Cloud Workflows から Cloud Run Jobs (`power-csv-fetcher-job`, `power-csv-transformer-job`) を実行するため、専用のサービスアカウントを作成し、必要なロールを付与します。

### サービスアカウント名
`power-fetcher-sa@<PROJECT_ID>.iam.gserviceaccount.com`

### 付与する IAM ロール
ワークフローの実行用サービスアカウントには、以下のロールを付与します。

1. **Cloud Run 閲覧者** (`roles/run.viewer`)
   - ジョブの実行結果・ステータスを取得するために必要
2. **Cloud Run 起動元** (`roles/run.invoker`)
   - Cloud Run Jobs の実行（トリガー）に必要
3. **ログ書き込み** (`roles/logging.logWriter`)
   - ワークフローの実行ログを Cloud Logging へ書き込むために必要
4. **ワークフロー起動元** (`roles/workflows.invoker`)
   - ワークフローの実行・管理に必要

> **補足（権限反映の注意点）**:  
> IAM ロールを追加・更新した直後は、Google Cloud 全体へ権限設定が反映されるまでに数分程度のタイムラグが発生する場合があります。エラー（403 Permission Denied 等）が発生した場合は、数分時間を置いてから再実行してください。

---

## 2. 環境変数ファイル (`.env`) の準備

プロジェクト直下に `.env` ファイルを作成し、以下のパラメータを設定します。

```env
PROJECT_ID: ご自身のPROJECT_ID
REGION: asia-northeast1
WORKFLOW_NAME: power-etl-workflow
```

---

## 3. ワークフローのデプロイ

PowerShell 環境（Windows）でデプロイスクリプトを実行します。

```powershell
.\deploy.ps1
```

> **文字コードに関する注意**:  
> PowerShell で日本語ログを正しく表示するため、`deploy.ps1` は **`UTF-8 with BOM`** 形式で保存してください。
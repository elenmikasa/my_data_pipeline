# コンソールの出力文字コードを UTF-8 に設定
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
# エラーが発生した際に処理をストップする設定
$ErrorActionPreference = "Stop"

Write-Host "=== 1. .env から環境変数を読み込みます ===" -ForegroundColor Cyan
Get-Content .env | foreach { 
    if($_ -match "^([^#:]+):\s*(.*)$") { 
        [System.Environment]::SetEnvironmentVariable($Matches[1].Trim(),$Matches[2].Trim()) 
    } 
}

Write-Host "=== 2. サービスアカウントを組み立てます ===" -ForegroundColor Cyan
$SA_EMAIL = "power-fetcher-sa@$env:PROJECT_ID.iam.gserviceaccount.com"
Write-Host "Target SA: $SA_EMAIL"

Write-Host "=== 3. Cloud Workflows のデプロイを実行します ===" -ForegroundColor Cyan
gcloud workflows deploy $env:WORKFLOW_NAME `
    --source=workflow.yaml `
    --location=$env:REGION `
    --service-account=$SA_EMAIL `
    --env-vars-file=.env

Write-Host "=== デプロイが正常に完了しました！ ===" -ForegroundColor Green
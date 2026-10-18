import os
import subprocess
import sys

def load_dotenv(env_path=".env"):
    """
    .env ファイルを読み込んで環境変数に設定する関数（KEY: VALUE 形式に対応）
    """
    if not os.path.exists(env_path):
        print(f"エラー: {env_path} が見つかりません。")
        sys.exit(1)
        
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # 空行やコメント行はスキップ
            if not line or line.startswith("#"):
                continue
            # コロン (:) または ィールト区切りの = に対応させる場合
            if ":" in line:
                key, value = line.split(":", 1)
                os.environ[key.strip()] = value.strip()
            elif "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

def main():
    print("=== 1. .env から環境変数を読み込みます ===")
    load_dotenv()

    # 必要な環境変数の取得
    project_id = os.environ.get("PROJECT_ID")
    region = os.environ.get("REGION")
    workflow_name = os.environ.get("WORKFLOW_NAME")

    if not all([project_id, region, workflow_name]):
        print("エラー: .env に PROJECT_ID, REGION, WORKFLOW_NAME のいずれかが不足しています。")
        sys.exit(1)

    print("=== 2. サービスアカウントを組み立てます ===")
    sa_email = f"power-fetcher-sa@{project_id}.iam.gserviceaccount.com"
    print(f"Target SA: {sa_email}")

    print("=== 3. Cloud Workflows のデプロイを実行します ===")
    cmd = [
        "gcloud", "workflows", "deploy", workflow_name,
        "--source=workflow.yaml",
        f"--location={region}",
        f"--service-account={sa_email}",
        "--env-vars-file=.env"
    ]

    # コマンドを実行（エラーが発生した場合は例外をスローして停止）
    try:
        cmd_str = f"gcloud workflows deploy {workflow_name} --source=workflow.yaml --location={region} --service-account={sa_email} --env-vars-file=.env"
        subprocess.run(cmd_str, shell=True, check=True)
        print("=== デプロイが正常に完了しました！ ===")
    except subprocess.CalledProcessError as e:
        print(f"デプロイエラーが発生しました (終了コード: {e.returncode})")
        sys.exit(e.returncode)

if __name__ == "__main__":
    main()
import os
from pathlib import Path
import subprocess
import sys


def load_env():
    # ルートにある .env を読み込む想定 (power_csv_fetcher の一階層上)
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        # power_csv_fetcher フォルダ内にある場合のフォールバック
        env_path = Path(__file__).resolve().parent / ".env"

    if not env_path.exists():
        print(f"[Warn] .env file not found at: {env_path}")
        return

    print(f"=== 1. .env から環境変数を読み込みます ({env_path}) ===")
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                key, value = line.split(":", 1)
            elif "=" in line:
                key, value = line.split("=", 1)
            else:
                continue

            key = key.strip()
            value = value.strip()
            os.environ[key] = value


def main():
    load_env()

    project_id = os.environ.get("PROJECT_ID")
    region = os.environ.get("REGION")
    repo_name = os.environ.get("REPO_NAME")

    image_name = "power-csv-fetcher"
    tag = "latest"

    print(f"PROJECT_ID : {project_id}")
    print(f"REGION     : {region}")
    print(f"REPO_NAME  : {repo_name}")

    if not all([project_id, region, repo_name]):
        print(
            "[Error] 必要な環境変数が .env から取得できませんでした。", file=sys.stderr
        )
        sys.exit(1)

    print("=== 2. イメージURIを組み立てます ===")
    image_uri = (
        f"{region}-docker.pkg.dev/{project_id}/{repo_name}/{image_name}:{tag}"
    )
    print(f"Target Image: {image_uri}")

    # このスクリプトがあるディレクトリ（power_csv_fetcher）をビルドコンテキストにする
    current_dir = Path(__file__).resolve().parent

    print("=== 3. Cloud Build によるビルド＆登録を実行します ===")
    build_cmd = f"gcloud builds submit --tag {image_uri} {current_dir}"
    build_result = subprocess.run(build_cmd, shell=True)
    if build_result.returncode != 0:
        print("[Error] Cloud Build に失敗しました。", file=sys.stderr)
        sys.exit(build_result.returncode)

    print("=== 4. Cloud Run Jobs を作成・更新します ===")
    job_name = "power-csv-fetcher-job"
    sa_email = f"power-fetcher-sa@{project_id}.iam.gserviceaccount.com"

    # 既存のジョブを更新するコマンド
    update_cmd = (
        f"gcloud run jobs update {job_name} "
        f"--image={image_uri} "
        f"--region={region} "
        f"--service-account={sa_email} "
        "--task-timeout=300s "
        "--max-retries=2"
    )

    update_result = subprocess.run(update_cmd, shell=True)

    # ジョブがまだ存在しない場合は新規作成にフォールバック
    if update_result.returncode != 0:
        print("ジョブが存在しないため、新規作成します...", file=sys.stderr)
        create_cmd = (
            f"gcloud run jobs create {job_name} "
            f"--image={image_uri} "
            f"--region={region} "
            f"--service-account={sa_email} "
            "--task-timeout=300s "
            "--max-retries=2"
        )
        create_result = subprocess.run(create_cmd, shell=True)
        if create_result.returncode != 0:
            print("[Error] Cloud Run Job の作成に失敗しました。", file=sys.stderr)
            sys.exit(create_result.returncode)

    print("=== すべての処理が正常に完了しました！ ===")


if __name__ == "__main__":
    main()
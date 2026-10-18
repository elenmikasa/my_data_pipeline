from datetime import datetime, timedelta
from pathlib import Path
import sys
from urllib.parse import urlparse

import httpx
import yaml
from google.api_core.exceptions import GoogleAPIError
from google.auth.exceptions import GoogleAuthError
from google.cloud import storage


def main() -> int:
    """設定された各社の先月分CSVを、変換せずGCSバケット直下へ保存する。"""
    config_path = Path(__file__).parent / "config.yaml"
    with config_path.open(encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)

    try:
        storage_client = storage.Client()
    except GoogleAuthError as error:
        print(f"GCSの認証に失敗しました: {error}", file=sys.stderr)
        return 1

    bucket = storage_client.bucket(config["bucket_name"])

    now = datetime.now()
    first_day_of_this_month = now.replace(day=1)
    last_month = first_day_of_this_month - timedelta(days=1)
    yyyymm = last_month.strftime("%Y%m")

    failed = False

    with httpx.Client(follow_redirects=True) as client:
        for info in config["companies"].values():
            company_name = info["name"]
            url = info["url"].format(yyyymm=yyyymm)
            file_name = Path(urlparse(url).path).name

            try:
                response = client.get(url)
                response.raise_for_status()
            except httpx.HTTPError as error:
                print(
                    f"{company_name}: CSVの取得に失敗しました: {error}",
                    file=sys.stderr,
                )
                failed = True
                continue

            try:
                # upload_from_string()で、文字列またはバイト列のデータをGCSのBlobへアップロードする
                bucket.blob(file_name).upload_from_string(
                    response.content,
                    content_type="text/csv",
                )
            except (GoogleAPIError, GoogleAuthError) as error:
                print(
                    f"{company_name}: GCSへの保存に失敗しました: {error}",
                    file=sys.stderr,
                )
                failed = True
                continue

            print(
                f"{company_name}: 保存しました "
                f"gs://{config['bucket_name']}/{file_name}"
            )

    if failed:
        return 1

    print("すべてのCSVをGCSバケット直下に保存しました。")
    return 0


if __name__ == "__main__":
    # ファイルを直接実行したとき、main()を呼び出して戻り値を終了コードとして終了する
    raise SystemExit(main())

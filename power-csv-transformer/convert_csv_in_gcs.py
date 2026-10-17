import logging
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

import yaml
from google.api_core.exceptions import GoogleAPIError
from google.auth.exceptions import GoogleAuthError
from google.cloud import storage


logging.basicConfig(level=logging.INFO, format="%(message)s")


def main() -> int:
    """GCSバケット直下の先月分CSVを変換し、共通フォルダーへ保存する。"""
    config_path = Path(__file__).parent / "config.yaml"
    with config_path.open(encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)

    try:
        storage_client = storage.Client()
    except GoogleAuthError as error:
        logging.error(f"GCSの認証に失敗しました: {error}")
        return 1

    bucket = storage_client.bucket(config["bucket_name"])

    now = datetime.now()
    first_day_of_this_month = now.replace(day=1)
    last_month = first_day_of_this_month - timedelta(days=1)
    yyyymm = last_month.strftime("%Y%m")
    header_mapping = config["header_mapping"]
    failed = False

    for info in config["companies"].values():
        company_name = info["name"]
        url = info["url"].format(yyyymm=yyyymm)
        source_file_name = Path(urlparse(url).path).name

        try:
            # バケット内の指定ファイルを操作するためのBlobオブジェクトを取得
            source_blob = bucket.blob(source_file_name)
            # GCS上のCSVファイルをダウンロードし、内容をバイト列として変数に格納
            raw_data = source_blob.download_as_bytes()

            try:
                # バイト列をCP932でデコードし、文字列として格納
                text_content = raw_data.decode("cp932")
            except UnicodeDecodeError:
                # バイト列をUTF-8でデコードし、文字列として格納
                text_content = raw_data.decode("utf-8", errors="ignore")

            # テキストを行ごとに分割し、先頭行（ヘッダー）を除いた2行目以降を取得
            lines = text_content.splitlines()[1:]
            if len(lines) < 2:
                raise ValueError("CSVファイルの行数が不足しています。")

            columns = [column.strip() for column in lines[0].split(",")]
            converted_columns = []
            known_column_indices = []
            unknown_columns = []

            # カラム名とその位置（インデックス）を取り出して順に処理
            for index, column in enumerate(columns):
                if column in header_mapping:
                    # 登録済みカラムの位置を記録し、後続でデータ行から対応する値を取り出せるようにする
                    known_column_indices.append(index)
                    converted_columns.append(header_mapping[column])
                else:
                    unknown_columns.append(column)

            # 変換後のカラム名をカンマで連結し、CSVのヘッダー行としてリストに格納
            processed_lines = [",".join(converted_columns)]
            for line in lines[1:]:
                values = line.split(",")
                if len(values) < len(columns):
                    raise ValueError(
                        "データ行の列数がヘッダーの列数より少ない行があります。"
                    )
                # 登録済みカラムの値のみを抽出し、カンマで連結
                processed_lines.append(
                    ",".join(values[index] for index in known_column_indices)
                )

            # processed_linesはリストなので改行で結合してCSVテキストを作成し、末尾に改行を追加
            processed_text = "\n".join(processed_lines) + "\n"
            converted_file_name = (
                source_file_name.replace(yyyymm, "last_month")
                .replace(".csv", "_converted_header.csv")
            )
            destination_path = (
                f"{config['common_folder']}/{converted_file_name}"
            )
            # 保存先パスのGCSオブジェクト（Blob）を取得
            # GCS上に実ファイルがなくても、保存先パスを指定したBlobオブジェクトを作成できる
            bucket.blob(destination_path).upload_from_string(
                processed_text.encode("utf-8"),
                content_type="text/csv; charset=utf-8",
            )
        except (GoogleAPIError, GoogleAuthError, ValueError, IndexError) as error:
            logging.error(
                f"{company_name}: CSVの変換またはGCSへの保存に失敗しました: "
                f"{error}"
            )
            failed = True
            continue

        logging.info(
            f"{company_name}: 保存しました "
            f"gs://{config['bucket_name']}/{destination_path}"
        )
        if unknown_columns:
            logging.warning(
                f"{company_name}: 未登録のカラムを除外しました: "
                f"{unknown_columns}"
            )

    if failed:
        return 1

    logging.info("すべてのCSVを変換して共通フォルダーへ保存しました。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

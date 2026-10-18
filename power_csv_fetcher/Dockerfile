# 軽量なPython公式イメージを使用
FROM python:3.11-slim

# 作業ディレクトリの設定
WORKDIR /app

# 依存関係ファイルのコピーとインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# スクリプトと設定ファイルをコンテナにコピー
COPY upload_csv_to_gcs.py .
COPY config.yaml .

# コンテナ起動時にスクリプトを実行
CMD ["python", "upload_csv_to_gcs.py"]
# 軽量なPython公式イメージを使用
FROM python:3.11-slim

# 作業ディレクトリの設定
WORKDIR /app

# 依存関係ファイルのコピーとインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# スクリプトと設定ファイルをコンテナにコピー
COPY convert_csv_in_gcs.py .
COPY config.yaml .

# コンテナ起動時にスクリプトを実行
CMD ["python", "convert_csv_in_gcs.py"]
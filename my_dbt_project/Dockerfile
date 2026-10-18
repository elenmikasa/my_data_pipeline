FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir dbt-bigquery

# ファイルをすべてコピー
COPY . .

# ★ここで dbt のパッケージをインストールするコマンドを追加
RUN dbt deps

CMD ["dbt", "build"]
# ★ここがポイント：dbtを実行する代わりに、/app の中身をログに表示して強制終了する
# CMD ["sh", "-c", "echo '=== /app フォルダの中身一覧 ===' && ls -la /app && exit 1"]
#!/usr/bin/env bash
# 使用 apps/api/ssl 目录下的证书启动 HTTPS（端口 3000，供 frp 转发到远程 443）
cd "$(dirname "$0")"
CERT=ssl/zephyr-s.online_bundle.crt
KEY=ssl/zephyr-s.online.key
if [[ ! -f $CERT ]]; then
  CERT=ssl/zephyr-s.online_bundle.pem
fi
if [[ ! -f $CERT ]] || [[ ! -f $KEY ]]; then
  echo "请将证书放在 ssl/ 目录：证书链（.crt 或 .pem）和私钥（.key）"
  exit 1
fi
source .venv/bin/activate 2>/dev/null || true
exec python -m uvicorn app.main:app --host 127.0.0.1 --port 3000 \
  --ssl-keyfile="$KEY" \
  --ssl-certfile="$CERT"

#!/usr/bin/env bash
set -e

# (선택) 캐시/데이터 디렉토리 생성
mkdir -p /app/data/cache

exec "$@"

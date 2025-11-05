FROM python:3.11-slim

# 시스템 패키지 (Playwright/Chromium 의존)
RUN apt-get update && apt-get install -y \
    wget curl git build-essential libglib2.0-0 libnss3 libatk1.0-0 libatk-bridge2.0-0 \
    libdrm2 libxkbcommon0 libgbm1 libasound2 libx11-xcb1 libxcomposite1 libxdamage1 \
    libxrandr2 libxfixes3 libpango-1.0-0 libcairo2 libjpeg62-turbo \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 파이썬 의존성
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Playwright + Chromium
RUN python -m playwright install --with-deps chromium

# 앱 소스
COPY src /app/src
ENV PYTHONPATH=/app/src

# 런타임 준비
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

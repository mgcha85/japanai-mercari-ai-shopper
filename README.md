좋아요 👍
아래는 `README.md`와 `requirements.txt`의 **초기 완성본**이야.
버전은 모두 제거했고, `mercari-ai-shopper`의 구조 및 목적을 기준으로 작성했어.
PowerShell 명령어로 자동 작성할 수 있게끔 `Set-Content`를 같이 포함했어.

---

## ✅ PowerShell 명령어

아래를 `mercari-ai-shopper` 폴더 내부에서 실행하세요 👇

```powershell
# --- README.md 생성 ---
$readme = @"
# 🛍️ Mercari AI Shopper

**Mercari Japan AI Shopper** is a Python-based intelligent agent that:
1. Understands natural language shopping requests (Korean/English/Japanese)
2. Searches effectively on **Mercari Japan**
3. Extracts and ranks the most relevant product listings
4. Explains the reasoning behind its top 3 recommendations

---

## 🚀 Features
- **LLM Tool-Calling Agent** (OpenAI Function Calling / Anthropic Tool Use)
- **Web Scraper** for Mercari (Requests + BeautifulSoup, Playwright fallback)
- **Multi-language input support** (Korean → Japanese keyword translation)
- **Explainable Recommendations** (price fit, item condition, brand match, etc.)
- **Containerized environment** (Docker + docker-compose)

---

## 🧩 Project Structure

```

mercari-ai-shopper/
├─ docker/               # Dockerfile, compose definitions
├─ scripts/              # CLI/test scripts
├─ src/
│  └─ mercari_ai_shopper/
│     ├─ agent/          # LLM agent, tool schema, reasoning
│     ├─ llm/            # OpenAI / Anthropic clients
│     ├─ scraping/       # Mercari scraping & parsing logic
│     ├─ models/         # Pydantic schemas (query, listing, recommendation)
│     └─ utils/          # HTTP, logging, text normalization
└─ tests/                # Unit, integration, e2e tests

````

---

## ⚙️ Setup Instructions

### 1️⃣ Clone & Build

```bash
git clone https://github.com/yourname/mercari-ai-shopper.git
cd mercari-ai-shopper
cp .env.example .env
````

Add your API key to `.env`:

```
OPENAI_API_KEY=sk-xxxx
# or
ANTHROPIC_API_KEY=sk-ant-xxxx
```

### 2️⃣ Build and Run Containers

```bash
cd docker
docker compose up --build -d api
```

Server will start at:

```
http://localhost:8000/docs
```

To run CLI mode:

```bash
docker compose run --rm cli --query "닌텐도 스위치 OLED 화이트 30000엔 이하"
```

To run tests:

```bash
docker compose run --rm tests
```

---

## 🧠 Design Choices

| Component            | Technology                                     | Purpose                              |
| -------------------- | ---------------------------------------------- | ------------------------------------ |
| **LLM**              | OpenAI or Anthropic                            | Natural language → structured search |
| **Scraper**          | Requests + BeautifulSoup + Playwright fallback | Reliable data extraction             |
| **Schema**           | Pydantic                                       | Type-safe request/result validation  |
| **Server**           | FastAPI + Uvicorn                              | Tool-calling & REST API              |
| **Containerization** | Docker Compose                                 | Unified dev/test/prod environment    |
| **Retry/Cache**      | Tenacity + requests-cache                      | Rate limit and duplicate protection  |

---

## 🧪 Example Output

Example CLI result:

```
Top 3 recommendations for '닌텐도 스위치 OLED 화이트 30000엔 이하':

1️⃣ Nintendo Switch OLED White - ¥29,800
   - Condition: 未使用に近い
   - Reason: Within budget, near-new condition, exact color match
   - URL: https://jp.mercari.com/item/xxxxxxxx

2️⃣ Nintendo Switch OLED White - ¥28,500
   - Condition: 目立った傷や汚れなし
   - Reason: Lower price, slightly used, same model
```

---

## 💡 Potential Improvements

* Incorporate seller reliability and transaction count
* Add Redis cache for cross-session deduplication
* Visualize price distributions per keyword
* Integrate optional vision model for image quality filtering
* Conversation memory for multi-turn shopping sessions

---

## 🤖 Agent Mode (LLM Tool-Calling)

이 프로젝트는 **LLM 에이전트 모드**를 통해 사용자 자연어 → 구조화 검색 → 추천을 자동화할 수 있습니다.  
OpenAI 또는 Anthropic 중 하나를 선택해 사용할 수 있습니다.

### 1) 환경 변수 설정
`.env` 파일에서 LLM 제공자를 선택하고 키를 설정하세요.

---

## 🧾 License

MIT License © 2025 Mingyu Cha
"@
Set-Content -Path "README.md" -Value $readme -Encoding UTF8


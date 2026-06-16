# 🎬 YANK (YouTube And Kut)

유튜브 영상을 다운로드하고 타임스탬프 기준으로 자르는 Streamlit 앱입니다.
**하나의 코드(`app.py`)와 하나의 런처(`run.py`)로 Windows · macOS · Linux 모두에서 동작합니다.**

```
yank/
├── app.py              ← 공용 앱 (크로스플랫폼)
├── run.py              ← 로컬 실행 런처 (모든 OS 공통)
├── requirements.txt    ← 의존성 목록
├── ffmpeg.exe          ← Windows 전용 (Win에서만 사용)
├── ffprobe.exe         ← Windows 전용 (Win에서만 사용)
├── Dockerfile          ← 컨테이너 이미지 정의
├── docker-compose.yml  ← 시놀로지/클라우드 배포용
├── .dockerignore
└── .streamlit/
    └── config.toml     ← 서버/헤드리스 설정
```

`run.py`가 실행 시 OS를 감지해서:
- 의존성(streamlit, yt-dlp, pyperclip)을 자동 설치하고
- Windows면 동봉된 `ffmpeg.exe`, macOS/Linux면 시스템에 설치된 ffmpeg를 사용합니다.

---

## ▶️ 실행 방법 (모든 OS 공통)

```bash
# Windows
python run.py

# macOS / Linux
python3 run.py
```

이 한 줄이면 끝입니다. 처음 실행할 때만 의존성 설치로 잠시 시간이 걸립니다.

---

## 사전 준비

**Windows**
- Python만 설치되어 있으면 됩니다. ffmpeg는 폴더에 동봉되어 있습니다.

**macOS / Linux**
- ffmpeg를 먼저 설치하세요.
  ```bash
  # macOS
  brew install ffmpeg
  # Linux (Debian/Ubuntu)
  sudo apt install ffmpeg
  ```

---

## 📦 의존성

- streamlit
- yt-dlp
- pyperclip
- ffmpeg (Windows: 동봉 / macOS·Linux: 직접 설치)

> 참고: 더블클릭 한 번으로 실행되는 단일 실행 파일은 OS마다 형식(.bat / .command)이 달라
> 진짜 "파일 하나"로 만들 수 없습니다. 대신 모든 OS에서 공통으로 쓰는 `python run.py`로 통일했습니다.

---

## 🐳 Docker로 띄우기 (시놀로지 / 클라우드)

리눅스 컨테이너에서는 ffmpeg가 이미지 안에 자동 설치되며(`apt`), Windows용
`ffmpeg.exe`는 사용하지 않습니다(`.dockerignore`로 제외).

### 1) docker compose (권장)
```bash
docker compose up -d --build
```
- 접속: `http://<호스트IP>:8501`
- 다운로드 결과: 프로젝트 폴더의 `./downloads` 에 저장됨 (컨테이너 `/downloads`와 매핑)

### 2) docker 명령으로 직접
```bash
docker build -t yank:latest .
docker run -d --name yank \
  -p 8501:8501 \
  -v "$(pwd)/downloads:/downloads" \
  -e DOWNLOAD_DIR=/downloads \
  --restart unless-stopped \
  yank:latest
```

### 3) 시놀로지 NAS (Container Manager)
1. 이 폴더를 NAS에 업로드 (예: `/volume1/docker/yank`)
2. Container Manager → **프로젝트 생성** → 경로를 위 폴더로 지정 → `docker-compose.yml` 인식
3. 빌드/실행 후 `http://<NAS-IP>:8501` 접속
4. 다운로드 폴더는 `docker-compose.yml`의 volume을 NAS 공유폴더로 바꾸면 됩니다.
   예: `- /volume1/Downloads:/downloads`

### 컨테이너 환경 참고사항
- **저장 폴더 경로**는 앱 화면에서 반드시 `/downloads`(또는 매핑한 컨테이너 내부 경로)로 입력하세요.
  호스트의 `C:\...` 나 `/Users/...` 경로는 컨테이너 안에서 보이지 않습니다.
- **"📂 폴더 열기" 버튼**은 데스크톱 전용 기능이라 서버/컨테이너 모드에서는 동작하지 않습니다.
  매핑한 호스트 폴더(`./downloads`)에서 직접 결과물을 확인하세요.
- **포트 변경**: `docker-compose.yml`의 `"8501:8501"`에서 앞 숫자(호스트 포트)만 바꾸면 됩니다.

### 환경변수
| 변수 | 기본값 | 설명 |
|---|---|---|
| `DOWNLOAD_DIR` | `/downloads` | 앱의 기본 저장 폴더 경로 |

---

## 🚀 GitHub Actions로 이미지 자동 배포 (yml 하나로 실행)

`main` 브랜치에 push하면 GitHub Actions가 이미지를 빌드해
**GHCR(GitHub Container Registry)** 에 자동으로 올립니다:
`ghcr.io/n8ki3/yank:latest`

이후 시놀로지/서버에는 **`docker-compose.deploy.yml` 하나만** 두면 됩니다.

```bash
docker compose -f docker-compose.deploy.yml up -d
```

### 최초 1회 설정 (GHCR 패키지 공개)
1. GitHub 레포 push → Actions 탭에서 빌드 성공 확인
2. 레포 우측 **Packages** → `yank` 패키지 → **Package settings**
3. **Danger Zone → Change visibility → Public** 으로 변경
   (Private으로 두면 pull 시 `docker login ghcr.io` 인증 필요)

### 이미지 직접 받아서 실행 (compose 없이)
```bash
docker run -d --name yank \
  -p 8501:8501 \
  -v "$(pwd)/downloads:/downloads" \
  --restart unless-stopped \
  ghcr.io/n8ki3/yank:latest
```


# 🎬 YANK (YouTube And Kut)

유튜브 영상을 다운로드하고 타임스탬프 기준으로 자르는 Streamlit 앱입니다.
**하나의 코드(`app.py`)와 하나의 런처(`run.py`)로 Windows · macOS · Linux 모두에서 동작합니다.**

## ✨ 주요 기능

**⬇️ 다운로드 탭**
- 유튜브 영상 다운로드 (최고화질 / 1080p / 720p / MP3, AVC1·H.264 우선)
- 안전 모드: 다운로드 후 프리미어 호환용 재인코딩
- 받은 파일 메타데이터에 **원본 유튜브 주소를 자동 저장** (나중에 자동 챕터 로드에 사용)

**✂️ 자르기 탭**
- 폴더를 스캔해 **하위 폴더까지 계층(폴더→파일)으로 영상 선택**
- 타임스탬프 기준으로 구간 분할 (정밀 자르기/재인코딩으로 정확히 컷)
- **🔗 유튜브 URL에서 챕터 자동 불러오기** — URL만 넣으면 타임스탬프 칸 자동 채움
- **📌 파일 선택 시 자동 로드** — 이 앱으로 받은 영상은 저장된 주소에서 챕터를 자동으로 불러옴
- 작업 완료 시 화면 배너 + 토스트 알림

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

## ✂️ 자르기 / 타임스탬프 형식

타임스탬프 칸에 **한 줄에 하나씩 `시간 제목`** 형태로 입력합니다. 각 줄의 시간이 그 구간의 **시작점**이고, **다음 줄 시간까지**가 한 조각, 마지막 줄은 **영상 끝까지**입니다.

```
0:00 오프닝
1:12 게스트 소개
8:40 본격 토크
25:30 Q&A
42:15 클로징
```
→ 5개 파일(`01_오프닝.mp4` … `05_클로징.mp4`)로 잘립니다.

- 시간 형식: `분:초`(예 `2:30`) 또는 `시:분:초`(예 `1:05:20`)
- `0:00 - 제목`, `[0:00] 제목`, `1. 0:00 제목` 같은 변형도 인식
- 제목을 안 적으면 `NoTitle`로 저장
- 결과는 원본 옆 `(파일명)_편집본` 폴더에 저장

**특정 구간만 받기**: 시작 줄만 적으면 그 지점부터 끝까지 잘립니다. 끝 지점을 한 줄 더 적으면 그 사이만 잘리고, 뒤쪽 자투리 파일은 지우면 됩니다.

```
11:35 LOVE ATTACK 역주행 기우제   ← 11:35 ~ 끝
```

> 자르기는 정확도를 위해 항상 **정밀(재인코딩)** 모드로 동작합니다.

---

## 📦 의존성

- streamlit
- yt-dlp
- pyperclip
- ffmpeg / ffprobe (Windows: 동봉 / macOS·Linux: 직접 설치)

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


import streamlit as st
import yt_dlp
import os
import sys
import shutil
import platform
import subprocess
import re

try:
    import pyperclip
except Exception:
    pyperclip = None

# ──────── 플랫폼 유틸 ────────
IS_WINDOWS = platform.system() == "Windows"
IS_MAC = platform.system() == "Darwin"


def subprocess_flags():
    """Windows에서만 콘솔 창 숨김 플래그를 적용한다."""
    if IS_WINDOWS and hasattr(subprocess, "CREATE_NO_WINDOW"):
        return {"creationflags": subprocess.CREATE_NO_WINDOW}
    return {}

# ──────── 기본 설정 ────────
st.set_page_config(page_title="YANK - YouTube And Kut", page_icon="🎬", layout="wide")

# ──────── 세션 상태 초기화 ────────
if 'url_input' not in st.session_state: st.session_state.url_input = ""
if 'last_save_path' not in st.session_state: st.session_state.last_save_path = ""
if 'is_processing' not in st.session_state: st.session_state.is_processing = False

# ──────── 함수 ────────
def get_ffmpeg_path():
    # 1) 동봉된 Windows 바이너리 (Windows 실행 시)
    local_exe = os.path.join(os.getcwd(), 'ffmpeg.exe')
    if IS_WINDOWS and os.path.exists(local_exe):
        return local_exe
    # 2) 동봉된 실행 파일(확장자 없는 경우)
    local_bin = os.path.join(os.getcwd(), 'ffmpeg')
    if os.path.exists(local_bin):
        return local_bin
    # 3) 시스템 PATH에서 탐색 (mac/Linux: brew, apt 등)
    found = shutil.which('ffmpeg')
    if found:
        return found
    # 4) 최종 폴백
    return 'ffmpeg'


def open_folder(path):
    norm_path = os.path.normpath(path)
    if not os.path.exists(norm_path):
        st.error(f"폴더 오류: {norm_path}")
        return
    try:
        if IS_WINDOWS:
            os.startfile(norm_path)  # type: ignore[attr-defined]
        elif IS_MAC:
            subprocess.run(['open', norm_path], check=False)
        else:
            subprocess.run(['xdg-open', norm_path], check=False)
    except Exception as e:
        st.error(f"폴더를 열 수 없습니다: {e}")


def paste_to_url():
    if pyperclip is None:
        st.warning("클립보드 기능(pyperclip)을 사용할 수 없습니다. 주소를 직접 붙여넣어 주세요.")
        return
    try:
        text = pyperclip.paste().strip()
        if text: st.session_state.url_input = text
    except Exception:
        pass

def parse_time(t):
    try:
        parts = list(map(int, t.split(':')))
        if len(parts) == 3: return parts[0]*3600 + parts[1]*60 + parts[2]
        elif len(parts) == 2: return parts[0]*60 + parts[1]
    except: return 0
    return 0

VIDEO_EXTS = ('.mp4', '.mkv', '.mov', '.avi', '.webm', '.flv', '.m4v', '.ts', '.wmv', '.mpg', '.mpeg')

def list_video_files(folder, limit=500):
    """폴더(하위 폴더 포함)를 스캔해 영상 파일의 상대경로 목록을 반환한다."""
    results = []
    if not folder or not os.path.isdir(folder):
        return results
    try:
        for root, _dirs, files in os.walk(folder):
            for name in files:
                if name.lower().endswith(VIDEO_EXTS):
                    full = os.path.join(root, name)
                    results.append(os.path.relpath(full, folder))
                    if len(results) >= limit:
                        return sorted(results)
    except Exception:
        pass
    return sorted(results)

# ──────── UI ────────
st.title("🎬 YANK : YouTube And Kut")

tab1, tab2 = st.tabs(["⬇️ 다운로드", "✂️ 자르기"])

# ──────── [탭1] 다운로드 ────────
with tab1:
    st.header("유튜브 영상 다운로드")
    
    col_input, col_btn = st.columns([5, 1])
    with col_input:
        url = st.text_input("유튜브 주소", key="url_input", disabled=st.session_state.is_processing)
    with col_btn:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        st.button("📋 붙여넣기", on_click=paste_to_url, use_container_width=True, disabled=st.session_state.is_processing)

    default_dir = os.environ.get("DOWNLOAD_DIR") or os.path.join(os.path.expanduser("~"), "Downloads")
    save_path = st.text_input("저장 폴더", value=default_dir, disabled=st.session_state.is_processing)
    
    st.write("---")
    quality = st.radio(
        "화질 선택",
        ["최고화질 (AVC1/H.264)", "1080p (AVC1/H.264)", "720p (AVC1/H.264)", "MP3"],
        horizontal=True,
        disabled=st.session_state.is_processing
    )
    
    force_safe = st.checkbox("🛡️ 안전 모드 (다운 후 프리미어 최적화 재인코딩)", 
                             value=False, 
                             disabled=st.session_state.is_processing,
                             help="체크 시 다운로드 후 재인코딩을 수행합니다.")

    col_run, col_open = st.columns([1, 1])
    
    with col_run:
        # 버튼 잠금 로직 적용
        if st.button("🚀 다운로드 시작", type="primary", use_container_width=True, disabled=st.session_state.is_processing):
            if not url:
                st.warning("주소를 입력하세요.")
            else:
                st.session_state.is_processing = True
                st.rerun()

    # 실제 다운로드 실행
    if st.session_state.is_processing and url:
        ffmpeg_path = get_ffmpeg_path()
        status = st.empty()
        pbar = st.progress(0)
        
        try:
            def progress_hook(d):
                if d['status'] == 'downloading':
                    try:
                        total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                        downloaded = d.get('downloaded_bytes', 0)
                        if total > 0:
                            p = downloaded / total
                            pbar.progress(min(p, 1.0))
                    except: pass
                    status.info(f"📥 다운로드 중... (다른 버튼 금지)")
                elif d['status'] == 'finished':
                    status.info("✅ 다운로드 완료! 변환 대기 중...")

            ydl_opts = {
                'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),
                'progress_hooks': [progress_hook],
                'nocheckcertificate': True,
                'ffmpeg_location': ffmpeg_path,
                'merge_output_format': 'mp4',
                'continuedl': True,
                'overwrites': True,
                'postprocessors': [{'key': 'FFmpegMetadata', 'add_metadata': False}], 
            }
            
            if "최고화질" in quality:
                ydl_opts['format'] = 'bestvideo[vcodec^=avc1]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            elif "720p" in quality:
                ydl_opts['format'] = 'bestvideo[height<=720][vcodec^=avc1]+bestaudio[ext=m4a]/best'
            elif "MP3" in quality:
                ydl_opts['format'] = 'bestaudio'
                ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}]

            status.info("🚀 작업 시작...")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                final_filename = os.path.splitext(filename)[0] + ".mp4"
            
            if force_safe and "MP3" not in quality:
                status.info("🛡️ 안전 모드: 재인코딩 중... (절대 끄지 마세요)")
                temp_name = final_filename.replace(".mp4", "_temp_enc.mp4")
                if os.path.exists(temp_name): os.remove(temp_name)
                    
                cmd = [
                    ffmpeg_path, '-y', '-i', final_filename, 
                    '-c:v', 'libx264', '-preset', 'superfast', '-crf', '23',
                    '-c:a', 'aac', '-b:a', '192k', temp_name
                ]
                subprocess.run(cmd, check=True, **subprocess_flags())
                os.replace(temp_name, final_filename)

            pbar.progress(100)
            status.success("🎉 작업 완료!")
            st.session_state.last_save_path = save_path
            
        except Exception as e:
            st.error(f"오류: {e}")
        finally:
            st.session_state.is_processing = False
            st.rerun()

    with col_open:
        target = st.session_state.last_save_path if st.session_state.last_save_path else save_path
        # 작업 중엔 비활성화
        if st.button("📂 폴더 열기", use_container_width=True, disabled=st.session_state.is_processing):
            open_folder(target)

# ──────── [탭2] 자르기 ────────
with tab2:
    st.header("타임스탬프 자르기")

    scan_dir = st.text_input(
        "📁 검색 폴더",
        value=default_dir,
        disabled=st.session_state.is_processing,
        help="이 폴더(하위 폴더 포함)를 읽어 영상 파일을 목록으로 보여줍니다.",
    )

    video_files = list_video_files(scan_dir)
    video_path = ""

    if video_files:
        # 하위 폴더(계층)별로 그룹화 → 폴더 먼저 선택, 그 안의 파일 선택
        folders = sorted({os.path.dirname(f) for f in video_files})
        folder_labels = ["[전체 보기]"] + [
            ("📁 " + (fd if fd else "(최상위 폴더)")) for fd in folders
        ]
        # 라벨 → 실제 폴더값 매핑 ('' 는 최상위)
        label_to_folder = {folder_labels[0]: None}
        for lbl, fd in zip(folder_labels[1:], folders):
            label_to_folder[lbl] = fd

        chosen_label = st.selectbox(
            f"📂 폴더 선택 ({len(folders)}개 폴더 / 영상 {len(video_files)}개)",
            options=folder_labels,
            disabled=st.session_state.is_processing,
        )
        chosen_folder = label_to_folder.get(chosen_label)

        if chosen_folder is None:
            # 전체 보기: 계층이 드러나도록 상대경로 그대로 표시
            file_options = video_files
        else:
            file_options = [f for f in video_files if os.path.dirname(f) == chosen_folder]

        selected = st.selectbox(
            f"🎞️ 영상 파일 선택 ({len(file_options)}개)",
            options=file_options,
            # 폴더를 고른 경우엔 파일명만, 전체 보기면 상대경로 전체를 보여줌
            format_func=(lambda p: p if chosen_folder is None else os.path.basename(p)),
            disabled=st.session_state.is_processing,
        )
        if selected:
            video_path = os.path.join(scan_dir, selected)
    else:
        st.info("해당 폴더에서 영상 파일을 찾지 못했습니다. 폴더 경로를 확인하거나 아래에 전체 경로를 직접 입력하세요.")

    manual_path = st.text_input(
        "또는 전체 경로 직접 입력 (선택)",
        disabled=st.session_state.is_processing,
        help="목록에 없는 파일은 전체 경로를 직접 입력하세요. 입력 시 위 선택보다 우선합니다.",
    )
    if manual_path.strip():
        video_path = manual_path.strip()

    if video_path:
        st.caption(f"대상 파일: `{video_path}`")

    col_t1, col_t2 = st.columns([3, 1])
    with col_t1: timestamps = st.text_area("타임스탬프", height=200, disabled=st.session_state.is_processing)
    with col_t2: 
        st.write("#### 설정")
        fast_mode = st.checkbox("⚡ 단순 자르기", value=False, disabled=st.session_state.is_processing)
        
    if st.button("✂️ 자르기 실행", type="primary", disabled=st.session_state.is_processing):
        if not video_path or not timestamps:
            st.error("파일과 타임스탬프를 확인하세요.")
        elif not os.path.exists(video_path):
            st.error(f"파일을 찾을 수 없습니다: {video_path}")
        else:
            st.session_state.is_processing = True
            st.rerun()

    if st.session_state.is_processing and video_path and timestamps:
        ffmpeg_exe = get_ffmpeg_path()
        lines = [l.strip() for l in timestamps.split('\n') if l.strip()]
        segments = []
        pattern = re.compile(r'(?:\[|\(|^)?(\d{1,2}:\d{2}(?::\d{2})?)(?:\]|\)|:|-)?\s*(.*)')
        
        try:
            for line in lines:
                m = pattern.search(line)
                if m:
                    clean_name = re.sub(r'[<>:"/\\|?*]', '_', re.sub(r'^[-: ]+', '', m.group(2)).strip()) or "NoTitle"
                    segments.append((parse_time(m.group(1)), clean_name))
            
            if segments:
                folder = os.path.dirname(video_path)
                save_dir = os.path.join(folder, f"{os.path.splitext(os.path.basename(video_path))[0]}_편집본")
                os.makedirs(save_dir, exist_ok=True)
                bar = st.progress(0)
                
                for i, (sec, title) in enumerate(segments):
                    out = os.path.join(save_dir, f"{i+1:02d}_{title}.mp4")
                    cmd = [ffmpeg_exe, '-y', '-ss', str(sec), '-i', video_path]
                    if i < len(segments)-1: cmd += ['-t', str(segments[i+1][0]-sec)]
                    
                    if fast_mode: cmd += ['-c', 'copy', '-avoid_negative_ts', 'make_zero', out]
                    else: cmd += ['-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '23', '-c:a', 'aac', out]
                    
                    subprocess.run(cmd, check=True, **subprocess_flags())
                    bar.progress((i+1)/len(segments))
                
                st.success("자르기 완료!")
                st.session_state.last_save_path = save_dir 
        except Exception as e:
            st.error(f"오류: {e}")
        finally:
            st.session_state.is_processing = False
            st.rerun()
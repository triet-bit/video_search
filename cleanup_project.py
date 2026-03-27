"""
cleanup_project.py — Dọn dẹp cấu trúc project
Chạy: python cleanup_project.py            # dry-run, chỉ xem thay đổi
       python cleanup_project.py --apply   # thực thi thật
"""

import os
import sys
import shutil
from pathlib import Path

DRY_RUN = "--apply" not in sys.argv
ROOT = Path(__file__).parent  # chạy script từ thư mục gốc project

# ─── Màu terminal ────────────────────────────────────────────────────────────
G = "\033[92m"   # xanh lá
Y = "\033[93m"   # vàng
R = "\033[91m"   # đỏ
B = "\033[94m"   # xanh dương
RESET = "\033[0m"
BOLD = "\033[1m"

def log(symbol, color, msg):
    prefix = f"  {'[DRY]' if DRY_RUN else '     '} {color}{symbol}{RESET}"
    print(f"{prefix}  {msg}")

def move(src: Path, dst: Path):
    if not src.exists():
        log("⚠", Y, f"Không tìm thấy: {src.relative_to(ROOT)}")
        return
    log("→", B, f"{src.relative_to(ROOT)}  →  {dst.relative_to(ROOT)}")
    if not DRY_RUN:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))

def rename(src: Path, new_name: str):
    dst = src.parent / new_name
    if not src.exists():
        log("⚠", Y, f"Không tìm thấy: {src.relative_to(ROOT)}")
        return
    log("✎", B, f"{src.relative_to(ROOT)}  →  {new_name}")
    if not DRY_RUN:
        src.rename(dst)

def delete(path: Path):
    if not path.exists():
        log("⚠", Y, f"Không tìm thấy: {path.relative_to(ROOT)}")
        return
    log("✕", R, f"{path.relative_to(ROOT)}")
    if not DRY_RUN:
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()

def write_file(path: Path, content: str, label: str):
    log("✚", G, f"{path.relative_to(ROOT)}  [{label}]")
    if not DRY_RUN:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

# ─── .gitignore ──────────────────────────────────────────────────────────────
GITIGNORE = """\
# Python
venv/
__pycache__/
*.py[cod]
*.pyo
.env
.env.*
!.env.example

# Data / index files (tuỳ chọn — bỏ comment nếu không muốn commit)
# data/faiss_index.bin
# data/metadata.json

# Misc
ngrok.txt
tree.txt
tree_clean.txt
*.log
.DS_Store
Thumbs.db

# Node
node_modules/
frontend/dist/
frontend/.env
frontend/.env.*
!frontend/.env.example
"""

ENV_EXAMPLE = """\
# ── App ──────────────────────────────────────
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=false

# ── Database ─────────────────────────────────
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=mydb

QDRANT_HOST=localhost
QDRANT_PORT=6333

# ── Models ───────────────────────────────────
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
LLM_MODEL=gpt-4o
RERANKING_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2

# ── Search ───────────────────────────────────
TOP_K=10
SCORE_THRESHOLD=0.5
"""

# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    mode = f"{R}DRY-RUN (chỉ xem){RESET}" if DRY_RUN else f"{G}APPLY (thực thi thật){RESET}"
    print(f"\n{BOLD}{'='*58}{RESET}")
    print(f"  cleanup_project.py — chế độ: {mode}")
    print(f"  ROOT: {ROOT}")
    print(f"{BOLD}{'='*58}{RESET}\n")

    # ── 1. Di chuyển file về đúng chỗ ─────────────────────────────────────
    print(f"{BOLD}[1] Di chuyển file{RESET}")
    move(ROOT / "init_db.py",      ROOT / "scripts" / "init_db.py")
    move(ROOT / "vectordb.py",     ROOT / "scripts" / "vectordb.py")
    move(ROOT / "testing_api.py",  ROOT / "tests" / "test_api.py")

    # ── 2. Sửa typo ────────────────────────────────────────────────────────
    print(f"\n{BOLD}[2] Sửa typo tên file{RESET}")
    rename(ROOT / "src" / "utils" / "hepler.py",         "helper.py")
    rename(ROOT / "src" / "search" / "trake_search.py",  "track_search.py")

    # ── 3. Xoá file rác ────────────────────────────────────────────────────
    print(f"\n{BOLD}[3] Xoá file rác{RESET}")
    delete(ROOT / "ngrok.txt")
    delete(ROOT / "tree.txt")
    delete(ROOT / "tree_clean.txt")

    # ── 4. Dọn placeholder Vite trong frontend ─────────────────────────────
    print(f"\n{BOLD}[4] Xoá placeholder Vite{RESET}")
    delete(ROOT / "frontend" / "public" / "icons" / "vite.svg")
    delete(ROOT / "frontend" / "public" / "videos" / "vite.svg")
    # Nếu folder rỗng sau khi xoá, xoá luôn folder
    for folder in [
        ROOT / "frontend" / "public" / "icons",
        ROOT / "frontend" / "public" / "videos",
    ]:
        if not DRY_RUN and folder.exists() and not any(folder.iterdir()):
            folder.rmdir()
            log("✕", R, f"{folder.relative_to(ROOT)}  [folder rỗng, đã xoá]")

    # ── 5. Tạo file mới ────────────────────────────────────────────────────
    print(f"\n{BOLD}[5] Tạo file mới{RESET}")
    write_file(ROOT / ".gitignore",    GITIGNORE,    ".gitignore")
    write_file(ROOT / "configs" / ".env.example", ENV_EXAMPLE, ".env.example mẫu")

    # ── Tóm tắt ────────────────────────────────────────────────────────────
    print(f"\n{BOLD}{'='*58}{RESET}")
    if DRY_RUN:
        print(f"  {Y}Dry-run xong. Chạy lại với --apply để thực thi thật:{RESET}")
        print(f"  {BOLD}python cleanup_project.py --apply{RESET}")
    else:
        print(f"  {G}✔ Hoàn tất! Kiểm tra lại với: git status{RESET}")
    print(f"{BOLD}{'='*58}{RESET}\n")

if __name__ == "__main__":
    main()

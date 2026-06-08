# generate_changelog.py
# ============================================================
# Tự động sinh ghi_chu_phien_ban trong version.json
# Luồng: git log (từ tag cũ → HEAD) → Claude API → version.json
# Chạy bởi build_release.bat, KHÔNG cần chạy tay
# ============================================================
import os
import sys
import json
import subprocess
import requests
from datetime import datetime

# ── Cấu hình ─────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MAX_COMMITS       = 40    # Lấy tối đa 40 commit gần nhất
MAX_CHANGELOG     = 6     # Tối đa 6 dòng changelog hiển thị
# ─────────────────────────────────────────────────────────────


def _lay_git_log(so_commit: int = MAX_COMMITS) -> str:
    """Lấy git log từ tag phiên bản cũ nhất đến HEAD"""
    try:
        # Lấy tag gần nhất (phiên bản cũ)
        tag_cu = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0", "HEAD~1"],
            capture_output=True, text=True, encoding="utf-8"
        ).stdout.strip()

        if tag_cu:
            range_arg = f"{tag_cu}..HEAD"
            print(f"   Git log từ tag: {tag_cu} → HEAD")
        else:
            range_arg = f"-{so_commit}"
            print(f"   Không có tag, lấy {so_commit} commit gần nhất")

        result = subprocess.run(
            ["git", "log", range_arg, "--pretty=format:%s", "--no-merges"],
            capture_output=True, text=True, encoding="utf-8"
        )
        commits = result.stdout.strip()
        if not commits:
            # Fallback: lấy N commit gần nhất
            result = subprocess.run(
                ["git", "log", f"-{so_commit}", "--pretty=format:%s", "--no-merges"],
                capture_output=True, text=True, encoding="utf-8"
            )
            commits = result.stdout.strip()
        return commits
    except Exception as e:
        print(f"   ⚠️  Không đọc được git log: {e}")
        return ""


def _goi_claude_api(commits: str, phien_ban: str) -> list[str]:
    """Gọi Claude API để tổng hợp changelog từ danh sách commit"""
    if not ANTHROPIC_API_KEY:
        print("   ⚠️  Không có ANTHROPIC_API_KEY, dùng commit thô")
        return _xu_ly_thu_cong(commits)

    prompt = f"""Bạn là trợ lý kỹ thuật cho phần mềm kế toán Việt Nam.

Dưới đây là danh sách git commit message cho phiên bản {phien_ban}:
---
{commits}
---

Hãy tổng hợp thành tối đa {MAX_CHANGELOG} dòng changelog ngắn gọn, rõ ràng bằng tiếng Việt.
Mỗi dòng bắt đầu bằng "✅ " và mô tả tính năng/sửa lỗi quan trọng.
Gộp các commit liên quan. Bỏ qua commit không quan trọng (fix typo, merge, chore...).
Chỉ trả về danh sách JSON dạng: ["✅ ...", "✅ ...", ...]
Không giải thích thêm."""

    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 512,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        if r.status_code == 200:
            text = r.json()["content"][0]["text"].strip()
            # Parse JSON array từ response
            start = text.find("[")
            end   = text.rfind("]") + 1
            if start >= 0 and end > start:
                changelog = json.loads(text[start:end])
                print(f"   ✅ Claude sinh được {len(changelog)} dòng changelog")
                return changelog[:MAX_CHANGELOG]
        print(f"   ⚠️  Claude API lỗi HTTP {r.status_code}, dùng commit thô")
    except Exception as e:
        print(f"   ⚠️  Lỗi gọi Claude API: {e}, dùng commit thô")

    return _xu_ly_thu_cong(commits)


def _xu_ly_thu_cong(commits: str) -> list[str]:
    """Fallback: dùng commit message trực tiếp nếu không có API key"""
    lines = [ln.strip() for ln in commits.splitlines() if ln.strip()]
    # Lọc commit không quan trọng
    ignore = ("merge", "typo", "wip", "chore", "fmt", "format", "revert")
    lines = [ln for ln in lines if not any(kw in ln.lower() for kw in ignore)]
    # Thêm ✅ nếu chưa có
    result = []
    for ln in lines[:MAX_CHANGELOG]:
        result.append(ln if ln.startswith("✅") else f"✅ {ln}")
    return result


def cap_nhat_changelog(version_json_path: str = "version.json") -> bool:
    """Hàm chính: đọc git log → sinh changelog → ghi lại version.json"""
    print("\n[Changelog] Đang phân tích git log...")

    # Đọc version.json hiện tại
    with open(version_json_path, encoding="utf-8") as f:
        data = json.load(f)
    phien_ban = data.get("phien_ban_moi_nhat", "?")

    # Lấy git commits
    commits = _lay_git_log()
    if not commits:
        print("   ⚠️  Không có commit nào, giữ nguyên changelog cũ")
        return False

    print(f"   Tìm thấy {len(commits.splitlines())} commit")

    # Sinh changelog
    changelog = _goi_claude_api(commits, phien_ban)
    if not changelog:
        print("   ⚠️  Không sinh được changelog")
        return False

    # Ghi lại version.json
    data["ghi_chu_phien_ban"] = changelog
    data["ngay_phat_hanh"] = datetime.now().strftime("%d/%m/%Y")
    with open(version_json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"   ✅ Đã cập nhật {len(changelog)} dòng changelog vào version.json")
    for line in changelog:
        print(f"      {line}")
    return True


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "version.json"
    ok = cap_nhat_changelog(path)
    sys.exit(0 if ok else 1)
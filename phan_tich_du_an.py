"""
Script phân tích chất lượng toàn bộ dự án Python
Chạy: python phan_tich_du_an.py D:\ke_toan_pro_v3
Kết quả xuất ra: bao_cao_chat_luong.txt
"""

import os
import sys
import ast
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
OUTPUT = ROOT / "bao_cao_chat_luong.txt"

lines_out = []

def log(text=""):
    print(text)
    lines_out.append(text)

def get_all_py(root):
    skip = {'.git', '__pycache__', '.pytest_cache', 'venv', 'env', 'node_modules', 'build', 'dist'}
    files = []
    for p in root.rglob("*.py"):
        if not any(s in p.parts for s in skip):
            files.append(p)
    return files

def count_lines(path):
    try:
        with open(path, encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        code = sum(1 for l in lines if l.strip() and not l.strip().startswith('#'))
        comments = sum(1 for l in lines if l.strip().startswith('#'))
        return len(lines), code, comments
    except:
        return 0, 0, 0

def parse_ast(path):
    try:
        with open(path, encoding='utf-8', errors='ignore') as f:
            src = f.read()
        return ast.parse(src), src
    except:
        return None, ""

def analyze_file(path):
    tree, src = parse_ast(path)
    result = {
        "functions": 0, "classes": 0,
        "has_docstring": 0, "missing_docstring": 0,
        "has_type_hints": 0, "missing_type_hints": 0,
        "bare_except": 0, "broad_except": 0,
        "todos": 0, "print_debug": 0,
        "long_functions": [],  # (name, lines)
        "sqlite_row_get": 0,
        "hardcoded_fields": 0,
    }
    if not tree:
        return result

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result["functions"] += 1
            # Docstring
            if (ast.get_docstring(node)):
                result["has_docstring"] += 1
            else:
                result["missing_docstring"] += 1
            # Type hints
            args = node.args
            all_args = args.args + args.posonlyargs + args.kwonlyargs
            has_hints = any(a.annotation for a in all_args) or node.returns
            if has_hints:
                result["has_type_hints"] += 1
            else:
                result["missing_type_hints"] += 1
            # Long functions
            end = getattr(node, 'end_lineno', node.lineno)
            func_lines = end - node.lineno
            if func_lines > 60:
                result["long_functions"].append((node.name, func_lines))

        elif isinstance(node, ast.ClassDef):
            result["classes"] += 1

        elif isinstance(node, ast.ExceptHandler):
            if node.type is None:
                result["bare_except"] += 1
            elif isinstance(node.type, ast.Name) and node.type.id == "Exception":
                result["broad_except"] += 1

    # Text analysis
    result["todos"] = len(re.findall(r'#\s*(TODO|FIXME|HACK|XXX)', src, re.IGNORECASE))
    result["print_debug"] = len(re.findall(r'\bprint\s*\(', src))
    result["sqlite_row_get"] = len(re.findall(r'inv\.get\(|row\.get\(|result\.get\(', src))
    result["hardcoded_fields"] = len(re.findall(r"allowed_fields\s*=\s*\[", src))

    return result

def check_test_coverage(root, all_py):
    test_files = [f for f in all_py if 'test' in f.name.lower() or 'test' in str(f.parent).lower()]
    non_test = [f for f in all_py if f not in test_files]
    return test_files, non_test

def check_dangerous_patterns(root):
    issues = []
    for path in get_all_py(root):
        _, src = parse_ast(path)
        rel = path.relative_to(root)
        if re.search(r'\.get\([\'"]', src) and 'sqlite3' not in src and 'Row' in src:
            issues.append(f"  [!] sqlite3.Row .get() — {rel}")
        if re.search(r'except Exception as e:\s*\n\s*pass', src):
            issues.append(f"  [!] Exception bị nuốt (pass) — {rel}")
        if re.search(r'eval\(|exec\(', src):
            issues.append(f"  [!] Dùng eval/exec — {rel}")
        if re.search(r'SELECT \*', src, re.IGNORECASE):
            issues.append(f"  [~] SELECT * (nên chỉ định cột) — {rel}")
    return issues

def score_project(stats):
    scores = {}

    # 1. Kiến trúc (có phân lớp không)
    layers = stats["layers"]
    scores["Kiến trúc & phân lớp"] = min(10, len(layers) * 1.5 + 2)

    # 2. Tỷ lệ docstring
    total_func = stats["total_functions"]
    doc_rate = stats["has_docstring"] / total_func if total_func else 0
    scores["Docstring & tài liệu"] = round(doc_rate * 10, 1)

    # 3. Type hints
    hint_rate = stats["has_type_hints"] / total_func if total_func else 0
    scores["Type hints"] = round(hint_rate * 10, 1)

    # 4. Xử lý lỗi
    err_penalty = stats["bare_except"] * 1.5 + stats["broad_except"] * 0.5
    scores["Xử lý lỗi"] = max(0, min(10, 8 - err_penalty * 0.3))

    # 5. Test
    test_ratio = stats["test_files"] / max(stats["total_files"], 1)
    scores["Test coverage"] = min(10, test_ratio * 30)

    # 6. Code sạch
    debug_penalty = stats["print_debug"] * 0.05
    todo_penalty = stats["todos"] * 0.1
    long_penalty = stats["long_functions"] * 0.2
    scores["Code sạch"] = max(0, min(10, 8 - debug_penalty - todo_penalty - long_penalty))

    # 7. Bảo mật patterns
    risky = stats["sqlite_row_get"] + stats["eval_exec"]
    scores["Bảo mật code"] = max(0, min(10, 8 - risky * 0.5))

    # 8. Quy mô & hoàn chỉnh
    scores["Quy mô & hoàn chỉnh"] = min(10, stats["total_files"] / 20 + 3)

    total = sum(scores.values()) / len(scores)
    return scores, round(total, 1)

# ===== CHẠY PHÂN TÍCH =====
log("=" * 60)
log(f"  PHÂN TÍCH CHẤT LƯỢNG DỰ ÁN PYTHON")
log(f"  Thư mục: {ROOT}")
log(f"  Thời gian: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
log("=" * 60)

all_py = get_all_py(ROOT)
log(f"\n[1] TỔNG QUAN")
log(f"  Tổng file .py   : {len(all_py)}")

total_lines = total_code = total_comments = 0
total_functions = has_docstring = missing_docstring = 0
has_type_hints = missing_type_hints = 0
bare_except = broad_except = 0
todos = print_debug = 0
sqlite_row_get = eval_exec = 0
long_functions = 0
long_func_list = []

folder_counts = defaultdict(int)
for f in all_py:
    parts = f.relative_to(ROOT).parts
    if len(parts) > 1:
        folder_counts[parts[0]] += 1

layers = [k for k in folder_counts if k in ('models','views','controllers','services','ui','utils','core','tests')]
log(f"  Lớp phát hiện   : {', '.join(layers) if layers else 'Không rõ'}")
log(f"  File theo thư mục:")
for folder, count in sorted(folder_counts.items(), key=lambda x: -x[1])[:10]:
    log(f"    {folder:<20}: {count} file")

log(f"\n[2] PHÂN TÍCH CHI TIẾT TỪNG FILE")
log("-" * 60)

for path in all_py:
    tl, tc, cm = count_lines(path)
    total_lines += tl
    total_code += tc
    total_comments += cm

    r = analyze_file(path)
    total_functions += r["functions"]
    has_docstring += r["has_docstring"]
    missing_docstring += r["missing_docstring"]
    has_type_hints += r["has_type_hints"]
    missing_type_hints += r["missing_type_hints"]
    bare_except += r["bare_except"]
    broad_except += r["broad_except"]
    todos += r["todos"]
    print_debug += r["print_debug"]
    sqlite_row_get += r["sqlite_row_get"]
    long_functions += len(r["long_functions"])
    if r["long_functions"]:
        for fname, flines in r["long_functions"]:
            long_func_list.append(f"    {path.relative_to(ROOT)} → {fname}() [{flines} dòng]")

log(f"  Tổng dòng code      : {total_lines:,}")
log(f"  Dòng thực thi       : {total_code:,}")
log(f"  Dòng comment        : {total_comments:,}")
log(f"  Tổng hàm/method     : {total_functions:,}")

log(f"\n[3] CHẤT LƯỢNG CODE")
log("-" * 60)
doc_rate = has_docstring / total_functions * 100 if total_functions else 0
hint_rate = has_type_hints / total_functions * 100 if total_functions else 0
log(f"  Có docstring        : {has_docstring}/{total_functions} ({doc_rate:.1f}%)")
log(f"  Có type hints       : {has_type_hints}/{total_functions} ({hint_rate:.1f}%)")
log(f"  bare except         : {bare_except} chỗ")
log(f"  except Exception    : {broad_except} chỗ")
log(f"  print() debug       : {print_debug} chỗ")
log(f"  TODO/FIXME          : {todos} chỗ")
log(f"  Hàm quá dài (>60ln) : {long_functions}")
log(f"  sqlite3.Row .get()  : {sqlite_row_get} chỗ (nguy hiểm)")

if long_func_list:
    log(f"\n  Danh sách hàm quá dài:")
    for item in long_func_list[:20]:
        log(item)

log(f"\n[4] KIỂM TRA PATTERNS NGUY HIỂM")
log("-" * 60)
dangerous = check_dangerous_patterns(ROOT)
if dangerous:
    for d in dangerous[:30]:
        log(d)
else:
    log("  Không phát hiện pattern nguy hiểm nghiêm trọng")

test_files, non_test = check_test_coverage(ROOT, all_py)
log(f"\n[5] TEST")
log("-" * 60)
log(f"  File test           : {len(test_files)}")
log(f"  File cần test       : {len(non_test)}")
log(f"  Tỷ lệ              : {len(test_files)/max(len(all_py),1)*100:.1f}%")
if test_files:
    log(f"  Các file test:")
    for t in test_files[:15]:
        log(f"    {t.relative_to(ROOT)}")

log(f"\n[6] ĐÁNH GIÁ ĐIỂM SỐ")
log("=" * 60)

stats = {
    "total_files": len(all_py),
    "total_functions": total_functions,
    "has_docstring": has_docstring,
    "has_type_hints": has_type_hints,
    "bare_except": bare_except,
    "broad_except": broad_except,
    "test_files": len(test_files),
    "print_debug": print_debug,
    "todos": todos,
    "long_functions": long_functions,
    "sqlite_row_get": sqlite_row_get,
    "eval_exec": eval_exec,
    "layers": layers,
}

scores, total = score_project(stats)
for name, score in scores.items():
    bar = "█" * int(score) + "░" * (10 - int(score))
    log(f"  {name:<25}: {bar} {score:.1f}/10")

log("-" * 60)
log(f"  {'TỔNG ĐIỂM':<25}: {total:.1f}/10")
log("=" * 60)

log(f"\n[7] KHUYẾN NGHỊ ƯU TIÊN")
log("-" * 60)
if sqlite_row_get > 0:
    log(f"  🔴 Sửa {sqlite_row_get} chỗ dùng .get() trên sqlite3.Row")
if doc_rate < 50:
    log(f"  🔴 Bổ sung docstring — hiện chỉ {doc_rate:.0f}%")
if bare_except > 5:
    log(f"  🔴 Sửa {bare_except} bare except")
if hint_rate < 30:
    log(f"  🟡 Thêm type hints — hiện chỉ {hint_rate:.0f}%")
if print_debug > 20:
    log(f"  🟡 Dọn {print_debug} lệnh print() debug")
if long_functions > 10:
    log(f"  🟡 Tách {long_functions} hàm quá dài (>60 dòng)")
if len(test_files) < 10:
    log(f"  🟡 Bổ sung test — hiện chỉ {len(test_files)} file test")

log(f"\nXuất báo cáo: {OUTPUT}")
log("=" * 60)

with open(OUTPUT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines_out))

print(f"\n✅ Đã lưu báo cáo: {OUTPUT}")

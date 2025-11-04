#!/usr/bin/env python3
"""
Metadata Applier from CSV → Media Files (cross‑platform)

Features:
- Reads a CSV with columns: Filename, Title, Keywords
- Matches files in a target directory (exact and case-insensitive fallback)
- Writes metadata using exiftool: Title and Keywords
- Supports dry-run, custom CSV encoding, and custom exiftool path
- Clear reporting summary at the end

Usage examples:
  python metadata_applier.py --csv metadata.csv --dir ./videos
  python metadata_applier.py --csv metadata.csv --dry-run

Requirements:
- Python 3.8+
- exiftool installed and available on PATH (or pass --exiftool /path/to/exiftool)
"""
from __future__ import annotations
import argparse
import csv
import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

def find_file_case_insensitive(root: Path, target_name: str) -> Path | None:
    """Attempt to locate a file by exact name first, then case-insensitive within root.
    Returns a Path if found, else None.
    """
    exact = root / target_name
    if exact.exists():
        return exact
    # Fallback: case-insensitive scan of the directory (non recursive by default)
    lower = target_name.lower()
    for p in root.iterdir():
        try:
            if p.is_file() and p.name.lower() == lower:
                return p
        except PermissionError:
            continue
    return None


def build_keywords_args(keywords_str: str) -> List[str]:
    """Split a comma-separated keywords string into multiple -Keywords= arguments.
    Trims whitespace; skips empty entries.
    """
    # Normalize various separators (comma, semicolon)
    if keywords_str is None:
        return []
    raw = [k.strip() for k in keywords_str.replace(";", ",").split(",")]
    return [f"-Keywords={k}" for k in raw if k]


def run_exiftool(exiftool: str, file_path: Path, title: str | None, keywords: str | None, dry_run: bool) -> Tuple[bool, str]:
    """Invoke exiftool to write Title and Keywords. Returns (ok, message)."""
    args = [exiftool]

    # Prefer explicit XMP where sensible; exiftool will map generically if tag is available
    if title:
        args.append(f"-Title={title}")
        # Also set XMP:Title for broader compatibility
        args.append(f"-XMP:Title={title}")

    kw_args = build_keywords_args(keywords)
    if kw_args:
        args.extend(kw_args)
        # Mirror into XMP:Subject as well (commonly used for keywords)
        # exiftool supports -Subject= for XMP:Subject
        subject_args = [a.replace("-Keywords=", "-Subject=") for a in kw_args]
        args.extend(subject_args)

    # Overwrite in place; exiftool writes a _original backup unless told otherwise
    args.extend(["-overwrite_original", str(file_path)])

    if dry_run:
        return True, "DRY-RUN: " + " ".join([repr(x) for x in args])

    try:
        result = subprocess.run(args, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            return True, (result.stdout.strip() or "Updated")
        else:
            msg = (result.stderr or result.stdout).strip()
            return False, msg
    except FileNotFoundError:
        return False, f"exiftool not found at '{exiftool}'. Install it or pass --exiftool."


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Apply Title and Keywords metadata to files based on a CSV.")
    p.add_argument("--csv", required=False, help="Path to the CSV file (columns: Filename, Title, Keywords). If omitted, will auto-detect a .csv in --dir")
    p.add_argument("--dir", default=".", help="Directory containing the target files (default: current directory)")
    p.add_argument("--encoding", default="utf-8-sig", help="CSV encoding (default: utf-8-sig, handles BOM)")
    p.add_argument("--delimiter", default=",", help="CSV delimiter (default: ,)")
    p.add_argument("--exiftool", default="exiftool", help="Path to exiftool executable (default: exiftool)")
    p.add_argument("--dry-run", action="store_true", help="Show what would be written without changing files")
    p.add_argument("--recursive", action="store_true", help="(Not used) Placeholder for future recursion support")
    return p.parse_args()


def read_csv_rows(csv_path: Path, encoding: str, delimiter: str) -> List[Dict[str, str]]:
    if not csv_path.exists():
        print(f"CSV tidak ditemukan: {csv_path}", file=sys.stderr)
        sys.exit(1)
    try:
        with csv_path.open("r", newline="", encoding=encoding) as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            # Normalize headers (strip surrounding spaces)
            reader.fieldnames = [fn.strip() for fn in (reader.fieldnames or [])]
            rows = []
            for row in reader:
                # Strip whitespace from values
                norm = {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
                rows.append(norm)
            return rows
    except UnicodeDecodeError as e:
        print(f"Gagal membaca CSV (encoding): {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    args = parse_args()
    base_dir = Path(args.dir).resolve()
    # Determine CSV path: use provided path or auto-detect inside base_dir
    if args.csv:
        csv_path = Path(args.csv)
        if not csv_path.is_absolute():
            # If a relative path is given, resolve relative to base_dir for convenience
            candidate = (base_dir / csv_path)
            csv_path = candidate.resolve() if candidate.exists() else csv_path.resolve()
        else:
            csv_path = csv_path.resolve()
    else:
        # Auto-detect CSV within base_dir
        candidates = sorted(base_dir.glob("*.csv"))
        preferred_names = {"metadata.csv", "meta.csv", "tags.csv"}
        preferred = [p for p in candidates if p.name.lower() in preferred_names]
        if preferred:
            csv_path = preferred[0]
        elif candidates:
            csv_path = candidates[0]
        else:
            print(f"CSV tidak ditemukan di folder: {base_dir}. Berikan --csv atau letakkan file .csv di folder tersebut.", file=sys.stderr)
            sys.exit(1)

    print(f"Folder  : {base_dir}")
    print(f"CSV     : {csv_path}")
    print(f"ExifTool: {args.exiftool}")
    print(f"Mode    : {'DRY-RUN' if args.dry_run else 'APPLY'}\n")

    rows = read_csv_rows(csv_path, args.encoding, args.delimiter)
    if not rows:
        print("CSV kosong atau tidak memiliki baris data.")
        return

    required_cols = {"Filename", "Title", "Keywords"}
    headers = set(rows[0].keys())
    if not required_cols.issubset(headers):
        print(f"Kolom CSV harus mengandung: {', '.join(sorted(required_cols))}. Ditemukan: {', '.join(sorted(headers))}")
        return

    total = len(rows)
    ok_count = 0
    miss_count = 0
    err_count = 0
    details: List[str] = []

    for idx, row in enumerate(rows, start=1):
        filename = row.get("Filename", "").strip()
        title = row.get("Title", "").strip() or None
        keywords = row.get("Keywords", "").strip() or None

        # Normalize path separators potentially present in CSV (we expect just filenames)
        filename_only = Path(filename).name
        target = find_file_case_insensitive(base_dir, filename_only)

        header = f"[{idx}/{total}] {filename_only}"
        if not target:
            print(f"{header} — ❌ File tidak ditemukan")
            miss_count += 1
            details.append(f"MISS : {filename_only}")
            continue

        print(f"{header} — updating metadata…")
        ok, msg = run_exiftool(args.exiftool, target, title, keywords, args.dry_run)
        if ok:
            print(f"   ✅ {target.name}: {msg}")
            ok_count += 1
            details.append(f"OK   : {target.name}")
        else:
            print(f"   ❌ {target.name}: {msg}")
            err_count += 1
            details.append(f"ERROR: {target.name} — {msg}")

    print("\n──── Summary ────")
    print(f"Total rows : {total}")
    print(f"Updated    : {ok_count}")
    print(f"Not found  : {miss_count}")
    print(f"Errors     : {err_count}")

    if details:
        print("\nDetails:")
        for d in details:
            print(" - ", d)

    if args.dry_run:
        print("\n(Ini hanyalah simulasi. Jalankan ulang TANPA --dry-run untuk menerapkan perubahan.)")

if __name__ == "__main__":
    main()

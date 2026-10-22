#!/usr/bin/env python3
"""Extract BODAS-RTS and easyConfig, recursively unpacking ConfigData."""

import argparse
from io import BytesIO
from pathlib import Path
from zipfile import BadZipFile, ZipFile, ZipInfo


def extract_member(archive: ZipFile, entry: ZipInfo, target: Path) -> None:
    """Extract a single member from a ZIP archive, handling nested ZIPs.

    Recursively extracts nested ZIP files if encountered.

    Args:
        archive (ZipFile): The ZIP archive containing the member.
        entry (ZipInfo): The member to extract.
        target (Path): The target directory for extraction.

    Raises:
        ValueError: If the member is unsafe (e.g., path traversal).
    """
    if entry.filename.lower().endswith(".library"):
        return
    member = (target / entry.filename).resolve()
    if not member.is_relative_to(target):
        raise ValueError(f"Unsafe archive member: {entry.filename}")
    if not entry.is_dir() and member.suffix.lower() == ".zip":
        with ZipFile(BytesIO(archive.read(entry))) as nested:
            nested_target = member.with_suffix("")
            nested_target.mkdir(parents=True, exist_ok=True)
            for nested_entry in nested.infolist():
                extract_member(nested, nested_entry, nested_target)
    else:
        archive.extract(entry, target)


def unzip_latest_build(source: Path, destination: Path | None = None) -> Path:
    if not source.is_dir():
        raise NotADirectoryError(f"Archive directory does not exist: {source}")

    archives = [
        path
        for path in source.iterdir()
        if path.is_file() and path.match("*[Bb]uild*.[Zz][Ii][Pp]")
    ]
    if not archives:
        raise FileNotFoundError(f"No *Build*.zip archives found in {source}")
    latest = max(archives, key=lambda path: (path.stat().st_mtime_ns, path.name))
    target = (
        destination if destination is not None else latest.with_suffix("")
    ).resolve()

    with ZipFile(latest) as archive:
        entries = [
            entry
            for entry in archive.infolist()
            if entry.filename.startswith(("BODAS-RTS/", "easyConfig/"))
            and (
                entry.filename == "easyConfig/easyConfig_ConfigData.zip"
                or not entry.filename.lower().endswith((".library", ".zip"))
            )
        ]
        if not entries:
            raise ValueError(f"No BODAS-RTS or easyConfig folders found in {latest}")
        for entry in entries:
            member = (target / entry.filename).resolve()
            if not member.is_relative_to(target):
                raise ValueError(f"Unsafe archive member: {entry.filename}")
        # Allow the target to pre-exist without raising an error.
        target.mkdir(parents=True, exist_ok=True)
        for entry in entries:
            extract_member(archive, entry, target)

    print(f"Extracted {latest.name} to {target}")
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "source",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="directory containing build ZIPs (default: repository root)",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        help="new extraction directory (default: ZIP path without .zip)",
    )
    args = parser.parse_args()
    try:
        unzip_latest_build(args.source, args.output_dir)
    except (OSError, BadZipFile, ValueError) as error:
        parser.exit(1, f"unzip_latest_build: {error}\n")


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.kb.downloader import DocumentDownloader, SourceInventory


INVENTORY_PATH = ROOT / "data" / "metadata" / "source_inventory.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download official legal sources.")
    parser.add_argument("source_ids", nargs="*", help="Only download these source_id values")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--retries", type=int, default=2)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    inventory = SourceInventory(INVENTORY_PATH)
    records = inventory.load()
    selected = set(args.source_ids)
    if selected:
        unknown = selected - {record.source_id for record in records}
        if unknown:
            raise ValueError(f"source_id không tồn tại: {sorted(unknown)}")
        records = [record for record in records if record.source_id in selected]

    downloader = DocumentDownloader(
        project_root=ROOT,
        timeout_seconds=args.timeout,
        retries=args.retries,
    )

    failures = 0
    for record in records:
        if not record.source_urls:
            print(f"SKIP {record.source_id}: chưa có source_url")
            continue
        try:
            downloaded = downloader.download(record)
            inventory.update(
                record.source_id,
                crawl_status="downloaded",
                crawl_date=datetime.now(timezone.utc).isoformat(),
                last_checked_at=datetime.now(timezone.utc).isoformat(),
                document_hash=",".join(item.sha256 for item in downloaded),
                content_length=sum(item.byte_count for item in downloaded),
                error_message="",
            )
            print(f"OK {record.source_id}: {len(downloaded)} file")
        except Exception as exc:
            failures += 1
            inventory.update(
                record.source_id,
                crawl_status="failed",
                last_checked_at=datetime.now(timezone.utc).isoformat(),
                error_message=str(exc),
            )
            print(f"FAILED {record.source_id}: {exc}")

    inventory.save()
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

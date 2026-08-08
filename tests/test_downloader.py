from __future__ import annotations

from pathlib import Path
import tempfile
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.kb.downloader import DocumentDownloader, SourceInventory


INVENTORY_PATH = ROOT / "data" / "metadata" / "source_inventory.csv"


def test_inventory_parses_semicolon_and_multiple_urls() -> None:
    inventory = SourceInventory(INVENTORY_PATH)
    records = inventory.load()
    land_law = inventory.get("src_luat_dat_dai_2024")

    assert len(records) == 4
    assert len(land_law.source_urls) == 3
    assert land_law.raw_target_path == "data/raw/laws/luat_dat_dai_2024"


def test_downloader_rejects_path_outside_project() -> None:
    with tempfile.TemporaryDirectory() as directory:
        downloader = DocumentDownloader(project_root=directory)
        try:
            downloader._target_directory("../outside")
        except ValueError:
            pass
        else:
            raise AssertionError("Path traversal phải bị từ chối.")


def main() -> None:
    test_inventory_parses_semicolon_and_multiple_urls()
    test_downloader_rejects_path_outside_project()
    print("MODULE 1 - DATA ACQUISITION: SUCCESS")


if __name__ == "__main__":
    main()

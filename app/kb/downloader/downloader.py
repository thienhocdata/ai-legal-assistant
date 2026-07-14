from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import mimetypes
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .inventory import InventoryRecord


@dataclass(frozen=True, slots=True)
class DownloadedFile:
    url: str
    path: Path
    byte_count: int
    sha256: str
    content_type: str
    downloaded_at: str


class DocumentDownloader:
    """Small dependency-free downloader with retries and atomic writes."""

    def __init__(
        self,
        *,
        project_root: str | Path,
        timeout_seconds: float = 30.0,
        retries: int = 2,
        user_agent: str = "AI-Legal-Assistant/0.1",
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds phải lớn hơn 0.")
        if retries < 0:
            raise ValueError("retries không được âm.")
        self.project_root = Path(project_root).resolve()
        self.timeout_seconds = timeout_seconds
        self.retries = retries
        self.user_agent = user_agent

    def _target_directory(self, raw_target_path: str) -> Path:
        target = (self.project_root / raw_target_path).resolve()
        try:
            target.relative_to(self.project_root)
        except ValueError as exc:
            raise ValueError("raw_target_path nằm ngoài project root.") from exc
        return target

    @staticmethod
    def _filename(url: str, index: int, document_id: str) -> str:
        name = Path(urlparse(url).path).name
        if name and "." in name:
            return name
        extension = mimetypes.guess_extension("application/pdf") or ".bin"
        return f"{document_id}_part{index}{extension}"

    def download(self, record: InventoryRecord) -> list[DownloadedFile]:
        urls = record.source_urls
        if not urls:
            raise ValueError(f"Nguồn {record.source_id} chưa có source_url.")

        target_directory = self._target_directory(record.raw_target_path)
        target_directory.mkdir(parents=True, exist_ok=True)
        results: list[DownloadedFile] = []

        for index, url in enumerate(urls, start=1):
            filename = self._filename(url, index, record.document_id)
            destination = target_directory / filename
            temporary = destination.with_suffix(destination.suffix + ".part")
            last_error: Exception | None = None

            for attempt in range(self.retries + 1):
                try:
                    request = Request(url, headers={"User-Agent": self.user_agent})
                    with urlopen(request, timeout=self.timeout_seconds) as response:
                        content = response.read()
                        content_type = response.headers.get_content_type()
                    if not content:
                        raise ValueError(f"Nguồn trả về file rỗng: {url}")
                    temporary.write_bytes(content)
                    temporary.replace(destination)
                    digest = sha256(content).hexdigest()
                    results.append(
                        DownloadedFile(
                            url=url,
                            path=destination,
                            byte_count=len(content),
                            sha256=digest,
                            content_type=content_type,
                            downloaded_at=datetime.now(timezone.utc).isoformat(),
                        )
                    )
                    last_error = None
                    break
                except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
                    last_error = exc
                    if temporary.exists():
                        temporary.unlink()
                    if attempt < self.retries:
                        time.sleep(min(2**attempt, 4))

            if last_error is not None:
                raise RuntimeError(f"Không tải được {url}: {last_error}") from last_error

        return results

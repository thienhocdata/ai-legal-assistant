from __future__ import annotations

from pathlib import Path

import fitz


class PDFParser:
    """
    Trích xuất văn bản thô từ PDF.

    Module này chỉ chịu trách nhiệm đọc PDF và trả về text theo đúng thứ tự trang.
    Việc xóa header/footer, nối dòng và nhận diện Điều/Khoản/Điểm thuộc các bước sau.
    """

    def extract_pages(self, pdf_path: str | Path) -> list[str]:
        """
        Trích xuất text của từng trang PDF.

        Args:
            pdf_path: Đường dẫn tới file PDF.

        Returns:
            Danh sách text theo đúng thứ tự trang. Mỗi phần tử tương ứng một trang.

        Raises:
            FileNotFoundError: Khi file không tồn tại.
            ValueError: Khi đường dẫn không phải file PDF hoặc PDF có mật khẩu.
            RuntimeError: Khi không thể mở hoặc đọc PDF.
        """
        path = Path(pdf_path)

        if not path.exists():
            raise FileNotFoundError(f"Không tìm thấy file PDF: {path}")

        if not path.is_file():
            raise ValueError(f"Đường dẫn không phải là file: {path}")

        if path.suffix.lower() != ".pdf":
            raise ValueError(f"File không có định dạng PDF: {path}")

        try:
            with fitz.open(path) as document:
                if document.needs_pass:
                    raise ValueError(f"PDF được bảo vệ bằng mật khẩu: {path}")

                pages: list[str] = []

                for page in document:
                    # Giữ nguyên text thô theo trang; chưa làm sạch tại Module 2.
                    pages.append(page.get_text("text"))

                return pages

        except (FileNotFoundError, ValueError):
            raise
        except Exception as exc:
            raise RuntimeError(f"Không thể đọc PDF '{path}': {exc}") from exc

    def extract_text(self, pdf_path: str | Path) -> str:
        """
        Đọc toàn bộ nội dung PDF và ghép text theo đúng thứ tự trang.

        Phương thức này được giữ nguyên để tương thích với code hiện tại.
        """
        pages = self.extract_pages(pdf_path)
        return "\n".join(pages)
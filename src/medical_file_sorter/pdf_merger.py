"""
PDFMerger class for combining medical documents into a single PDF.
"""

import io
from pathlib import Path
from typing import Any

from pdf2image import convert_from_path
from PIL import Image
from pypdf import PdfReader, PdfWriter


class PDFMerger:
    """
    Merges medical documents (PDFs and images) into a single structured PDF.
    """

    def __init__(self, output_filename: str = "Merged_Medical_Records.pdf"):
        """
        Initialize the PDFMerger.

        Args:
            output_filename: Name of the output PDF file.
        """
        self.output_filename = output_filename

    def _image_to_pdf_bytes(self, image_path: Path) -> bytes:
        """
        Convert an image file to PDF bytes.

        Args:
            image_path: Path to the image file.

        Returns:
            PDF content as bytes.
        """
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            buffer = io.BytesIO()
            img.save(buffer, format="PDF")
            buffer.seek(0)
            return buffer.read()

    def _append_pdf(self, writer: PdfWriter, file_path: Path) -> bool:
        """
        Append a PDF file to the writer.

        Args:
            writer: PdfWriter object.
            file_path: Path to the PDF file.

        Returns:
            True if successful, False otherwise.
        """
        try:
            reader = PdfReader(file_path)
            for page in reader.pages:
                writer.add_page(page)
            return True
        except Exception as e:
            print(f"Warning: Failed to append PDF {file_path.name}: {e}")
            return False

    def _append_image(self, writer: PdfWriter, file_path: Path) -> bool:
        """
        Convert an image to PDF and append to the writer.

        Args:
            writer: PdfWriter object.
            file_path: Path to the image file.

        Returns:
            True if successful, False otherwise.
        """
        try:
            pdf_bytes = self._image_to_pdf_bytes(file_path)
            reader = PdfReader(io.BytesIO(pdf_bytes))
            for page in reader.pages:
                writer.add_page(page)
            return True
        except Exception as e:
            print(f"Warning: Failed to append image {file_path.name}: {e}")
            return False

    def _append_file(self, writer: PdfWriter, file_path: Path) -> bool:
        """
        Append a file (PDF or image) to the writer.

        Args:
            writer: PdfWriter object.
            file_path: Path to the file.

        Returns:
            True if successful, False otherwise.
        """
        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            return self._append_pdf(writer, file_path)
        elif suffix in {".jpg", ".jpeg", ".png", ".heic"}:
            return self._append_image(writer, file_path)
        else:
            print(f"Warning: Unsupported file type: {file_path.name}")
            return False

    def merge_documents(
        self, folder_path: Path, sort_result: dict[str, Any]
    ) -> Path | None:
        """
        Merge documents according to the sorted groups.

        Args:
            folder_path: Path to the folder containing the files.
            sort_result: Dictionary with 'groups' and 'uncategorized' keys.

        Returns:
            Path to the output PDF, or None if merge failed.
        """
        writer = PdfWriter()
        files_added = 0

        # Process grouped documents first
        for group_idx, group in enumerate(sort_result.get("groups", []), 1):
            print(f"\nProcessing Group {group_idx}:")
            
            # Handle both old format (list) and new format (dict with files/summary)
            if isinstance(group, dict):
                files = group.get("files", [])
            else:
                files = group
            
            for filename in files:
                file_path = folder_path / filename
                if not file_path.exists():
                    print(f"  Warning: File not found: {filename}")
                    continue

                print(f"  Adding: {filename}")
                if self._append_file(writer, file_path):
                    files_added += 1

        # Process uncategorized documents at the end
        uncategorized = sort_result.get("uncategorized", [])
        if uncategorized:
            print("\nProcessing Uncategorized Documents:")
            for filename in uncategorized:
                file_path = folder_path / filename
                if not file_path.exists():
                    print(f"  Warning: File not found: {filename}")
                    continue

                print(f"  Adding: {filename}")
                if self._append_file(writer, file_path):
                    files_added += 1

        if files_added == 0:
            print("Error: No files were successfully added to the PDF.")
            return None

        # Write the output file
        output_path = folder_path / self.output_filename
        try:
            with open(output_path, "wb") as output_file:
                writer.write(output_file)
            print(f"\nSuccessfully created: {output_path}")
            print(f"Total files merged: {files_added}")
            return output_path
        except Exception as e:
            print(f"Error: Failed to write output PDF: {e}")
            return None

"""
Main entry point for the Intelligent Medical File Sorter CLI.
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from .image_processor import ImageProcessor
from .llm_sorter import (
    BACKEND_CONFIGS,
    LLMBackend,
    LLMSorter,
    get_backend_from_string,
    list_backends,
)
from .pdf_merger import PDFMerger


def display_groups(sort_result: dict) -> None:
    """
    Display the sorted groups to the user.

    Args:
        sort_result: Dictionary with 'groups' and 'uncategorized' keys.
    """
    print("\n" + "=" * 60)
    print("📋 DOCUMENT ORGANIZATION RESULTS")
    print("=" * 60)

    groups = sort_result.get("groups", [])
    total_bill_amount = 0.0
    
    if groups:
        for idx, group in enumerate(groups, 1):
            # Handle both old format (list) and new format (dict with files/summary)
            if isinstance(group, dict):
                files = group.get("files", [])
                summary = group.get("summary", "")
                patient_name = group.get("patient_name", "Unknown")
                bill_amount = group.get("bill_amount", 0)
            else:
                files = group
                summary = ""
                patient_name = "Unknown"
                bill_amount = 0

            total_bill_amount += float(bill_amount) if bill_amount else 0.0

            print(f"\n🗂️  Group {idx} (Transaction):")
            print(f"    👤 Patient: {patient_name}")
            if summary:
                print(f"    📝 {summary}")
            if bill_amount and bill_amount > 0:
                print(f"    💰 Bill Amount: ₹{bill_amount:,.2f}")
            for filename in files:
                print(f"    • {filename}")
    else:
        print("\n⚠️  No document groups were identified.")

    uncategorized = sort_result.get("uncategorized", [])
    if uncategorized:
        print(f"\n📁 Uncategorized ({len(uncategorized)} files):")
        for filename in uncategorized:
            print(f"    • {filename}")

    print("\n" + "=" * 60)
    
    # Show grand total
    if total_bill_amount > 0:
        print(f"\n💵 TOTAL BILLS PAID: ₹{total_bill_amount:,.2f}")
        print("=" * 60)


def get_user_confirmation() -> bool:
    """
    Ask the user for confirmation to proceed with merging.

    Returns:
        True if user confirms, False otherwise.
    """
    while True:
        response = input("\n❓ Proceed with merging these documents? (Y/N): ").strip().upper()
        if response in ("Y", "YES"):
            return True
        elif response in ("N", "NO"):
            return False
        else:
            print("Please enter Y or N.")


def get_api_key_for_backend(backend: LLMBackend) -> str | None:
    """
    Get the appropriate API key for the specified backend.
    
    Args:
        backend: The LLM backend being used.
        
    Returns:
        API key string or None if not required/found.
    """
    config = BACKEND_CONFIGS[backend]
    
    if not config.requires_api_key:
        return None
    
    # Check for backend-specific API key first
    if backend == LLMBackend.OPENROUTER:
        key = os.getenv("OPENROUTER_API_KEY")
        if key:
            return key
    
    # Fall back to generic OPENAI_API_KEY
    return os.getenv("OPENAI_API_KEY")


def main() -> int:
    """
    Main entry point for the CLI.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    # Load environment variables
    load_dotenv()

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Intelligent Medical File Sorter - Organize medical documents using AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  # Using OpenAI (default)
  %(prog)s /path/to/medical/documents

  # Using LM Studio (local)
  %(prog)s /path/to/docs --backend lmstudio --model "your-local-model"

  # Using OpenRouter  
  %(prog)s /path/to/docs --backend openrouter --model "anthropic/claude-3.5-sonnet"

{list_backends()}

Requirements:
  - API key set via environment variable (see .env.example)
  - poppler must be installed (brew install poppler on macOS)
        """,
    )
    parser.add_argument(
        "folder_path",
        type=str,
        help="Path to the folder containing medical documents",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="Merged_Medical_Records.pdf",
        help="Output filename (default: Merged_Medical_Records.pdf)",
    )
    parser.add_argument(
        "--max-dimension",
        "-m",
        type=int,
        default=1000,
        help="Maximum image dimension for processing (default: 1000)",
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip confirmation prompt and proceed with merging",
    )
    parser.add_argument(
        "--backend",
        "-b",
        type=str,
        default="openrouter",
        help="LLM backend: openai, openrouter, lmstudio (default: openrouter)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model name (uses backend default if not specified)",
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default=None,
        help="Custom API base URL (overrides backend default)",
    )

    args = parser.parse_args()

    # Validate folder path
    folder_path = Path(args.folder_path).expanduser().resolve()
    if not folder_path.exists():
        print(f"❌ Error: Folder does not exist: {folder_path}")
        return 1
    if not folder_path.is_dir():
        print(f"❌ Error: Path is not a directory: {folder_path}")
        return 1

    # Parse backend
    try:
        backend = get_backend_from_string(args.backend)
    except ValueError as e:
        print(f"❌ Error: {e}")
        return 1
    
    backend_config = BACKEND_CONFIGS[backend]
    
    # Get API key
    api_key = get_api_key_for_backend(backend)
    if backend_config.requires_api_key and not api_key:
        if backend == LLMBackend.OPENROUTER:
            print("❌ Error: OPENROUTER_API_KEY or OPENAI_API_KEY environment variable is not set.")
        else:
            print("❌ Error: OPENAI_API_KEY environment variable is not set.")
        print("   Set it in your environment or create a .env file.")
        return 1

    # Determine model
    model = args.model or backend_config.default_model

    print(f"\n🔍 Scanning folder: {folder_path}")
    print(f"🤖 Using backend: {backend_config.name} (model: {model})")

    # Step 1: Process files
    print("\n📸 Step 1: Processing files...")
    processor = ImageProcessor(max_dimension=args.max_dimension)

    try:
        valid_files = processor.get_valid_files(folder_path)
    except ValueError as e:
        print(f"❌ Error: {e}")
        return 1

    if not valid_files:
        print("❌ Error: No valid files found in the folder.")
        print("   Supported formats: PDF, JPG, JPEG, PNG, HEIC")
        return 1

    print(f"   Found {len(valid_files)} valid files")

    # Warn about large batches
    if len(valid_files) > 20:
        print(f"\n⚠️  Warning: Processing {len(valid_files)} files may affect accuracy.")
        print("   Consider processing in smaller batches for best results.")

    # Convert files to Base64
    print("\n🔄 Converting files to processable format...")
    file_data = processor.process_folder(folder_path)

    if not file_data:
        print("❌ Error: Failed to process any files.")
        return 1

    print(f"   Successfully processed {len(file_data)} files")

    # Step 2: Sort with LLM
    print(f"\n🤖 Step 2: Analyzing documents with {backend_config.name}...")
    
    try:
        sorter = LLMSorter(
            api_key=api_key,
            model=model,
            backend=backend,
            base_url=args.base_url,
        )
    except ValueError as e:
        print(f"❌ Error: {e}")
        return 1

    try:
        raw_result = sorter.sort_documents(file_data)
        sort_result = sorter.validate_result(raw_result, set(file_data.keys()))
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    # Display results
    display_groups(sort_result)

    # Get user confirmation
    if not args.yes:
        if not get_user_confirmation():
            print("\n🚫 Operation cancelled. You can manually organize files and try again.")
            return 0

    # Step 3: Merge PDFs
    print("\n📄 Step 3: Merging documents...")
    merger = PDFMerger(output_filename=args.output)
    output_path = merger.merge_documents(folder_path, sort_result)

    if output_path:
        print(f"\n✅ Success! Merged PDF saved to: {output_path}")
        return 0
    else:
        print("\n❌ Failed to create merged PDF.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

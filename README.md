# Intelligent Medical File Sorter CLI

A Python-based CLI tool for macOS that ingests a folder of disorganized medical documents (images and PDFs), identifies relationships between prescriptions and bills using a Multimodal LLM (GPT-4o), and merges them into a single, structured PDF.

## Features

- 📄 **Multi-format support**: Handles PDF, JPG, JPEG, PNG, and HEIC files
- 🤖 **AI-powered organization**: Uses GPT-4o Vision to classify and group documents
- 🔗 **Smart matching**: Links prescriptions with related bills based on content (medicines, doctor names)
- 📑 **PDF merging**: Combines all documents into a single organized PDF
- ✅ **User confirmation**: Review the AI's grouping before merging

## Quick Setup

The easiest way to get started is to run the setup script:

```bash
# Clone the repository
git clone https://github.com/your-username/medical-bills-organiser.git
cd medical-bills-organiser

# Run the setup script (installs all dependencies automatically)
chmod +x setup.sh
./setup.sh
```

The setup script will automatically:
- Install pipx (via Homebrew on macOS)
- Install Poetry (via pipx)
- Install poppler (via Homebrew on macOS)
- Install Python dependencies
- Create `.env` from template

## Manual Installation

If you prefer to install dependencies manually:

### 1. System Dependencies

```bash
# macOS
brew install pipx poppler
pipx install poetry
```

### 2. Project Setup

```bash
# Install Python dependencies
poetry install

# Copy environment template
cp .env.example .env

# Activate virtual environment
poetry shell
```

## Usage

```bash
# Basic usage
python -m medical_file_sorter.main /path/to/medical/documents

# With options
python -m medical_file_sorter.main ~/Documents/medical_files \
    --output "My_Medical_Records.pdf" \
    --max-dimension 1200

# Skip confirmation prompt
python -m medical_file_sorter.main /path/to/docs --yes
```

### Command Line Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `folder_path` | - | Required | Path to folder containing medical documents |
| `--output` | `-o` | `Merged_Medical_Records.pdf` | Output filename |
| `--max-dimension` | `-m` | `1000` | Maximum image dimension for processing |
| `--yes` | `-y` | `False` | Skip confirmation prompt |

## How It Works

1. **Scanning**: The tool scans the specified folder for valid files (PDF, images)
2. **Processing**: Each file is converted to a standardized image format for AI analysis
3. **AI Analysis**: GPT-4o Vision analyzes all documents to:
   - Classify each as "Prescription" or "Bill"
   - Group related documents (e.g., a prescription with its associated bills)
4. **Review**: The groupings are displayed for user confirmation
5. **Merging**: Documents are merged into a single PDF in the organized order

## Project Structure

```
medical-bills-organiser/
├── src/
│   └── medical_file_sorter/
│       ├── __init__.py
│       ├── main.py              # CLI entry point
│       ├── image_processor.py   # File → Base64 conversion
│       ├── llm_sorter.py        # GPT-4o classification logic
│       └── pdf_merger.py        # PDF merging logic
├── pyproject.toml
├── .env.example
├── .gitignore
└── README.md
```

## Development

```bash
# Install with dev dependencies
poetry install

# Run tests (when available)
poetry run pytest

# Format code
poetry run black src/
poetry run isort src/
```

## Error Handling

- **API Failures**: Gracefully handles OpenAI API connection errors
- **Missing Files**: Skips files that the AI mentions but don't exist (logs a warning)
- **Empty Folder**: Exits clearly if no valid files are found
- **Large Batches**: Warns user when processing >20 files (may affect accuracy)

## License

MIT

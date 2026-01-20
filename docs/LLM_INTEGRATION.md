# Medical File Sorter - LLM Integration Guide

This document explains how the Medical File Sorter uses LLM (Large Language Model) vision capabilities to analyze, classify, and group medical documents.

---

## Architecture Overview

```mermaid
flowchart LR
    A[📁 Image Files] --> B[ImageProcessor]
    B --> C[Base64 Encoded Images]
    C --> D[LLMSorter]
    D --> E[OpenAI-compatible API]
    E --> F[JSON Response]
    F --> G[Validation]
    G --> H[display_groups]
    H --> I[📊 Formatted Output]
```

---

## Step 1: Image Processing

**File**: [image_processor.py](file:///Users/jatinbansal/Documents/Code/medical-bills-organiser/src/medical_file_sorter/image_processor.py)

Before calling the LLM, images are converted to Base64 strings:

```python
# ImageProcessor.process_folder() returns:
{
    "Report 0.HEIC": "base64_encoded_string...",
    "Report 0b.HEIC": "base64_encoded_string...",
    "Report 3a.jpg": "base64_encoded_string...",
}
```

---

## Step 2: Calling the LLM

**File**: [llm_sorter.py](file:///Users/jatinbansal/Documents/Code/medical-bills-organiser/src/medical_file_sorter/llm_sorter.py)

### The API Request

The `LLMSorter.sort_documents()` method builds a multimodal API request:

```python
# Message structure sent to the LLM
messages = [
    {"role": "system", "content": SYSTEM_PROMPT},  # Instructions
    {"role": "user", "content": [
        {"type": "text", "text": "Please analyze these 5 medical documents:"},
        {"type": "text", "text": "File: Report 0.HEIC"},
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,/9j/4AAQ..."}},
        {"type": "text", "text": "File: Report 0b.HEIC"},
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,/9j/4BBR..."}},
        # ... more files
    ]}
]
```

### The System Prompt

The `SYSTEM_PROMPT` instructs the LLM to:
1. **Classify** documents as Prescription or Bill
2. **Group** related documents (matching medicines, same doctor, same hospital)
3. **Extract** patient name and bill amounts
4. **Return** structured JSON

---

## Step 3: LLM Response

The LLM returns a JSON object with this structure:

```json
{
    "groups": [
        {
            "files": ["prescription1.pdf", "bill1.pdf"],
            "patient_name": "John Doe",
            "bill_amount": 1250.50,
            "summary": "Prescription and bills from Dr. Smith for antibiotics"
        },
        {
            "files": ["prescription2.png", "bill2.jpg"],
            "patient_name": "Jane Smith", 
            "bill_amount": 500.00,
            "summary": "Eye checkup prescription and pharmacy bill"
        }
    ],
    "uncategorized": ["unclear_document.jpg"]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `groups` | Array | List of related document groups |
| `groups[].files` | Array | Filenames belonging to this group |
| `groups[].patient_name` | String | Extracted patient name |
| `groups[].bill_amount` | Number | Total bill amount (₹) |
| `groups[].summary` | String | Why these documents are related |
| `uncategorized` | Array | Files that couldn't be grouped |

---

## Step 4: Validation

**Method**: `LLMSorter.validate_result()`

Before using the response, we validate it:

```python
def validate_result(self, result, known_files):
    # 1. Remove hallucinated filenames (LLM might invent files)
    # 2. Add missing files to uncategorized
    # 3. Ensure all fields have defaults
    
    for group in result["groups"]:
        valid_files = [f for f in group["files"] if f in known_files]
        # Keep only real files...
```

This prevents issues where the LLM might:
- Return filenames that don't exist
- Miss some files entirely
- Return malformed data

---

## Step 5: Display Output

**File**: [main.py](file:///Users/jatinbansal/Documents/Code/medical-bills-organiser/src/medical_file_sorter/main.py)

The `display_groups()` function formats the validated result:

```python
def display_groups(sort_result):
    total_bill_amount = 0.0
    
    for idx, group in enumerate(groups, 1):
        patient_name = group.get("patient_name", "Unknown")
        bill_amount = group.get("bill_amount", 0)
        summary = group.get("summary", "")
        files = group.get("files", [])
        
        total_bill_amount += bill_amount
        
        print(f"🗂️  Group {idx} (Transaction):")
        print(f"    👤 Patient: {patient_name}")
        print(f"    📝 {summary}")
        print(f"    💰 Bill Amount: ₹{bill_amount:,.2f}")
        for filename in files:
            print(f"    • {filename}")
    
    print(f"💵 TOTAL BILLS PAID: ₹{total_bill_amount:,.2f}")
```

### Final Output

```
============================================================
📋 DOCUMENT ORGANIZATION RESULTS
============================================================

🗂️  Group 1 (Transaction):
    👤 Patient: John Doe
    📝 Prescription and bills from Dr. Smith for antibiotics
    💰 Bill Amount: ₹1,250.50
    • Report 0.HEIC
    • Report 0b.HEIC

🗂️  Group 2 (Transaction):
    👤 Patient: Jane Smith
    📝 Eye checkup prescription and pharmacy bill
    💰 Bill Amount: ₹500.00
    • Report 3a.jpg
    • Report 3b.jpg

📁 Uncategorized (1 files):
    • Report 0c.HEIC

============================================================

💵 TOTAL BILLS PAID: ₹1,750.50
============================================================
```

---

## Supported Backends

| Backend | Base URL | API Key Required |
|---------|----------|------------------|
| OpenAI | `api.openai.com` | Yes (`OPENAI_API_KEY`) |
| OpenRouter | `openrouter.ai/api/v1` | Yes (`OPENROUTER_API_KEY`) |
| LM Studio | `localhost:1234/v1` | No (local) |

All backends use the OpenAI-compatible API format, so the same client works for all.

---

## Error Handling

The code handles several edge cases:

1. **JSON parsing errors** - Attempts to extract JSON from markdown code blocks
2. **Empty responses** - Raises clear error if model doesn't support vision
3. **Hallucinated files** - Filters out non-existent filenames
4. **Missing files** - Adds unmentioned files to uncategorized
5. **Missing fields** - Provides sensible defaults (0 for amounts, "Unknown" for names)

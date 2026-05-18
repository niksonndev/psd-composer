# psd-composer

Production-grade automated mockup generation pipeline for print-on-demand e-commerce. Integrates with Airtable, Photoshop, image compression, and FTP delivery. Drop a PNG design → get hundreds of organized, web-optimized JPGs automatically delivered.

---

## Pipeline Overview

```
Airtable Polling
    ↓
Poll "Pending" designs → Download PNG attachment
    ↓
Run ExtendScript 3× (main, marketing, print batches)
    ↓
Apply artwork + iterate color layers → Export JPGs
    ↓
Compress JPGs (Pillow) → Upload to FTP
    ↓
Update Airtable status → Move to next design
```

**Key features:**

- Automatic polling every 60s (configurable)
- Processes 3 batch types per design (main mockups, marketing, print files)
- Applies design PNG + iterates all available colors
- Automatic image compression with configurable quality
- FTP upload with folder organization
- Error handling + logging with rotating file handler
- All credentials via `.env` — no hardcoded secrets

---

## Prerequisites

- **Windows** machine with Adobe Photoshop 2020+ installed
- **Python 3.10+**
- **Airtable** account with properly configured base:
  - `Designs` table with fields: Design Name, Artist Name, Design PNG (attachment), Status, Notes
  - `Colors` table with field: Name
- **FTP server** (optional, leave credentials blank to skip upload)

---

## Setup

### 1. Install dependencies

```bash
git clone https://github.com/niksonndev/psd-composer
cd psd-composer
pip install -r requirements.txt
```

**Dependencies:**

- `requests` — Airtable API
- `python-dotenv` — environment configuration
- `Pillow` — image compression
- `ftplib` — (built-in) FTP uploads

### 2. Configure Airtable

1. Go to [airtable.com/create/tokens](https://airtable.com/create/tokens)
2. Create a new token with these scopes:
   - `data.records:read` — read designs and colors
   - `data.records:write` — update status
   - `schema.bases:read` — optional, for validation

3. Copy your **Base ID** from your base URL: `https://airtable.com/{BASE_ID}/...`

4. Set up your Airtable base with two tables:

**Designs table:**
| Design Name | Artist Name | Design PNG | Status | Notes |
|---|---|---|---|---|
| Iron-Aran | john-doe | [attachment] | Pending | — |

**Colors table:**
| Name |
|---|
| Black |
| Navy |
| Grey |

### 3. Configure environment

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Airtable
AIRTABLE_API_KEY=your_token_here
AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX

# Photoshop
PHOTOSHOP_EXE=C:/Program Files/Adobe/Adobe Photoshop 2024/Photoshop.exe
COMPOSER_JSX=C:/psd-composer/composer.jsx

# Templates (one per batch)
TEMPLATES_DIR_MAIN=C:/psd-composer/assets/templates/main
TEMPLATES_DIR_MARKETING=C:/psd-composer/assets/templates/marketing
TEMPLATES_DIR_PRINT=C:/psd-composer/assets/templates/print

# Output
OUTPUT_BASE_DIR=C:/psd-composer/assets/output

# FTP (optional)
FTP_HOST=ftp.example.com
FTP_USER=username
FTP_PASS=password
FTP_BASE_PATH=uploads/DTG

# Image quality
JPG_QUALITY=85

# Polling interval (seconds)
POLL_INTERVAL=60
```

### 4. Configure Photoshop templates

Each batch requires PSD templates with:

- **Layer named `ARTWORK`** — Smart Object for the design PNG
- **Color layers named `COLOR_{ColorName}`** — e.g., `COLOR_Black`, `COLOR_Navy`

The script will:

1. Replace the `ARTWORK` Smart Object with the PNG from Airtable
2. Iterate each color, hiding all except the active one
3. Export as `{DesignName}-{ProductCode}-{ColorName}.jpg`

### 5. Run the orchestrator

```bash
python main.py
```

The script will:

- Poll Airtable every 60 seconds for designs with Status = "Pending"
- Download the PNG attachment
- Process all three batches
- Compress and upload files
- Update Airtable with "Complete" or "Error" status
- Log everything to `logs/psd_composer.log` with rotation

---

## Adding colors dynamically

Edit the `Colors` table in Airtable — no code changes needed. Colors are fetched on each polling cycle.

Fallback to local `colors.json` if Airtable is unavailable:

```json
{
  "colors": [
    { "name": "Black" },
    { "name": "Navy" },
    { "name": "Grey" },
    { "name": "White" },
    { "name": "Maroon" }
  ]
}
```

---

## Adding new batches

To add a 4th batch (e.g., "apparel"), just add to `.env`:

```env
TEMPLATES_DIR_APPAREL=C:/psd-composer/assets/templates/apparel
```

Then update `main.py` line ~400 in `process_design()`:

```python
batches = [
    ("main", folders["original_apparel"]),
    ("marketing", folders["marketing"]),
    ("print", folders["print"]),
    ("apparel", folders["apparel"]),  # ADD THIS
]
```

And add the folder to `create_design_folders()`:

```python
folders = {
    # ... existing ...
    "apparel": str(base_path / "04 - APPAREL"),
}
```

---

## Logging

Logs are written to `logs/psd_composer.log` with automatic rotation at 10MB. Each log file is timestamped with:

- Poll cycle start/end
- Design processing (start, actions, completion)
- Batch execution status
- Image compression details
- FTP upload status
- Errors with full context

---

## Error handling

If a design fails at any point:

1. Exception is caught and logged with full traceback
2. Airtable Status is updated to "Error" with error details in Notes
3. Pipeline continues to the next design (no stopping)
4. Temp files are cleaned up automatically

---

## Performance notes

- Each design typically takes 2-5 minutes (depending on number of colors and PSD complexity)
- ExtendScript has 5-minute timeout per batch
- Polling has no CPU overhead when idle
- Image compression is single-threaded (can be parallelized in future)

---

## Development

### Running locally without Airtable

Comment out the Airtable integration and provide local design data:

```python
# In main():
# airtable = AirtableClient(...)
# pending_designs = airtable.get_records(...)

# Instead:
pending_designs = [{
    "id": "test-1",
    "fields": {
        "Design Name": "Test-Design",
        "Artist Name": "test-artist",
        "Design PNG": [{"url": "file:///C:/test.png"}],
        "Status": "Pending",
        "Notes": ""
    }
}]
```

### Testing ExtendScript

Open `composer.jsx` in Photoshop's ExtendScript IDE and edit the CONFIG section manually.

---

## Troubleshooting

| Problem                       | Solution                                         |
| ----------------------------- | ------------------------------------------------ |
| Photoshop not found           | Check PHOTOSHOP_EXE path in .env                 |
| Airtable connection fails     | Verify API_KEY and BASE_ID                       |
| No colors loaded              | Check Colors table exists and has "Name" field   |
| FTP upload fails              | Check credentials, server availability, firewall |
| ExtendScript timeout          | Reduce number of templates or colors             |
| PNG not found in Smart Object | Check PNG exists and ARTWORK layer name matches  |

---

## License

MIT

---

## Author

Created for print-on-demand mockup automation.]
}

````

Adding a new PSD template works the same way: drop it into the templates folder and it gets picked up automatically on the next run.

---

## Usage

```bash
python main.py --design "Iron-Aran" --png ./assets/iron-aran.png
````

That's it. The pipeline runs unattended and logs progress to the terminal.

---

## Output structure

```
Iron-Aran/
├── 00 - CSV/
├── 00 - MARKETING/
├── 01 - ORIGINAL/
│   ├── Apparel/
│   └── Accessories/
├── 02 - OPTIMIZED/
├── 03 - ART FILES/
└── Print-Files/
```

Files follow the naming convention `[Design-Name]-[Product-Code]-[Color].jpg`:

```
Iron-Aran-Men-Black.jpg
Iron-Aran-Hoodie-Back-Navy.jpg
Iron-Aran-Mug11-R-White.jpg
```

---

## Error handling

- Color not available in a PSD → skipped silently, logged to terminal
- Missing artwork layer → error logged, template skipped, pipeline continues
- Failed export → recorded in run summary, does not halt remaining templates

---

## Stack

- **ExtendScript (JSX)** — Photoshop automation, layer manipulation, JPG export
- **Python** — orchestration, file management, image compression
- **Airtable API** — work queue trigger and status updates

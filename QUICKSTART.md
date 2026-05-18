# PSD Composer - Quick Start Guide

## 5-Minute Setup

### 1. Create Airtable token

- Go to https://airtable.com/create/tokens
- Create token with scopes: `data.records:read`, `data.records:write`
- Copy token and Base ID from your base URL

### 2. Copy environment file

```bash
cp .env.example .env
```

### 3. Edit `.env`

```env
AIRTABLE_API_KEY=pat_xxxxx
AIRTABLE_BASE_ID=appXXXXX
PHOTOSHOP_EXE=C:/Program Files/Adobe/Adobe Photoshop 2024/Photoshop.exe
COMPOSER_JSX=C:/psd-composer/composer.jsx
# ... fill in other paths ...
```

### 4. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 5. Run

```bash
python main.py
```

---

## Setting up Airtable

### Create `Designs` table:

| Design Name | Artist Name | Design PNG   | Status  | Notes |
| ----------- | ----------- | ------------ | ------- | ----- |
| Iron-Aran   | john-doe    | [upload PNG] | Pending | —     |

**Field types:**

- Design Name: `Single line text`
- Artist Name: `Single line text`
- Design PNG: `Attachment`
- Status: `Single select` (options: Pending, Processing, Complete, Error)
- Notes: `Long text`

### Create `Colors` table:

| Name  |
| ----- |
| Black |
| Navy  |
| Grey  |

**Field type:**

- Name: `Single line text`

---

## Setting up Photoshop Templates

Each `.psd` template must have:

1. **An ARTWORK layer** (Smart Object) — where your PNG design goes
2. **Color layers** named `COLOR_Black`, `COLOR_Navy`, etc. — groups or layers

Example structure:

```
Main
├── ARTWORK (Smart Object)
├── COLOR_Black (Group)
│   ├── Shadow
│   └── Main Color
├── COLOR_Navy (Group)
│   ├── Shadow
│   └── Main Color
└── Background
```

The script will:

1. Replace ARTWORK with your PNG
2. For each color in Airtable:
   - Hide all color layers
   - Show only `COLOR_{ColorName}`
   - Export as JPG

---

## Folder Structure

The script creates this automatically:

```
output/
└── Iron-Aran/
    ├── 00 - CSV/
    ├── 00 - MARKETING/          ← Marketing batch JPGs
    ├── 01 - ORIGINAL/
    │   ├── Apparel/             ← Main batch JPGs
    │   └── Accessories/
    ├── 02 - OPTIMIZED/          ← Compressed JPGs (uploaded to FTP)
    ├── 03 - ART FILES/
    └── Print-Files/             ← Print batch JPGs
```

---

## Monitoring

Watch logs in real-time:

```bash
tail -f logs/psd_composer.log
```

Or view in any text editor.

---

## What happens when you run `python main.py`

1. **Poll Airtable** every 60 seconds
2. **Find designs** with Status = "Pending"
3. **For each design:**
   - Download PNG from attachment
   - Create folder structure
   - Run ExtendScript for MAIN batch
   - Run ExtendScript for MARKETING batch
   - Run ExtendScript for PRINT batch
   - Compress all JPGs (Pillow)
   - Upload to FTP server
   - Update Airtable Status to "Complete"
4. **On error:**
   - Log the error
   - Update Airtable Status to "Error" with details
   - Continue to next design (doesn't stop)

---

## Configuration Examples

### Adjust image quality

```env
JPG_QUALITY=75  # Lower = smaller file, faster upload (0-95)
```

### Change polling interval

```env
POLL_INTERVAL=30  # Check Airtable every 30 seconds instead of 60
```

### Skip FTP upload

Leave FTP credentials blank:

```env
FTP_HOST=
FTP_USER=
FTP_PASS=
```

### Add a 4th batch

In `.env`:

```env
TEMPLATES_DIR_APPAREL=C:/templates/apparel
```

Then update `main.py` (search for "batches = ["):

```python
batches = [
    ("main", folders["original_apparel"]),
    ("marketing", folders["marketing"]),
    ("print", folders["print"]),
    ("apparel", folders["apparel"]),  # NEW
]
```

And add folder in `create_design_folders()`:

```python
"apparel": str(base_path / "04 - APPAREL"),
```

---

## Troubleshooting

**"Photoshop not found"**

- Check that the exe path is correct: `Settings` → `About Photoshop` to see version
- Update PHOTOSHOP_EXE in `.env`

**"Airtable connection failed"**

- Verify token is correct (all 50+ characters)
- Verify Base ID is correct
- Check internet connection

**"No designs found"**

- Check Status field in Airtable is exactly "Pending"
- Check there's at least one record in Designs table

**"ExtendScript timeout"**

- Reduce number of colors in the batch
- Reduce number of PSD templates
- Increase timeout in main.py (line ~150)

**"FTP upload failed"**

- Verify FTP credentials are correct
- Check firewall allows FTP (ports 20, 21)
- Verify FTP user has write permissions

---

## Support

Check `logs/psd_composer.log` for detailed error messages with timestamps and full context.

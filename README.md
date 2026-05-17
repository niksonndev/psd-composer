# psd-composer

Automated mockup generation pipeline for print-on-demand e-commerce. Drop a PNG design, get hundreds of organized, web-optimized JPGs — no manual steps required.

---

## How it works

```
PNG uploaded → ExtendScript opens each PSD → applies artwork + color layers → exports JPGs → Python organizes, compresses, and delivers files
```

Each run processes all PSD templates across three batches (main mockups, marketing, print files), iterates through every available color, and skips silently if a color isn't defined in a given template.

---

## Prerequisites

- Windows machine with Adobe Photoshop CC installed
- Python 3.10+
- Airtable account (optional for local runs)

---

## Setup

```bash
git clone https://github.com/niksonndev/psd-composer
cd psd-composer
pip install -r requirements.txt
```

Point the script to your folders in `config.json`:

```json
{
  "templates_dir": "C:/mockups/templates",
  "output_dir": "C:/mockups/output"
}
```

---

## Adding or removing colors

Open `colors.json` and edit the list — no code changes needed:

```json
{
  "colors": ["Black", "Navy", "Grey", "White", "Maroon"]
}
```

Adding a new PSD template works the same way: drop it into the templates folder and it gets picked up automatically on the next run.

---

## Usage

```bash
python main.py --design "Iron-Aran" --png ./assets/iron-aran.png
```

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

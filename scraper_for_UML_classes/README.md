# UML Degree Pathway Scraper

## What it does

This script scrapes undergraduate degree pathway pages from the UMass Lowell catalog and writes a structured JSON file for the requested major into the repository `data/` directory (example: `data/cs-general-2020.json`). The scraper implementation is [`scraper.py`](scraper_for_UML_classes/scraper.py) and is intended to be run from the project root.

The scraper:
- Parses "Year" / "Semester" sections and course tables.
- Optionally follows course detail pages to collect descriptions and prerequisites.
- Saves output as JSON; the filename is derived by [`extract_filename_from_url`](scraper_for_UML_classes/scraper.py).

## Prerequisites
Install the packages
```bash
pip install -r requirements.txt
```

## Run from project root

Usage (general):
```bash
python scraper_for_UML_classes/scraper.py '<Major Name>' '<Catalog URL>'
```

Examples (from project root):
```bash
python scraper_for_UML_classes/scraper.py "Computer-Science" "https://www.uml.edu/catalog/undergraduate/sciences/departments/computer-science/degree-pathways/dp-cs-general-2020.aspx"

python scraper_for_UML_classes/scraper.py "Nursing" "https://www.uml.edu/catalog/undergraduate/health-sciences/departments/nursing/degree-pathways/dp-nursing-3.5year-2025.aspx"
```

## Output

- Files are written to the `data/` folder (e.g., [data/cs-general-2020.json](data/cs-general-2020.json)).
- The exact output filename is created by [`extract_filename_from_url`](scraper_for_UML_classes/scraper.py).


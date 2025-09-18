# Rate My Professor Scraper

## What it does

This script scrapes professor ratings from Rate My Professors for a list of instructors (or schools) and writes the results to the repository `data/` directory (for example, `data/rmp_professors.json`). The scraper is implemented in `professor_rating_scraper.py` and is intended to be run from the project root.

## Prerequisites

- Python 3.x installed on your system
- Install required Python packages from the project root:

```bash
pip install -r requirements.txt
```

## Run from project root

Invoke the scraper from the repository root (the folder that contains `requirements.txt`) with:

```bash
python3 scraper_for_rate_my_professor/professor_rating_scraper.py
```

## Notes

- If the script accepts command-line arguments (filters, output path, etc.), pass them after the script path. Check the top of `professor_rating_scraper.py` or its inline help for available options.
- The scraped output will typically be written to `data/rmp_professors.json` in this repository — confirm the exact output path in the script if you need to change it.

If you want, I can open `professor_rating_scraper.py` to confirm its exact arguments and output file and update this README with an exact command including flags.

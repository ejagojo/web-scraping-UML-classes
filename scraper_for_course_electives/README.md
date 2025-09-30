# UML Course Electives Scraper

## What it does

This script fetches course data from the University of Massachusetts Lowell Registrar API and normalizes the results into a simple JSON list of course records. It is implemented in `scraper_electives.py` and is intended to be run from the project root.

The script queries the registrar API by course subject prefix (e.g., `COMP`, `NURS`) and writes a cleaned JSON array to the output file you provide.

## Prerequisites

- Python 3.x
- Install required Python packages from the project root:

```bash
pip install -r requirements.txt
```

(If you use a virtual environment, activate it first.)

## Usage (from project root)

The script requires exactly two positional arguments: a subject prefix and an output filename.

Usage:

```bash
python scraper_for_course_electives/scraper_electives.py <PREFIX> <output_file.json>
```

- `<PREFIX>`: Course subject prefix to query (case-insensitive; script will uppercase it). Example: `COMP`, `CS`, `NURS`.
- `<output_file.json>`: Path to write normalized JSON. The script will create parent directories as needed.

Example (save Computer Science electives):

```bash
python3 scraper_for_course_electives/scraper_electives.py COMP data/ComputerScience/cs-electives-2025.json
```

Example (save Nursing electives):

```bash
python3 scraper_for_course_electives/scraper_electives.py NURS data/Nursing/nursing-electives-2025.json
```

## Output format

The output is a JSON array where each element is an object with the following keys:

- `course_number` (string or null) — Usually like `COMP.1000` or similar combined subject.catalog number.
- `course_name` (string or null) — The course title.
- `credits` — Credits or units for the course (type preserved from API, often number or string).
- `description` — Course description text.
- `prerequisites` — Text or structure returned by the API; when none found the script sets: "This class has no prerequisites."
- `offered_semesters` — Terms/semesters the course is offered, if present.

The script will skip records that don't contain at least a `course_number` or a `course_name` and print up to 5 sample keys for skipped records to help debugging.

## Notes, behavior, and troubleshooting

- The script calls the UML registrar endpoint:

  `https://www.uml.edu/api/registrar/course_catalog/v1.0/courses?field=subject&query=<PREFIX>`

  It sends a simple `User-Agent` header and a 20s timeout.

- Exit codes and errors:

  - If arguments are incorrect the script prints usage and exits with non-zero status.
  - Network errors or non-200 responses will print an error and exit non-zero.
  - Invalid JSON from the API will also exit non-zero.

- The script is resilient to schema drift: it tries multiple key names for subject, catalog number, title, description, etc. If many records are missing expected fields, check the printed sample keys to update the normalization logic.

- Prefixes: the registrar API expects the subject prefix used by UML. If unsure which prefix to use, try the department pages on UML or request a small prefix (e.g., `COMP`) and inspect the returned keys/records.

- Output directory creation: the script will create parent directories for the supplied output path with `os.makedirs(..., exist_ok=True)`.

## Quick sanity check

After running, open the JSON file and inspect the first few entries. Example (jq is helpful):

```bash
# show first 3 records (if you have jq installed)
jq '.[0:3]' data/ComputerScience/cs-electives-2025.json
```

## Where to look next / improvements

- Add a small wrapper to iterate multiple prefixes and merge results into a single file.
- Add a `--dry-run` flag to only print counts without writing files.
- Add unit tests for `normalize_record` using sample API payloads.

---

Files changed:

- `scraper_for_course_electives/README.md` — README for `scraper_electives.py` (this file).

If you want, I can also open `scraper_electives.py` to add a `--help` flag or add a small runner script that calls multiple prefixes and writes to `data/`.

# Web Scraping Classes Project

This project contains two web scrapers:

1. A UMass Lowell degree pathway scraper
2. A Rate My Professor scraper

Both scrapers work together to collect course information and professor ratings, storing the results in JSON format.

## Project Structure

```
.
├── data/                           # Output directory for scraped data
│   ├── cs-general-2020.json       # Computer Science pathway data
│   ├── nursing-3.5year-2025.json  # Nursing pathway data
│   └── rmp_professors.json        # Professor ratings data
├── scraper_for_UML_classes/       # UML degree pathway scraper
│   ├── README.md
│   └── scraper.py
├── scraper_for_rate_my_professor/ # Rate My Professor scraper
│   ├── README.md
│   └── professor_rating_scraper.py
└── requirements.txt               # Python package dependencies
```

## Prerequisites

### Python Setup

This project requires Python 3.x. Here's how to set up a virtual environment on different operating systems:

#### On macOS/Linux:

```bash
# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

#### On Windows:

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
.\venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

## Using the Scrapers

### 1. UML Degree Pathway Scraper

This scraper collects course information from UMass Lowell's degree pathway pages.

To run the scraper:

```bash
python scraper_for_UML_classes/scraper.py "<Major Name>" "<Catalog URL>"
```

Example commands:

```bash
# Scrape Computer Science pathway
python scraper_for_UML_classes/scraper.py "Computer Science" "https://www.uml.edu/catalog/undergraduate/sciences/departments/computer-science/degree-pathways/dp-cs-general-2020.aspx"

# Scrape Nursing pathway
python scraper_for_UML_classes/scraper.py "Nursing" "https://www.uml.edu/catalog/undergraduate/health-sciences/departments/nursing/degree-pathways/dp-nursing-3.5year-2025.aspx"
```

Output will be saved to the `data/` directory with a filename derived from the URL (e.g., `cs-general-2020.json`).

### 2. Rate My Professor Scraper

This scraper collects professor ratings from Rate My Professor.

To run the scraper:

```bash
python scraper_for_rate_my_professor/professor_rating_scraper.py
```

Output will be saved to `data/rmp_professors.json`.

## Output Data

All scraped data is stored in JSON format in the `data/` directory:

- `cs-general-2020.json`: Computer Science degree pathway information
- `nursing-3.5year-2025.json`: Nursing degree pathway information
- `rmp_professors.json`: Professor ratings from Rate My Professor

## Deactivating the Virtual Environment

When you're done working with the project:

```bash
deactivate
```

This command works the same way on both Windows and macOS/Linux.

## Required Python Packages

- requests: For making HTTP requests
- beautifulsoup4: For parsing HTML
- lxml: XML and HTML parser

These are all specified in `requirements.txt` and will be installed automatically when following the setup instructions above.

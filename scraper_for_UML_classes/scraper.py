import requests
from bs4 import BeautifulSoup, Tag
import json
import time
import sys
import os

BASE_URL = "https://www.uml.edu"
HEADERS = {"User-Agent": "UML-Scraper/1.0 (Academic Research; contact: your-email@uml.edu)"}

def fetch_page(url):
    """Safely fetch the webpage and return HTML."""
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()
    return response.text

def fetch_course_details(course_url):
    """Scrape a course page for description and prerequisites."""
    full_url = BASE_URL + course_url
    time.sleep(5)  # throttle to avoid hammering UML servers
    html = fetch_page(full_url)
    soup = BeautifulSoup(html, "lxml")

    details = {"description": None, "prerequisites": None}

    desc_header = soup.find("h3", string="Description")
    if desc_header:
        desc_p = desc_header.find_next("p")
        if desc_p:
            details["description"] = desc_p.get_text(" ", strip=True)

    prereq_header = soup.find("h3", string="Prerequisites")
    if prereq_header:
        prereq_p = prereq_header.find_next("p")
        if prereq_p:
            details["prerequisites"] = prereq_p.get_text(" ", strip=True)
    else:
        details["prerequisites"] = "This class has no prerequisites."

    return details

def parse_course_table(table):
    """Extract all rows from a course table into a list of dicts."""
    courses = []
    rows = table.find("tbody").find_all("tr")
    for row in rows:
        cols = row.find_all("td")
        if len(cols) == 3:
            link_tag = cols[0].find("a")
            course_url = link_tag["href"] if link_tag else None

            course_number = cols[0].get_text(" ", strip=True)
            course_name = cols[1].get_text(" ", strip=True)
            try:
                credits = int(cols[2].get_text(strip=True))
            except ValueError:
                credits = cols[2].get_text(strip=True)

            course_data = {
                "course_number": course_number,
                "course_name": course_name,
                "credits": credits,
                "description": None,
                "prerequisites": None
            }

            if course_url:
                details = fetch_course_details(course_url)
                course_data.update(details)

            courses.append(course_data)
    return courses

def parse_pathway(html, major):
    """Parse the degree pathway into a JSON structure."""
    soup = BeautifulSoup(html, "lxml")
    data = {"major": major, "pathway": {}}

    for year_header in soup.find_all("h2"):
        year_name = year_header.get_text(strip=True)
        if "Year" not in year_name:
            continue

        year_data = {}
        current_sem = None

        for el in year_header.next_elements:
            if isinstance(el, Tag) and el.name == "h2":
                break

            if isinstance(el, Tag) and el.name == "h3":
                current_sem = el.get_text(strip=True)

            if isinstance(el, Tag) and el.name == "table" and current_sem:
                year_data.setdefault(current_sem, []).extend(parse_course_table(el))

        if year_data:
            data["pathway"][year_name] = year_data

    return data

def extract_filename_from_url(url):
    """Turn a UML catalog URL into a clean filename."""
    last_part = url.strip().split("/")[-1]      # e.g. dp-cs-general-2020.aspx
    name = last_part.replace("dp-", "").replace(".aspx", "")
    return name

def main():
    if len(sys.argv) != 3:
        print("Usage: python scraper.py '<Major Name>' '<Catalog URL>'")
        sys.exit(1)

    major = sys.argv[1]
    url = sys.argv[2]

    html = fetch_page(url)
    data = parse_pathway(html, major)

    os.makedirs("data", exist_ok=True)
    filename_key = extract_filename_from_url(url)
    filename = f"data/{filename_key}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ Scraping complete. Data saved to {filename}")

if __name__ == "__main__":
    main()

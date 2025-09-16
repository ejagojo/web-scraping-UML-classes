import requests
from bs4 import BeautifulSoup
import json
import time

BASE_URL = "https://www.uml.edu"
URL = f"{BASE_URL}/catalog/undergraduate/sciences/departments/computer-science/degree-pathways/dp-cs-general-2020.aspx"
HEADERS = {"User-Agent": "UML-CS-Scraper/1.0 (Academic Research; contact: your-email@uml.edu)"}

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
        # Sometimes there are no prerequisites section
        details["prerequisites"] = "This class has no prerequisites."

    return details

def parse_course_table(table):
    """Extract all rows from a course table into a list of dicts."""
    courses = []
    rows = table.find("tbody").find_all("tr")
    for row in rows:
        cols = row.find_all("td")
        if len(cols) == 3:
            # Look for link to course detail page
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

            # If we have a course link, fetch details
            if course_url:
                details = fetch_course_details(course_url)
                course_data.update(details)

            courses.append(course_data)
    return courses

def parse_pathway(html):
    """Parse the degree pathway into a JSON structure."""
    soup = BeautifulSoup(html, "lxml")

    data = {"major": "Computer Science", "pathway": {}}

    # Each year section is an <h2>
    for year_header in soup.find_all("h2"):
        year_name = year_header.get_text(strip=True)
        if "Year" not in year_name:
            continue  # skip things like "Notes"

        year_data = {}
        year_section = year_header.find_next("div", class_="row")
        if not year_section:
            continue

        semesters = year_section.find_all("div", class_="column")
        for sem in semesters:
            sem_header = sem.find("h3")
            if not sem_header:
                continue
            sem_name = sem_header.get_text(strip=True)

            # course table inside this semester
            table = sem.find("table")
            if table:
                year_data[sem_name] = parse_course_table(table)

        data["pathway"][year_name] = year_data

    return data

def main():
    html = fetch_page(URL)
    data = parse_pathway(html)

    # Save JSON
    with open("data/catalog.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("✅ Scraping complete. Data saved to data/catalog.json")

    # Preview sample: Freshman Fall Semester
    # print(json.dumps(data["pathway"]["Freshman Year"]["Fall Semester"], indent=2))

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# /school/Fall2025/MobileAppProgrammingI/finalProject/web-scraping-classes/scraper_for_course_electives/scraper_electives.py

import requests
import json
import sys
import os
from typing import Any, Dict, Iterable, List

HEADERS = {
    "User-Agent": "HawkAdvisor-Scraper/1.0 (Academic Project; ejagojo@gmail.com)"
}

API_URL = "https://www.uml.edu/api/registrar/course_catalog/v1.0/courses"

def fetch_course_data(prefix: str) -> Any:
    """
    Call UML registrar API:
      https://www.uml.edu/api/registrar/course_catalog/v1.0/courses?field=subject&query=<PREFIX>
    Returns parsed JSON (list or dict, depending on API).
    """
    params = {"field": "subject", "query": prefix}
    print(f"🔎 Requesting {prefix} courses from {API_URL} with params {params}")
    resp = requests.get(API_URL, headers=HEADERS, params=params, timeout=20)
    resp.raise_for_status()
    return resp.json()

def to_lower_keys(d: Dict[str, Any]) -> Dict[str, Any]:
    """Return a copy of dict with lower-cased keys for case-insensitive access."""
    return { (k.lower() if isinstance(k, str) else k): v for k, v in d.items() }

def pick(d: Dict[str, Any], candidates: Iterable[str]) -> Any:
    """
    Return first non-empty value in d for any candidate key (case-insensitive).
    Candidates should be provided in lower-case.
    """
    for k in candidates:
        if k in d and d[k] not in (None, "", []):
            return d[k]
    return None

def normalize_record(rec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map an arbitrary course record from the API into our normalized structure.
    Tries multiple aliases and falls back safely.
    """
    lower = to_lower_keys(rec)

    # Try subject
    subject = pick(lower, ["subject", "subjectcode", "subj", "dept", "department", "prefix"])

    # Try catalog/course number
    catalog = pick(lower, [
        "catalognbr", "catalog_nbr", "catalognumber", "catalog", "number",
        "coursenumber", "course_number", "course_num", "cnum", "catnum"
    ])

    # Try combined code like "COMP.1000"
    code = pick(lower, ["code", "coursecode", "id"])

    # Compose course_number
    course_number = None
    if subject and catalog:
        course_number = f"{str(subject).strip()}.{str(catalog).strip()}"
    elif code:
        # If code exists (e.g., "COMP.1000"), use it directly
        course_number = str(code).strip()

    # Title
    title = pick(lower, ["title", "coursename", "name", "longtitle", "long_title"])

    # Credits
    credits = pick(lower, ["mincredits", "credits", "credithours", "units", "credit"])

    # Description
    description = pick(lower, ["description", "descr", "desc", "course_description"])

    # Prerequisites
    prerequisites = pick(lower, ["prerequisites", "prereq", "requisites", "requirements"])
    if not prerequisites:
        prerequisites = "This class has no prerequisites."

    # Terms offered / semesters
    offered_semesters = pick(lower, ["termsoffered", "terms", "offeredterms", "offered", "semesters", "term"])

    return {
        "course_number": course_number,
        "course_name": title,
        "credits": credits,
        "description": description,
        "prerequisites": prerequisites,
        "offered_semesters": offered_semesters
    }

def coerce_to_list(api_json: Any) -> List[Dict[str, Any]]:
    """
    The API *usually* returns a list; if it returns a dict wrapper,
    try common container keys like 'data', 'results', 'items'.
    """
    if isinstance(api_json, list):
        return api_json

    if isinstance(api_json, dict):
        lower = to_lower_keys(api_json)
        for key in ["data", "results", "items", "courses", "payload"]:
            if key in lower and isinstance(lower[key], list):
                return lower[key]
        # Some APIs return dict of id->record
        # Fall back: if values look like dicts, convert to list
        if all(isinstance(v, dict) for v in lower.values()):
            return list(lower.values())

    # Last resort: wrap single object
    return [api_json]

def format_courses(api_data: Any) -> List[Dict[str, Any]]:
    """
    Normalize API results into desired JSON format, robust to schema drift.
    """
    raw_list = coerce_to_list(api_data)

    normalized: List[Dict[str, Any]] = []
    skipped_samples: List[Dict[str, Any]] = []

    for rec in raw_list:
        if not isinstance(rec, dict):
            continue
        norm = normalize_record(rec)
        # Require at least course_number or course_name
        if not norm["course_number"] and not norm["course_name"]:
            if len(skipped_samples) < 5:
                skipped_samples.append({"keys": list(rec.keys()), "sample": rec})
            continue
        normalized.append(norm)

    if skipped_samples:
        print(f"⚠️ Skipped {len(skipped_samples)} records without identifiable keys.")
        # Print just the keys to help you adjust quickly
        for i, s in enumerate(skipped_samples, 1):
            print(f"   • Sample {i} keys: {s['keys']}")

    return normalized

def main():
    if len(sys.argv) != 3:
        print("Usage: python scraper_electives.py <PREFIX> <output_file.json>")
        sys.exit(1)

    prefix = sys.argv[1].upper()
    output_file = sys.argv[2]

    try:
        api_json = fetch_course_data(prefix)
        final = format_courses(api_json)
    except requests.HTTPError as e:
        print(f"❌ HTTP error: {e}")
        sys.exit(1)
    except requests.RequestException as e:
        print(f"❌ Request error: {e}")
        sys.exit(1)
    except json.JSONDecodeError:
        print("❌ API did not return valid JSON.")
        sys.exit(1)

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final, f, indent=2, ensure_ascii=False)

    print(f"✅ Done. Saved {len(final)} {prefix} courses to {output_file}")

if __name__ == "__main__":
    main()

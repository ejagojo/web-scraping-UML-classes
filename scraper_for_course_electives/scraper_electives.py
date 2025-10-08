#!/usr/bin/env python3

import requests
import json
import sys
import os
from typing import Any, Dict, List

HEADERS = {
    "User-Agent": "HawkAdvisor-Scraper/1.0 (Academic Project; your-email@example.com)",
    "Referer": "https://www.uml.edu/student-dashboard/",
}

API_URL = "https://www.uml.edu/student-dashboard/api/ClassSchedule/RealTime/Search/"

def fetch_course_data(search_type: str, query: str, term: str = "3510") -> List[Dict[str, Any]]:
    """
    Calls the single, powerful student dashboard API to search for courses.
    """
    # Base parameters required for any search
    params = {
        "term": term,
        "page": 1,
        "pageSize": 5000,
        # --- THIS IS THE CRITICAL FIX ---
        "courseOfferingModes": "1" # '1' specifies "Undergraduate Classes"
    }

    # Add the specific search type parameter
    if search_type == 'prefix':
        params['subjects'] = query
    elif search_type == 'core':
        params['coreCurriculumBOKs'] = query
    else:
        return []

    print(f"🔎 Requesting data from {API_URL} with params: {params}")
    try:
        resp = requests.get(API_URL, headers=HEADERS, params=params, timeout=30)
        resp.raise_for_status()
        
        data = resp.json().get('data', {})
        return data.get('Classes', [])
        
    except requests.RequestException as e:
        print(f"    - Error: Could not fetch data. Error: {e}")
        return []

def normalize_record(rec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Maps a course record from the new API into our final normalized structure.
    """
    details = rec.get('Details', {})
    
    course_number = f"{details.get('Subject', '')}.{details.get('CatalogNumber', '')}"
    course_name = details.get('CourseTitle')
    credits = details.get('MinimumCredits')
    description = details.get('CourseDescription')
    prereqs = details.get('EnrollmentRequirements')
    
    if not prereqs:
        prereqs = "This class has no prerequisites."

    return {
        "course_number": course_number,
        "course_name": course_name,
        "credits": credits,
        "description": description,
        "prerequisites": prereqs,
        "offered_semesters": None
    }

def main():
    if len(sys.argv) != 4:
        print("Usage: python scraper_electives.py <TYPE> <QUERY> <output_file.json>")
        print("\nExamples:")
        print("  python scraper_electives.py prefix COMP data/ComputerScience/comp_electives.json")
        print("  python scraper_electives.py core AH data/CoreCurriculum/arts_humanities.json")
        sys.exit(1)

    search_type = sys.argv[1].lower()
    query = sys.argv[2].upper()
    output_file = sys.argv[3]

    raw_course_data = []
    
    try:
        if search_type in ['prefix', 'core']:
            raw_course_data = fetch_course_data(search_type, query)
        else:
            print(f"❌ Error: Unknown search_type '{search_type}'. Use 'prefix' or 'core'.")
            sys.exit(1)

        unique_courses = {}
        for course_record in raw_course_data:
            normalized = normalize_record(course_record)
            if normalized['course_number'] and normalized['course_number'] not in unique_courses:
                unique_courses[normalized['course_number']] = normalized
        
        final_data = list(unique_courses.values())

    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        sys.exit(1)

    output_dir = os.path.dirname(output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Done. Saved {len(final_data)} unique courses for '{query}' to {output_file}")

if __name__ == "__main__":
    main()
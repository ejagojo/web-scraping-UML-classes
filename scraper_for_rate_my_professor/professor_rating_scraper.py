import requests
import json
import time

URL = "https://www.ratemyprofessors.com/graphql"
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (compatible; UML-Scraper/1.0; +contact@uml.edu)"
}

# GraphQL query string
QUERY = """
query TeacherSearchPaginationQuery($count: Int!, $cursor: String, $query: TeacherSearchQuery!) {
  search: newSearch {
    teachers(query: $query, first: $count, after: $cursor) {
      edges {
        cursor
        node {
          id
          legacyId
          firstName
          lastName
          avgRating
          numRatings
          wouldTakeAgainPercent
          avgDifficulty
          department
          school { name id }
        }
      }
      pageInfo { hasNextPage endCursor }
      resultCount
    }
  }
}
"""

def scrape_professors(school_id, dept_id=None, max_pages=10):
    """Scrape professors for a given school (and optional department)."""
    professors = []
    cursor = None

    for _ in range(max_pages):
        variables = {
            "count": 20,   # fetch 20 at a time
            "cursor": cursor,
            "query": {
                "text": "",
                "schoolID": school_id,
                "fallback": True
            }
        }
        if dept_id:
            variables["query"]["departmentID"] = dept_id

        payload = {"query": QUERY, "variables": variables}

        resp = requests.post(URL, headers=HEADERS, json=payload)
        resp.raise_for_status()
        data = resp.json()

        teachers = data["data"]["search"]["teachers"]
        for edge in teachers["edges"]:
            node = edge["node"]
            prof = {
                "name": f"{node['firstName']} {node['lastName']}",
                "avgRating": node.get("avgRating"),
                "numRatings": node.get("numRatings"),
                "wouldTakeAgain": node.get("wouldTakeAgainPercent"),
                "avgDifficulty": node.get("avgDifficulty"),
                "department": node.get("department"),
                "school": node["school"]["name"]
            }
            professors.append(prof)

        if not teachers["pageInfo"]["hasNextPage"]:
            break
        cursor = teachers["pageInfo"]["endCursor"]

        time.sleep(2)  # throttle to avoid hitting too hard

    return professors

if __name__ == "__main__":
    # Example: UML schoolID (encoded) from your payload
    SCHOOL_ID = "U2Nob29sLTEzNjI="   # University of Massachusetts Lowell
    DEPT_ID = "RGVwYXJ0bWVudC0xMQ==" # Computer Science (optional)
    
    results = scrape_professors(SCHOOL_ID, dept_id=DEPT_ID, max_pages=10)

    with open("data/rmp_professors.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved {len(results)} professors to data/rmp_professors.json")

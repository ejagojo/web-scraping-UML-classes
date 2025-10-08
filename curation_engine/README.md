# 🎓 Hawk Advisor Curation Engine

## Overview

The **Curation Engine** is the intelligent recommendation system for the Hawk Advisor project. It automatically generates personalized academic roadmaps for students by enriching base degree pathways with AI-powered course recommendations tailored to specific career goals.

This engine analyzes degree requirements, career-specific skills, course catalogs, and prerequisites to provide context-aware elective recommendations that align with each student's professional aspirations.

---

## 📁 Directory Structure

```
curation_engine/
├── README.md               # This file
├── config.json            # Career definitions and keyword mappings
├── generate_roadmap.py    # Main recommendation engine
└── compare_roadmaps.py    # Validation and reporting tool
```

---

## 🔧 Files Overview

### 1. `config.json`

**Purpose:** Central configuration file that defines majors, career paths, and recommendation criteria.

**Structure:**

- **Major Configuration:** Maps majors to their base pathways and relevant course catalogs
- **Career Definitions:** Contains keyword weights for each career path
  - `tech_keywords`: Technical skills specific to the career (weighted 1-10)
  - `general_ed_keywords`: Relevant general education topics (weighted 1-10)
  - `negative_keywords`: Topics to avoid/filter out
- **Pathway Files:** Links career paths to base degree templates

**Example Entry:**

```json
{
  "career_name": "Frontend Developer",
  "base_pathway_name": "General Option",
  "tech_keywords": {
    "javascript": 10,
    "react": 10,
    "web": 8,
    "css": 8,
    "html": 8,
    "ui": 8
  },
  "general_ed_keywords": {
    "design": 10,
    "communication": 8,
    "visual": 5
  },
  "negative_keywords": ["music", "sculpture", "backend", "database"]
}
```

---

### 2. `generate_roadmap.py`

**Purpose:** Core recommendation engine that enriches base pathways with personalized course suggestions.

**Key Features:**

- 🎯 **Context-Aware Recommendations:** Considers year level, prerequisites, and courses already taken
- 📊 **Intelligent Scoring System:** Weights courses based on:
  - Keyword relevance (career-specific and general education)
  - Course level appropriateness
  - Prerequisite satisfaction
  - Year standing restrictions
- 🔍 **Smart Catalog Matching:** Automatically identifies correct course catalogs for elective types
- 🚫 **Negative Filtering:** Removes irrelevant courses using negative keywords
- 📝 **Transparency:** Includes selection reasoning for each recommendation

**Main Functions:**

- `score_course_relevance()`: Assigns relevance scores based on keywords and course level
- `find_best_courses()`: Context-aware recommender for specific elective slots
- `get_catalogs_for_elective()`: Maps elective types to appropriate course catalogs
- `parse_prerequisites()`: Extracts structured prerequisite information

**Scoring Algorithm:**

1. Match course against career-specific keywords (weighted scoring)
2. Filter out courses with negative keywords
3. Apply level appropriateness bonus (10 pts for exact match, 5 pts for ±1 level)
4. Add bonus for low-barrier courses (no prerequisites: +3 pts)
5. Validate prerequisites and standing requirements
6. Return top 5 ranked recommendations per elective slot

---

### 3. `compare_roadmaps.py`

**Purpose:** Quality assurance tool that generates human-readable reports comparing base pathways to enriched roadmaps.

**Key Features:**

- 📋 Identifies all enriched elective slots
- 🔍 Displays recommended courses with selection reasoning
- 📝 Generates Markdown reports for review

**Output Location:** `data/comparison_reports/`

---

## 🚀 Usage

### Generate Personalized Roadmaps

**Basic Command:**

```bash
python curation_engine/generate_roadmap.py
```

**What It Does:**

1. Reads configuration from `config.json`
2. Loads all course catalogs from `data/catalogs/`
3. Processes each major and career path defined in config
4. For each elective slot in the base pathway:
   - Identifies relevant course catalog(s)
   - Filters courses by prerequisites and restrictions
   - Scores courses based on career relevance
   - Selects top 5 recommendations
5. Saves enriched roadmaps to `data/curated_roadmaps/{Major}/{career-name}.json`

**Expected Output:**

```
--- Starting Hawk Advisor Curation Engine (Context-Aware Version) ---

Processing Major: Computer_Science
  -> Generating recommendations for: Frontend Developer
    📘 Processing Freshman Year - Fall Semester
     ✅ Matched elective 'Computer Science Elective' → Catalogs: ['comp_courses.json']
    📘 Processing Sophomore Year - Spring Semester
     ✅ Matched elective 'Natural Science with Lab (SCL)' → Catalogs: ['sciences_with_lab.json']
     ✅ Saved enriched roadmap: data/curated_roadmaps/Computer_Science/frontend-developer.json

--- ✅ Curation Engine Finished Successfully ---
```

---

### Generate Comparison Reports

**Command:**

```bash
python curation_engine/compare_roadmaps.py <MajorKey>
```

**Examples:**

```bash
# Generate report for Computer Science major
python curation_engine/compare_roadmaps.py Computer_Science

# Generate report for Nursing major
python curation_engine/compare_roadmaps.py Nursing
```

**Sample Output:**

```
--- Generating Comparison Report for Major: Computer_Science ---
✅ Report successfully generated at: data/comparison_reports/Computer_Science_comparison_report.md
```

**Report Format:**

```markdown
# Comparison Report for Major: Computer_Science

## Frontend Developer

**Based on:** General Option

### Enriched Elective Slots with Recommendations

#### Recommendations for: `COMP.XXXX - Computer Science Elective`

- COMP.3610 - Web Programming I
  - _Selection Logic: Matches: (javascript, web, html, css). level-appropriate_
- COMP.4610 - Web Programming II
  - _Selection Logic: Matches: (javascript, react, web). level-appropriate_
```

---

## 📊 Example Use Cases

### Use Case 1: New Career Path

**Scenario:** Adding "DevOps Engineer" to Computer Science careers

1. Edit `config.json` and add:

```json
{
  "career_name": "DevOps Engineer",
  "base_pathway_name": "General Option",
  "tech_keywords": {
    "docker": 10,
    "kubernetes": 10,
    "ci/cd": 10,
    "automation": 8,
    "cloud": 8,
    "linux": 8
  },
  "general_ed_keywords": {
    "systems": 10,
    "communication": 8,
    "problem solving": 5
  },
  "negative_keywords": ["ui", "ux", "design", "art"]
}
```

2. Run the generator:

```bash
python curation_engine/generate_roadmap.py
```

3. Review the output:

```bash
python curation_engine/compare_roadmaps.py Computer_Science
```

---

### Use Case 2: Validating Recommendations

**Scenario:** Ensuring recommendations are appropriate for a specific career

1. Generate roadmaps:

```bash
python curation_engine/generate_roadmap.py
```

2. Generate comparison report:

```bash
python curation_engine/compare_roadmaps.py Computer_Science
```

3. Review `data/comparison_reports/Computer_Science_comparison_report.md` to verify:
   - Recommended courses match career goals
   - Selection reasoning makes sense
   - No irrelevant courses were suggested

---

### Use Case 3: Testing Configuration Changes

**Scenario:** Tweaking keyword weights to improve recommendations

1. Update keyword weights in `config.json`
2. Run generator:

```bash
python curation_engine/generate_roadmap.py
```

3. Compare results:

```bash
python curation_engine/compare_roadmaps.py Computer_Science
cat data/comparison_reports/Computer_Science_comparison_report.md
```

4. Iterate until recommendations are optimized

---

## 🔍 How It Works

### Recommendation Pipeline

```
Base Pathway → Identify Electives → Match Catalogs → Filter Prerequisites
                                                              ↓
                                           Score & Rank ← Apply Keywords
                                                              ↓
                                           Top 5 Selections → Add to Roadmap
```

### Elective Type Detection

The engine automatically detects elective types using pattern matching:

| Elective Name Pattern                             | Matched Catalog                |
| ------------------------------------------------- | ------------------------------ |
| "Natural Science", "SCL", "with lab"              | `sciences_with_lab.json`       |
| "Computer Science Elective", "Technical Elective" | `comp_courses.json`            |
| "Arts and Humanities", "(AH"                      | `arts_humanities_courses.json` |
| "Social Sciences", "(SS"                          | `social_sciences_courses.json` |
| "Free Elective"                                   | All relevant catalogs          |

### Prerequisite Validation

The engine respects:

- ✅ Course prerequisites (e.g., COMP.1010 required before COMP.2010)
- ✅ Standing requirements (Junior/Senior standing)
- ✅ Major restrictions (Majors only)
- ❌ Courses requiring instructor permission (filtered out)

---

## 🎯 Configuration Tips

### Keyword Strategy

**High Weights (8-10):**

- Core technologies/skills for the career
- Must-have competencies

**Medium Weights (5-7):**

- Complementary skills
- Secondary technologies

**Low Weights (1-4):**

- Nice-to-have skills
- Tangentially related topics

**Negative Keywords:**

- Topics that would mislead recommendations
- Completely irrelevant subjects
- Courses that waste elective slots

### Best Practices

1. **Be Specific:** Use exact technical terms (e.g., "react" not just "web")
2. **Balance Weights:** Don't make everything weight 10
3. **Test Iterations:** Generate → Review → Adjust → Repeat
4. **Use Negative Keywords:** Prevent obviously wrong recommendations
5. **Consider Context:** General ed keywords should support career soft skills

---

## 📦 Input Requirements

The engine expects the following data structure:

```
data/
├── catalogs/              # Course catalogs (JSON)
│   ├── comp_courses.json
│   ├── arts_humanities_courses.json
│   ├── social_sciences_courses.json
│   ├── sciences_with_lab.json
│   └── nurse_courses.json
└── pathways/              # Base degree pathways (JSON)
    ├── computer_science/
    │   ├── cs-general-2020.json
    │   ├── cs-data-science-2020.json
    │   └── cs-cybersecurity-2020.json
    └── nursing/
        └── nursing-4year-2025.json
```

---

## 🐛 Troubleshooting

### No Recommendations Generated

**Symptoms:** Elective slots remain empty after running generator

**Solutions:**

1. Check that keywords match course descriptions (case-insensitive)
2. Verify catalog files are properly loaded
3. Ensure negative keywords aren't too broad
4. Review prerequisite requirements (may be filtering out all candidates)

### Irrelevant Recommendations

**Symptoms:** Suggested courses don't match career goals

**Solutions:**

1. Add negative keywords to filter out unwanted topics
2. Increase weights for more specific technical keywords
3. Review and adjust keyword definitions in `config.json`
4. Check catalog matching logic in `get_catalogs_for_elective()`

### Missing Elective Detection

**Symptoms:** Engine doesn't recognize certain elective slots

**Solutions:**

1. Add pattern matching in `get_catalogs_for_elective()` function
2. Verify elective naming convention in base pathway files
3. Check for typos in course names

---

## 🔮 Future Enhancements (TODOs)

The following improvements are planned:

- [ ] **Rank by Relevance:** Sort recommendations by better alignment with career goals
- [ ] **Sequential Awareness:** Don't recommend courses already taken in previous semesters
- [ ] **Keyword Optimization:** Improve matching accuracy with NLP techniques
- [ ] **Enhanced Filtering:** Expand negative keyword database
- [ ] **Prerequisite Chains:** Recommend courses that unlock valuable future options
- [ ] **Professor Integration:** Factor in RateMyProfessor data for recommendations

---

## 📝 Output Format

Generated roadmaps follow this structure:

```json
{
  "major": "Computer Science",
  "option": "General Option",
  "pathway": {
    "Freshman Year": {
      "Fall Semester": [
        {
          "course_number": "COMP.XXXX",
          "course_name": "Computer Science Elective",
          "credits": 3,
          "recommended_options": [
            {
              "course_number": "COMP.3610",
              "course_name": "Web Programming I",
              "credits": 3,
              "description": "Introduction to web development...",
              "prerequisites": "COMP.2010",
              "selection_reason": "Matches: (javascript, web, html). level-appropriate"
            }
          ]
        }
      ]
    }
  }
}
```

---

## 🤝 Contributing

To add new features or fix bugs:

1. Test changes locally with sample data
2. Run comparison reports to validate output
3. Update this README if adding new functionality
4. Document any new configuration options

---

## 📞 Support

For issues or questions:

- Review comparison reports for validation
- Check console output for debugging information
- Examine selection reasoning in generated roadmaps

---

## 📄 License

Part of the Hawk Advisor project for UMass Lowell.

---

**Last Updated:** October 2025  
**Version:** 2.0 (Context-Aware Engine)

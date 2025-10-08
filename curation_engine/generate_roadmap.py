import json
import os
import re
from copy import deepcopy

# --- Configuration ---
DATA_DIR = 'data'
OUTPUT_DIR = 'data/curated_roadmaps'
CONFIG_FILE = 'curation_engine/config.json'

# ---------------------------
# Utilities
# ---------------------------
def load_json_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def get_course_level(course):
    s = course.get('course_number', '') or ''
    m = re.search(r'\d+', s)
    return int(m.group()) if m else None

def course_prefix(code: str) -> str:
    return (code or '').split('.')[0]

def is_lab_course(course):
    name = (course.get('course_name') or '').lower()
    num = (course.get('course_number') or '')
    return (
        'lab' in name or 'laboratory' in name or
        bool(re.search(r'/\d{3,4}L\b', course.get('course_name', '') or '')) or
        num.endswith('L')
    )

# ---------------------------
# Prerequisites & Restrictions
# ---------------------------
NO_PREREQ_PHRASES = {
    'no prereq', 'no prerequisite', 'no prerequisites',
    'this class has no prerequisites', 'none', 'n/a'
}

DISALLOWED_SPECIAL_TYPES = [
    'capstone', 'internship', 'practicum', 'thesis', 'honors',
    'directed study', 'independent study', 'research seminar', 'research service learning',
    'senior seminar', 'seminar', 'fieldwork', 'co-op'
]

SCL_ALLOWED_PREFIXES = {'BIOL', 'LIFE', 'CHEM', 'ATMO', 'ENVI', 'GEOL', 'PHYS', 'RADI'}

def contains_disallowed_special_type(course) -> bool:
    name = (course.get('course_name') or '').lower()
    return any(word in name for word in DISALLOWED_SPECIAL_TYPES)

def detect_major_restriction(text: str) -> bool:
    if not text:
        return False
    s = text.lower()
    patterns = [
        r'\bmajors only\b',
        r'\blimited to [a-z&/\-\s]+ majors\b',
        r'\brestricted to [a-z&/\-\s]+ majors\b',
        r'\bopen only to [a-z&/\-\s]+ majors\b',
        r'\bcomputer science majors only\b'
    ]
    return any(re.search(p, s) for p in patterns)

# --- NEW: robust prereq parsing ---
PR_CODE_PATTERNS = [
    # ECON.2110 / MATH.1320 / PHYS.1010L
    re.compile(r'\b([A-Z]{2,5})\.(\d{3,4}L?)\b'),
    # ECON 2110 / MATH 1320 / PHYS 1010L
    re.compile(r'\b([A-Z]{2,5})\s+(\d{3,4}L?)\b'),
    # legacy numeric codes like 92.183, 14.110
    re.compile(r'\b(\d{2})\.(\d{3})\b')
]

ROMAN_II_PAT = re.compile(r'\b(ii|iib|2nd|2)\b', flags=re.I)

def normalize_code_tuple(t):
    # ('ECON','2110') -> 'ECON.2110', ('92','183') -> '#92.183' (unknown subject)
    if len(t) == 2 and t[0].isalpha():
        return f"{t[0].upper()}.{t[1].upper()}"
    if len(t) == 2 and t[0].isdigit():
        return f"#{t[0]}.{t[1]}"  # unknown dept, still treat as prereq code
    return None

def parse_prerequisites_struct(prereq_str: str):
    """
    Returns:
      {
        "codes": set([...]),              # normalized codes like ECON.2110 or '#92.183'
        "flags": set([...]),              # permission, junior_standing, senior_standing, majors_only, coreq_present
        "logic": "any" | "all",
        "raw_has_prereq": bool,           # true if text clearly indicates a prereq requirement even if codes unreadable
    }
    """
    result = {"codes": set(), "flags": set(), "logic": "all", "raw_has_prereq": False}
    if not prereq_str:
        return result

    s = prereq_str.strip().lower()

    # majors-only & other flags
    if detect_major_restriction(prereq_str):
        result["flags"].add("majors_only")
    if 'permission of instructor' in s or 'consent of instructor' in s:
        result["flags"].add("permission")
    if 'junior standing' in s:
        result["flags"].add("junior_standing")
    if 'senior standing' in s:
        result["flags"].add("senior_standing")
    if 'co-req' in s or 'coreq' in s or 'co req' in s:
        result["flags"].add("coreq_present")

    # no-prereq fast path
    if any(p in s for p in NO_PREREQ_PHRASES):
        return result

    # mark we saw prereq language
    if 'pre-req' in s or 'prereq' in s or 'prerequisite' in s or 'pre req' in s:
        result["raw_has_prereq"] = True

    # collect codes in multiple formats
    codes = set()
    for pat in PR_CODE_PATTERNS:
        for m in pat.findall(prereq_str):
            norm = normalize_code_tuple(m if isinstance(m, tuple) else tuple(m))
            if norm:
                codes.add(norm)
    result["codes"] = codes

    # OR logic if text includes 'or' near any codes; default ALL
    if re.search(r'\bor\b', s):
        result["logic"] = "any"
    else:
        result["logic"] = "all"

    return result

def prereqs_satisfied(struct, courses_taken: set, is_first_term: bool) -> bool:
    """
    - If explicit codes exist: enforce ANY/ALL.
    - If no codes but raw prereq language exists:
        * In the very first term, never satisfied.
        * Later, be conservative → treat as unsatisfied (we can't prove it's met).
    """
    codes = struct["codes"]

    if codes:
        if struct["logic"] == "any":
            return any(c in courses_taken for c in codes)
        return codes.issubset(courses_taken)

    if struct["raw_has_prereq"]:
        return False if is_first_term else False  # conservative: require explicit satisfaction
    return True

def categorize_elective(slot_name: str) -> str:
    s = (slot_name or '').lower()
    if ('science' in s and 'lab' in s) or 'scl' in s:
        return 'scl'
    if 'arts and humanities' in s or '(ah' in s:
        return 'ah'
    if 'social sciences' in s or '(ss' in s:
        return 'ss'
    if 'computer science' in s or 'technical' in s:
        return 'tech'
    if 'free elective' in s:
        return 'free'
    return 'other'

# --- STRONGER series guard (II before I) ---
def is_series_advanced_without_intro(course, courses_taken, all_courses):
    name = (course.get('course_name') or '').lower()
    if not ROMAN_II_PAT.search(name):
        # also catch words signaling advanced
        if not any(w in name for w in ['advanced', 'intermediate']) or 'introduction' in name:
            return False

    # tokenize, remove numerals/roman numerals and "formerly" clutter
    base = re.sub(r'\b(i{1,3}|iv|v|vi{0,3}|2nd|ii|2)\b', ' ', name)
    base = re.sub(r'\b(formerly|previously|honors|with lab|laboratory)\b', ' ', base)
    base_tokens = set(t for t in re.findall(r'[a-z]+', base) if t not in {'i','ii','iii','iv','v','vi','and','or'})

    # find plausible intro courses
    intro_codes = set()
    for c in all_courses:
        cn = (c.get('course_name') or '').lower()
        if 'intro' in cn or re.search(r'\b i\b', ' ' + cn + ' '):
            tokens = set(re.findall(r'[a-z]+', cn))
            # require good overlap
            if len(base_tokens & tokens) >= max(1, min(3, len(base_tokens))):
                intro_codes.add((c.get('course_number') or '').split('/')[0].strip())

        # also direct "I" vs "II" title pairs
        alt = re.sub(r'\b(ii|2nd|2)\b', ' i ', name)
        if re.sub(r'\s+', ' ', cn) == re.sub(r'\s+', ' ', alt):
            intro_codes.add((c.get('course_number') or '').split('/')[0].strip())

    return intro_codes and not any(ic in courses_taken for ic in intro_codes)

# ---------------------------
# Catalog mapping for slots
# ---------------------------
def get_catalogs_for_elective(elective_course, major_config):
    name = str(elective_course.get('course_name', '')).lower()
    cats = []
    if (re.search(r'natural\s*science', name) or
        re.search(r'\bSCL\b', elective_course.get('course_name', '') or '', flags=re.I) or
        'with lab' in name or 'science with lab' in name):
        cats.append('sciences_with_lab.json')
    elif 'computer science elective' in name or 'technical elective' in name:
        cats.append('comp_courses.json')
    elif 'arts and humanities' in name or '(ah' in name:
        cats.append('arts_humanities_courses.json')
    elif 'social sciences' in name or '(ss' in name:
        cats.append('social_sciences_courses.json')
    elif 'free elective' in name:
        cats.extend(major_config.get('relevant_catalogs', []))
    return cats

# ---------------------------
# Scoring & Ranking
# ---------------------------
def score_course_relevance(course, keywords, negative_keywords, target_year_level):
    text = (str(course.get('course_name', '')) + ' ' + str(course.get('description', ''))).lower()
    for neg in negative_keywords or []:
        if re.search(r'\b' + re.escape(neg.lower()) + r'\b', text):
            return (0, f"Disqualified by negative keyword: '{neg}'.")
    kw_score = 0
    hits = []
    for k, w in (keywords or {}).items():
        if re.search(r'\b' + re.escape(k.lower()) + r'\b', text):
            kw_score += w
            hits.append(k)
    if kw_score == 0:
        return (0, "")
    reasons = []
    if hits:
        reasons.append(f"Matches: ({', '.join(hits)})")

    lvl_bonus = 0
    lvl = get_course_level(course)
    band_note = None
    if lvl is not None:
        band = (lvl // 1000)
        diff = abs(band - target_year_level)
        if diff == 0:
            lvl_bonus = 10
            band_note = "ideal level band"
        elif diff == 1:
            lvl_bonus = 5
            band_note = "nearby level band"
        else:
            band_note = "level band mismatch"
    if band_note:
        reasons.append(band_note)

    s = (course.get('prerequisites') or '') + ' ' + (course.get('description') or '')
    sl = s.lower()
    if any(p in sl for p in NO_PREREQ_PHRASES):
        lvl_bonus += 3
        reasons.append("no prerequisites")

    return (kw_score + lvl_bonus, ". ".join(reasons))

# ---------------------------
# Recommendation engine
# ---------------------------
def find_best_courses(available_courses, career_def, year_name, semester_slot, courses_taken, scheduled_codes, elective_slot_name, count=5):
    target_year_level = {'freshman': 1, 'sophomore': 2, 'junior': 3, 'senior': 4}.get(
        (year_name or '').lower().split()[0], 0
    )
    slot_cat = categorize_elective(elective_slot_name or "")
    slot_credits = semester_slot.get('credits')
    is_first_term = (len(courses_taken) == 0)

    if slot_cat == 'tech':
        keywords = career_def.get('tech_keywords') or career_def.get('core_keywords') or {}
    else:
        keywords = career_def.get('general_ed_keywords') or {}
    neg_keywords = career_def.get('negative_keywords') or []

    eligible = []
    for c in available_courses:
        code = (c.get('course_number') or '').split('/')[0].strip()
        lvl = get_course_level(c)
        pref = course_prefix(code)
        cr = c.get('credits', 0) or 0

        if not lvl or lvl >= 5000:
            continue
        if cr is None or cr <= 0:
            continue  # drop 0.0 credit or unknown credit entries (e.g., bad CHEM.2230 data)

        # avoid duplicates already in required plan
        if code in scheduled_codes:
            continue

        if contains_disallowed_special_type(c):
            continue

        # majors-only restriction barred in gen-eds/free
        if detect_major_restriction(c.get('prerequisites', '')) or detect_major_restriction(c.get('description', '')):
            if slot_cat in ('ah', 'ss', 'free', 'scl'):
                continue

        # category constraints
        if slot_cat == 'scl':
            if pref not in SCL_ALLOWED_PREFIXES:
                continue
            # SCL must be a single 4+ credit lecture-with-lab OR an explicit lab course (but we won't offer naked labs)
            looks_lab = is_lab_course(c)
            if not looks_lab and cr < 4:
                continue
            if lvl >= 3000:
                continue

        elif slot_cat in ('ah', 'ss'):
            if lvl >= 3000:
                continue

        elif slot_cat == 'tech':
            if target_year_level >= 3 and lvl < 2000:
                continue
            if target_year_level >= 4 and lvl < 3000:
                continue

        # prereq structure
        struct = parse_prerequisites_struct(c.get('prerequisites', '') or '')
        if 'permission' in struct["flags"]:
            continue
        if 'junior_standing' in struct["flags"] and target_year_level < 3:
            continue
        if 'senior_standing' in struct["flags"] and target_year_level < 4:
            continue
        if 'coreq_present' in struct["flags"] and not any(cc in courses_taken for cc in struct["codes"]):
            continue
        if not prereqs_satisfied(struct, courses_taken, is_first_term):
            # also gate obvious series (II before I)
            if is_series_advanced_without_intro(c, courses_taken, available_courses):
                continue
            continue

        eligible.append(c)

    # score + annotate
    scored = []
    for c in eligible:
        s, reason = score_course_relevance(c, keywords, neg_keywords, target_year_level)
        if s <= 0:
            continue
        notes = [reason]
        if slot_cat == 'scl' and is_lab_course(c):
            notes.append("lab verified")
        cc = deepcopy(c)
        cc['selection_reason'] = ". ".join([n for n in notes if n])
        scored.append((s, cc))

    scored.sort(key=lambda x: x[0], reverse=True)

    # dedupe & take top N with rank
    final = []
    seen = set()
    rank = 1
    for _, c in scored:
        code = (c.get('course_number') or '').split('/')[0].strip()
        if code in seen:
            continue
        seen.add(code)
        c['rank'] = rank
        rank += 1
        final.append(c)
        if len(final) >= count:
            break

    return final

# ---------------------------
# Main
# ---------------------------
def main():
    print("--- Starting Hawk Advisor Curation Engine (strict prereq + SCL logic) ---")

    config = load_json_file(CONFIG_FILE)
    if not config:
        print(f"FATAL: Could not load configuration from {CONFIG_FILE}. Exiting.")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    catalog_dir = os.path.join(DATA_DIR, 'catalogs')
    all_catalog_data = {
        f: load_json_file(os.path.join(catalog_dir, f))
        for f in os.listdir(catalog_dir) if f.endswith('.json')
    }

    for major_key, major_config in config.items():
        print(f"\nProcessing Major: {major_key}")
        pathways_dir = os.path.join(DATA_DIR, 'pathways', major_config['pathways_dir_name'])
        major_output_dir = os.path.join(OUTPUT_DIR, major_config['output_dir_name'])
        os.makedirs(major_output_dir, exist_ok=True)

        for career in major_config['careers']:
            career_name = career['career_name']
            base_pathway_name = career['base_pathway_name']
            print(f"  -> Generating recommendations for: {career_name}")

            base_file = major_config['pathway_files'].get(base_pathway_name)
            if not base_file:
                print(f"     ⚠️  No base pathway file for '{base_pathway_name}'. Skipping.")
                continue

            base_pathway_path = os.path.join(pathways_dir, base_file)
            base_pathway = load_json_file(base_pathway_path)
            if not base_pathway:
                print(f"     ⚠️  Cannot load base pathway '{base_pathway_path}'. Skipping.")
                continue

            enriched = deepcopy(base_pathway)

            # Attach high-level metadata for UI/DB
            enriched['career_metadata'] = {
                "major_key": major_key,
                "career_name": career_name,
                "base_pathway_name": base_pathway_name,
                "keywords_used": {
                    "tech_keywords_or_core": career.get('tech_keywords') or career.get('core_keywords') or {},
                    "general_ed_keywords": career.get('general_ed_keywords') or {},
                    "negative_keywords": career.get('negative_keywords') or []
                }
            }
            enriched['db_bindings'] = {
                "Majors.Name": major_key.replace('_', ' '),
                "CareerPaths.Name": career_name,
                "DegreePathways.Name": base_pathway_name
            }

            # Compute required codes to avoid dup recs
            scheduled_codes = set()
            for years in base_pathway.get('pathway', {}).values():
                for sem_courses in years.values():
                    for c in sem_courses:
                        code = (c.get('course_number') or '').split('/')[0].strip()
                        if code and 'xxxx' not in code.lower():
                            scheduled_codes.add(code)

            courses_taken_so_far = set()

            # iterate terms in order
            for year_name, semesters in enriched['pathway'].items():
                for semester_name, semester_courses in semesters.items():
                    for course in semester_courses:
                        name = str(course.get('course_name', '')).lower()
                        num = str(course.get('course_number', '')).lower()
                        is_elective = ('elective' in name) or ('xxxx.xxxx' in num)
                        if not is_elective:
                            continue

                        catalogs = get_catalogs_for_elective(course, major_config)
                        pool = []
                        for cat in catalogs:
                            pool.extend(all_catalog_data.get(cat, []) or [])

                        recs = find_best_courses(
                            pool, career, year_name, course,
                            courses_taken_so_far, scheduled_codes,
                            course.get('course_name'), count=5
                        )
                        if recs:
                            course['recommended_options'] = recs
                        else:
                            # prefer silence over wrong recs
                            course.pop('recommended_options', None)

                    # mark completed after the term
                    for c in semester_courses:
                        code = (c.get('course_number') or '').split('/')[0].strip()
                        if code and 'xxxx' not in code.lower():
                            courses_taken_so_far.add(code)

            out_name = f"{career_name.lower().replace(' ', '-').replace('/', '-')}.json"
            out_path = os.path.join(major_output_dir, out_name)
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(enriched, f, indent=2, ensure_ascii=False)
            print(f"     ✅ Saved enriched roadmap: {out_path}")

    print("\n--- ✅ Curation Engine Finished Successfully ---")

if __name__ == "__main__":
    main()

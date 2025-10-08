import json
import os
import sys

# --- Configuration ---
DATA_DIR = 'data'
OUTPUT_DIR = 'data/curated_roadmaps'
REPORTS_DIR = 'data/comparison_reports'
CONFIG_FILE = 'curation_engine/config.json' # Reads from the same config

def load_json_file(file_path):
    """Safely loads a single JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def find_enriched_electives(roadmap_data):
    """Finds all course objects that have been enriched with recommendations."""
    enriched_electives = []
    if not roadmap_data or 'pathway' not in roadmap_data:
        return enriched_electives
    for year in roadmap_data['pathway'].values():
        for semester in year.values():
            for course in semester:
                if 'recommended_options' in course and course['recommended_options']:
                    enriched_electives.append(course)
    return enriched_electives

def main():
    """Main function to find and report on enriched electives in generated roadmaps."""
    config = load_json_file(CONFIG_FILE)
    if not config:
        print(f"FATAL: Could not load configuration from {CONFIG_FILE}. Exiting.")
        return

    if len(sys.argv) != 2:
        print("Usage: python compare_roadmaps.py <MajorKey>")
        print(f"Example: python compare_roadmaps.py {list(config.keys())[0]}")
        sys.exit(1)
        
    major_to_compare = sys.argv[1]
    
    if major_to_compare not in config:
        print(f"Error: Major key '{major_to_compare}' not found in {CONFIG_FILE}.")
        sys.exit(1)

    os.makedirs(REPORTS_DIR, exist_ok=True)
    output_filename = f"{major_to_compare}_comparison_report.md"
    output_path = os.path.join(REPORTS_DIR, output_filename)

    print(f"--- Generating Comparison Report for Major: {major_to_compare} ---")

    with open(output_path, 'w', encoding='utf-8') as report_file:
        report_file.write(f"# Comparison Report for Major: {major_to_compare}\n\n")
        report_file.write("This report shows the recommended courses that were automatically appended to each elective slot.\n\n")
        
        major_config = config[major_to_compare]
        
        pathways_dir = os.path.join(DATA_DIR, 'pathways', major_config['pathways_dir_name'])
        output_dir = os.path.join(OUTPUT_DIR, major_config['output_dir_name'])
        
        for career in major_config['careers']:
            career_name = career['career_name']
            base_pathway_name = career['base_pathway_name']
            
            report_file.write(f"## {career_name}\n")
            report_file.write(f"**Based on:** `{base_pathway_name}`\n\n")
            
            generated_filename = f"{career_name.lower().replace(' ', '-').replace('/', '-')}.json"
            generated_pathway_path = os.path.join(output_dir, generated_filename)
            generated_roadmap_data = load_json_file(generated_pathway_path)
            
            if not generated_roadmap_data:
                 print(f"Warning: Could not find generated file for '{career_name}' at {generated_pathway_path}")
                 report_file.write("Could not find the generated roadmap file for this career path.\n\n---\n\n")
                 continue
            
            enriched_slots = find_enriched_electives(generated_roadmap_data)
            
            if not enriched_slots:
                report_file.write("No specific recommendations were generated for the elective slots in this path.\n\n")
            else:
                report_file.write("### Enriched Elective Slots with Recommendations\n\n")
                for slot in enriched_slots:
                    original_slot_name = f"`{slot.get('course_number')} - {slot.get('course_name')}`"
                    report_file.write(f"#### Recommendations for: {original_slot_name}\n")
                    
                    recommendations = slot.get('recommended_options', [])
                    for rec in recommendations:
                        rec_name = f"{rec.get('course_number')} - {rec.get('course_name')}"
                        report_file.write(f"* {rec_name}\n")
                        
                        reason = rec.get('selection_reason')
                        if reason:
                            report_file.write(f"  * *Selection Logic: {reason}*\n")

                    report_file.write("\n")

            report_file.write("---\n\n")

    print(f"✅ Report successfully generated at: {output_path}")

if __name__ == "__main__":
    main()
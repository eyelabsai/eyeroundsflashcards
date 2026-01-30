"""
Extract all atlas entries from EyeRounds JS database and organize by category
"""
import requests
import re
import json
import os

CATEGORIES = [
    'CATARACT', 'CONTACT LENS', 'CORNEA', 'EXTERNAL DISEASE', 'GENETICS',
    'GLAUCOMA', 'INHERITED DISEASE', 'IRIS', 'LENS', 'NEURO-OP', 
    'PATHOLOGY', 'OCULOPLASTICS', 'RETINA', 'SYSTEMS', 'TRAUMA', 
    'UVEITIS', 'VITREOUS'
]

def parse_js_object(obj_str):
    """Parse a JavaScript object string into a Python dict"""
    entry = {}
    
    # Extract string fields - handle escaped quotes
    for field in ['name', 'imgSrc', 'src', 'title', 'keyWords']:
        # Try single quotes first
        pattern = rf"{field}\s*:\s*'((?:[^'\\]|\\.)*)'"
        match = re.search(pattern, obj_str)
        if match:
            entry[field] = match.group(1).replace("\\'", "'")
        else:
            # Try double quotes
            pattern = rf'{field}\s*:\s*"((?:[^"\\]|\\.)*)"'
            match = re.search(pattern, obj_str)
            if match:
                entry[field] = match.group(1).replace('\\"', '"')
    
    # Extract year and numImg (can be string or number)
    for field in ['year', 'numImg']:
        match = re.search(rf"{field}\s*:\s*'?(\d+)'?", obj_str)
        if match:
            entry[field] = match.group(1)
    
    # Extract categories array
    cat_match = re.search(r"cat\s*:\s*\[(.*?)\]", obj_str, re.DOTALL)
    if cat_match:
        cats_str = cat_match.group(1)
        cats = re.findall(r"'([^']*)'", cats_str)
        if not cats:
            cats = re.findall(r'"([^"]*)"', cats_str)
        entry['cat'] = cats
    else:
        # Single category
        cat_match = re.search(r"cat\s*:\s*'([^']*)'", obj_str)
        if cat_match:
            entry['cat'] = [cat_match.group(1)]
    
    return entry

def main():
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0'})
    
    print("Fetching atlas database...")
    response = session.get('https://eyerounds.org/atlas/atlasJS/atlasJS_revision_22.js')
    js = response.text
    
    # Find linkInformationDB
    start = js.find('linkInformationDB = [')
    if start == -1:
        print("Database not found!")
        return
    
    start = js.find('[', start)
    
    # Find closing bracket by counting
    depth = 0
    end = start
    for i, c in enumerate(js[start:]):
        if c == '[': 
            depth += 1
        elif c == ']': 
            depth -= 1
        if depth == 0:
            end = start + i + 1
            break
    
    raw_array = js[start:end]
    print(f"Found database: {len(raw_array)} chars")
    
    # Parse entries by finding each { ... } block at the top level
    entries = []
    i = 0
    brace_depth = 0
    bracket_depth = 0
    obj_start = -1
    
    while i < len(raw_array):
        c = raw_array[i]
        
        # Skip strings
        if c in ["'", '"']:
            quote = c
            i += 1
            while i < len(raw_array):
                if raw_array[i] == '\\':
                    i += 2
                    continue
                if raw_array[i] == quote:
                    break
                i += 1
            i += 1
            continue
        
        if c == '[':
            bracket_depth += 1
        elif c == ']':
            bracket_depth -= 1
        elif c == '{':
            if brace_depth == 0 and bracket_depth == 1:
                obj_start = i
            brace_depth += 1
        elif c == '}':
            brace_depth -= 1
            if brace_depth == 0 and bracket_depth == 1 and obj_start >= 0:
                obj_str = raw_array[obj_start:i+1]
                entry = parse_js_object(obj_str)
                if entry.get('name') or entry.get('title') or entry.get('src'):
                    entries.append(entry)
                obj_start = -1
        
        i += 1
    
    print(f"Parsed {len(entries)} entries")
    
    # Organize by category
    by_category = {cat: [] for cat in CATEGORIES}
    by_category['OTHER'] = []
    
    for entry in entries:
        cats = entry.get('cat', [])
        if not cats:
            by_category['OTHER'].append(entry)
            continue
        
        added = False
        for cat in cats:
            cat_upper = cat.upper().strip()
            for std_cat in CATEGORIES:
                if std_cat in cat_upper or cat_upper in std_cat or std_cat.replace('-', ' ') in cat_upper:
                    by_category[std_cat].append(entry)
                    added = True
                    break
        if not added:
            by_category['OTHER'].append(entry)
    
    # Print summary
    print("")
    print("=" * 60)
    print("ATLAS ENTRIES BY CATEGORY")
    print("=" * 60)
    
    total = 0
    for cat in CATEGORIES + ['OTHER']:
        count = len(by_category[cat])
        if count > 0:
            print(f"{cat}: {count} entries")
            total += count
    
    print(f"\nTotal: {total} entries (some may be in multiple categories)")
    
    # Create data directory
    os.makedirs('data', exist_ok=True)
    
    # Save master database
    output = {
        'all_entries': entries,
        'by_category': by_category,
        'categories': CATEGORIES
    }
    
    with open('data/atlas_database.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nSaved master database to data/atlas_database.json")
    
    # Save individual category files
    for cat in CATEGORIES:
        if by_category[cat]:
            filename = f"data/{cat.lower().replace(' ', '_').replace('-', '_')}.json"
            with open(filename, 'w') as f:
                json.dump({
                    'category': cat,
                    'count': len(by_category[cat]),
                    'entries': by_category[cat]
                }, f, indent=2)
            print(f"  Saved {filename}: {len(by_category[cat])} entries")
    
    # Show sample entries
    print("")
    print("=" * 60)
    print("SAMPLE ENTRIES")
    print("=" * 60)
    for cat in ['RETINA', 'CORNEA', 'GLAUCOMA']:
        if by_category[cat]:
            print(f"\n{cat} ({len(by_category[cat])} total):")
            for e in by_category[cat][:3]:
                title = e.get('title', e.get('name', 'Unknown'))
                src = e.get('src', 'N/A')
                print(f"  - {title}")
                if src != 'N/A':
                    print(f"    URL: {src}")

if __name__ == "__main__":
    main()
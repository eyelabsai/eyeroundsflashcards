"""
Generate flashcards from scraped data (URLs only, no image downloads)
"""
import json
import os

CATEGORIES = [
    'CATARACT', 'CONTACT LENS', 'CORNEA', 'EXTERNAL DISEASE', 'GENETICS',
    'GLAUCOMA', 'INHERITED DISEASE', 'IRIS', 'LENS', 'NEURO-OP', 
    'PATHOLOGY', 'OCULOPLASTICS', 'RETINA', 'SYSTEMS', 'TRAUMA', 
    'UVEITIS', 'VITREOUS'
]

def generate_flashcards(data_dir='data'):
    print("=" * 60)
    print("GENERATING FLASHCARDS")
    print("=" * 60)
    
    all_flashcards = {}
    
    for cat in CATEGORIES:
        cat_file = cat.lower().replace(' ', '_').replace('-', '_')
        scraped_file = f'{data_dir}/{cat_file}_scraped.json'
        
        if not os.path.exists(scraped_file):
            print(f"  {cat}: No data file")
            continue
        
        with open(scraped_file, 'r') as f:
            data = json.load(f)
        
        entries = data.get('entries', [])
        flashcards = []
        
        for i, entry in enumerate(entries):
            flashcard = {
                'id': f"{cat_file}_{i}",
                'category': cat,
                'title': entry.get('title', 'Unknown'),
                'description': entry.get('description', ''),
                'contributor': entry.get('contributor', ''),
                'photographer': entry.get('photographer', ''),
                'source_url': entry.get('url', ''),
                'images': entry.get('images', []),
                'keywords': entry.get('keywords', ''),
                'year': entry.get('year', '')
            }
            flashcards.append(flashcard)
        
        all_flashcards[cat] = flashcards
        
        # Save per-category file
        with open(f'{data_dir}/{cat_file}_flashcards.json', 'w') as f:
            json.dump({
                'category': cat,
                'count': len(flashcards),
                'flashcards': flashcards
            }, f, indent=2)
        
        num_images = sum(len(fc['images']) for fc in flashcards)
        print(f"  {cat}: {len(flashcards)} flashcards, {num_images} images")
    
    # Save master file
    master_flashcards = []
    for cat in CATEGORIES:
        if cat in all_flashcards:
            master_flashcards.extend(all_flashcards[cat])
    
    with open(f'{data_dir}/all_flashcards.json', 'w') as f:
        json.dump({
            'total': len(master_flashcards),
            'categories': [c for c in CATEGORIES if c in all_flashcards],
            'flashcards': master_flashcards
        }, f, indent=2)
    
    total_images = sum(len(fc['images']) for fc in master_flashcards)
    
    print("")
    print("=" * 60)
    print(f"COMPLETE: {len(master_flashcards)} flashcards, {total_images} image URLs")
    print("=" * 60)
    print("")
    print("Files:")
    print(f"  {data_dir}/all_flashcards.json")
    for cat in CATEGORIES:
        cat_file = cat.lower().replace(' ', '_').replace('-', '_')
        if os.path.exists(f'{data_dir}/{cat_file}_flashcards.json'):
            print(f"  {data_dir}/{cat_file}_flashcards.json")


if __name__ == "__main__":
    generate_flashcards()
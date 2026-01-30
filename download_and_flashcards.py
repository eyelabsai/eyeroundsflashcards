"""
Download all images and generate flashcards for all categories
"""
import requests
import json
import os
import time
import hashlib
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

CATEGORIES = [
    'CATARACT', 'CONTACT LENS', 'CORNEA', 'EXTERNAL DISEASE', 'GENETICS',
    'GLAUCOMA', 'INHERITED DISEASE', 'IRIS', 'LENS', 'NEURO-OP', 
    'PATHOLOGY', 'OCULOPLASTICS', 'RETINA', 'SYSTEMS', 'TRAUMA', 
    'UVEITIS', 'VITREOUS'
]

class ImageDownloaderAndFlashcardGenerator:
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
        # Create image directories
        os.makedirs(f'{data_dir}/images', exist_ok=True)
        for cat in CATEGORIES:
            cat_dir = cat.lower().replace(' ', '_').replace('-', '_')
            os.makedirs(f'{data_dir}/images/{cat_dir}', exist_ok=True)
    
    def download_image(self, img_url, category):
        """Download a single image"""
        try:
            response = self.session.get(img_url, timeout=15)
            response.raise_for_status()
            
            # Generate filename from URL
            parsed = urlparse(img_url)
            ext = os.path.splitext(parsed.path)[1] or '.jpg'
            filename = hashlib.md5(img_url.encode()).hexdigest()[:12] + ext
            
            cat_dir = category.lower().replace(' ', '_').replace('-', '_')
            filepath = f'{self.data_dir}/images/{cat_dir}/{filename}'
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            return filepath
        except Exception as e:
            print(f"      Error: {img_url[:50]}... - {e}")
            return None
    
    def process_category(self, category):
        """Process a single category - download images and prepare flashcards"""
        cat_file = category.lower().replace(' ', '_').replace('-', '_')
        scraped_file = f'{self.data_dir}/{cat_file}_scraped.json'
        
        if not os.path.exists(scraped_file):
            print(f"  No data file for {category}")
            return []
        
        with open(scraped_file, 'r') as f:
            data = json.load(f)
        
        entries = data.get('entries', [])
        print(f"
  {category}: {len(entries)} entries")
        
        flashcards = []
        
        for i, entry in enumerate(entries):
            title = entry.get('title', 'Unknown')
            print(f"    [{i+1}/{len(entries)}] {title[:40]}...", end=' ')
            
            # Download images
            local_images = []
            for img in entry.get('images', []):
                img_url = img.get('url', '')
                if img_url:
                    local_path = self.download_image(img_url, category)
                    if local_path:
                        local_images.append({
                            'url': img_url,
                            'local_path': local_path,
                            'alt': img.get('alt', ''),
                            'figure_label': img.get('figure_label', '')
                        })
                    time.sleep(0.1)  # Rate limit
            
            print(f"{len(local_images)} images")
            
            # Create flashcard
            flashcard = {
                'id': f"{cat_file}_{i}",
                'category': category,
                'title': title,
                'description': entry.get('description', ''),
                'contributor': entry.get('contributor', ''),
                'photographer': entry.get('photographer', ''),
                'source_url': entry.get('url', ''),
                'images': local_images,
                'keywords': entry.get('keywords', ''),
                'year': entry.get('year', '')
            }
            
            flashcards.append(flashcard)
        
        # Save category flashcards
        with open(f'{self.data_dir}/{cat_file}_flashcards.json', 'w') as f:
            json.dump({
                'category': category,
                'count': len(flashcards),
                'flashcards': flashcards
            }, f, indent=2)
        
        return flashcards
    
    def process_all(self):
        """Process all categories"""
        print("="*60)
        print("DOWNLOADING IMAGES & GENERATING FLASHCARDS")
        print("="*60)
        
        all_flashcards = {}
        total_images = 0
        
        for cat in CATEGORIES:
            flashcards = self.process_category(cat)
            if flashcards:
                all_flashcards[cat] = flashcards
                total_images += sum(len(fc['images']) for fc in flashcards)
        
        # Save master flashcard file
        master_flashcards = []
        for cat, cards in all_flashcards.items():
            master_flashcards.extend(cards)
        
        with open(f'{self.data_dir}/all_flashcards.json', 'w') as f:
            json.dump({
                'total': len(master_flashcards),
                'categories': list(all_flashcards.keys()),
                'flashcards': master_flashcards
            }, f, indent=2)
        
        # Print summary
        print("
" + "="*60)
        print("COMPLETE")
        print("="*60)
        
        for cat in CATEGORIES:
            if cat in all_flashcards:
                cards = all_flashcards[cat]
                imgs = sum(len(fc['images']) for fc in cards)
                print(f"  {cat}: {len(cards)} flashcards, {imgs} images")
        
        print(f"
Total: {len(master_flashcards)} flashcards, {total_images} images downloaded")
        print(f"
Files created:")
        print(f"  - {self.data_dir}/all_flashcards.json (master file)")
        print(f"  - {self.data_dir}/{{category}}_flashcards.json (per category)")
        print(f"  - {self.data_dir}/images/{{category}}/ (images)")
        
        return all_flashcards


def main():
    generator = ImageDownloaderAndFlashcardGenerator()
    generator.process_all()


if __name__ == "__main__":
    main()

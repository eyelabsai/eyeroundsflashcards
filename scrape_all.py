"""
Scrape all EyeRounds atlas pages and images, organized by category
"""
import requests
from bs4 import BeautifulSoup
import json
import re
import os
import time
from urllib.parse import urljoin, urlparse
import hashlib

CATEGORIES = [
    'CATARACT', 'CONTACT LENS', 'CORNEA', 'EXTERNAL DISEASE', 'GENETICS',
    'GLAUCOMA', 'INHERITED DISEASE', 'IRIS', 'LENS', 'NEURO-OP', 
    'PATHOLOGY', 'OCULOPLASTICS', 'RETINA', 'SYSTEMS', 'TRAUMA', 
    'UVEITIS', 'VITREOUS'
]

class EyeRoundsFullScraper:
    def __init__(self, output_dir='data'):
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.base_url = 'https://eyerounds.org'
        self.webeye_base = 'https://webeye.ophth.uiowa.edu'
        
        # Create directories
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(f'{output_dir}/images', exist_ok=True)
        for cat in CATEGORIES:
            cat_dir = cat.lower().replace(' ', '_').replace('-', '_')
            os.makedirs(f'{output_dir}/images/{cat_dir}', exist_ok=True)
    
    def load_atlas_database(self):
        """Load the extracted atlas database"""
        with open(f'{self.output_dir}/atlas_database.json', 'r') as f:
            return json.load(f)
    
    def resolve_url(self, url, page_url=None):
        """Resolve a URL to absolute"""
        if not url:
            return None
        if url.startswith('http'):
            return url
        if url.startswith('//'):
            return 'https:' + url
        if url.startswith('/'):
            if page_url and 'webeye.ophth.uiowa.edu' in page_url:
                return urljoin(self.webeye_base, url)
            return urljoin(self.base_url, url)
        if page_url:
            return urljoin(page_url, url)
        return urljoin(self.base_url, url)
    
    def scrape_page(self, entry):
        """Scrape a single atlas page"""
        src = entry.get('src', '')
        if not src:
            return None
        
        # Build full URL - src already includes 'pages/' prefix
        if src.startswith('http'):
            url = src
        elif src.startswith('/'):
            url = self.base_url + src
        else:
            url = self.base_url + '/atlas/' + src
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
        except Exception as e:
            print(f"    Error fetching {url}: {e}")
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title = entry.get('title', '')
        if not title:
            h1 = soup.find('h1')
            if h1:
                title = h1.get_text().strip()
            else:
                title = entry.get('name', 'Unknown')
        
        # Extract category from page
        page_text = soup.get_text()
        category = self._extract_category(page_text, entry.get('cat', []))
        
        # Extract contributor
        contributor = ''
        contrib_pattern = r'Contributor[s]?[:\s]+([^\r\n]+?)(?=\r|\n|Photographer|Posted|Category)'
        contrib_match = re.search(contrib_pattern, page_text, re.I)
        if contrib_match:
            contributor = re.sub(r'\s+', ' ', contrib_match.group(1).strip())
        
        # Extract photographer
        photographer = ''
        photo_pattern = r'Photographer[s]?[:\s]+([^\r\n]+?)(?=\r|\n|Posted|Category)'
        photo_match = re.search(photo_pattern, page_text, re.I)
        if photo_match:
            photographer = re.sub(r'\s+', ' ', photo_match.group(1).strip())
        
        # Extract description
        description = self._extract_description(soup, page_text)
        
        # Extract images
        images = self._extract_images(soup, url)
        
        return {
            'title': title,
            'url': url,
            'category': category,
            'contributor': contributor,
            'photographer': photographer,
            'description': description,
            'images': images,
            'keywords': entry.get('keyWords', ''),
            'year': entry.get('year', '')
        }
    
    def _extract_category(self, page_text, entry_cats):
        """Extract category from page"""
        cat_match = re.search(r'Category\(?ies?\)?[:\s]+([^\r\n]+)', page_text, re.I)
        if cat_match:
            cat_text = cat_match.group(1).lower()
            for std_cat in CATEGORIES:
                if std_cat.lower() in cat_text:
                    return std_cat
        
        if entry_cats:
            cat = entry_cats[0].upper().strip()
            for std_cat in CATEGORIES:
                if std_cat in cat or cat in std_cat:
                    return std_cat
        
        return 'OTHER'
    
    def _extract_description(self, soup, page_text):
        """Extract description text"""
        patterns = [
            r'(?:Photographer[s]?:[^\r\n]+[\r\n]\s*)([A-Z][^.]*(?:\.[^.]*){1,5})',
            r'([A-Z][a-z]+ is (?:a |an |the )?[^.]*(?:\.[^.]*){1,3})',
            r'(This (?:patient|case|photograph)[^.]*(?:\.[^.]*){1,3})',
            r'(These (?:photographs|images)[^.]*(?:\.[^.]*){1,3})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, page_text, re.DOTALL)
            if match:
                desc = match.group(1).strip()
                desc = re.sub(r'\s+', ' ', desc)
                for marker in ['Image Permissions', 'Creative Commons', 'University of Iowa', 'Address', 'Related Articles', 'Enlarge', 'Download']:
                    if marker in desc:
                        desc = desc.split(marker)[0].strip()
                if len(desc) > 50:
                    return desc
        
        return ""
    
    def _extract_images(self, soup, page_url):
        """Extract all medical images from page"""
        images = []
        skip_patterns = [
            'cc.png', 'lowerLogo', 'DomeGold', 'eyerounds-logo', 
            'facebook', 'twitter', 'instagram', 'Eyerounds-500w',
            '/i/current/', 'logo', 'Logo', 'social', 'icon', 'banner'
        ]
        
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src')
            if not src:
                continue
            
            if any(skip.lower() in src.lower() for skip in skip_patterns):
                continue
            
            full_url = self.resolve_url(src, page_url)
            if not full_url:
                continue
            
            alt = img.get('alt', '')
            
            figure_label = ''
            parent = img.find_parent(['figure', 'div'])
            if parent:
                label_match = re.search(r'Figure\s+(\d+[a-z]?)', parent.get_text(), re.I)
                if label_match:
                    figure_label = label_match.group(0)
            
            images.append({
                'url': full_url,
                'alt': alt,
                'figure_label': figure_label
            })
        
        return images
    
    def download_image(self, img_url, category, filename=None):
        """Download an image and save it"""
        try:
            response = self.session.get(img_url, timeout=15)
            response.raise_for_status()
            
            if not filename:
                ext = os.path.splitext(urlparse(img_url).path)[1] or '.jpg'
                filename = hashlib.md5(img_url.encode()).hexdigest()[:12] + ext
            
            cat_dir = category.lower().replace(' ', '_').replace('-', '_')
            filepath = f'{self.output_dir}/images/{cat_dir}/{filename}'
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            return filepath
        except Exception as e:
            print(f"    Error downloading {img_url}: {e}")
            return None
    
    def scrape_category(self, category, entries, download_images=True):
        """Scrape all entries for a category"""
        print(f"\n{'='*60}")
        print(f"SCRAPING: {category} ({len(entries)} entries)")
        print('='*60)
        
        scraped = []
        
        for i, entry in enumerate(entries):
            title = entry.get('title', entry.get('name', 'Unknown'))
            print(f"  [{i+1}/{len(entries)}] {title[:50]}...")
            
            data = self.scrape_page(entry)
            if data:
                if download_images and data['images']:
                    for j, img in enumerate(data['images']):
                        local_path = self.download_image(img['url'], category)
                        if local_path:
                            data['images'][j]['local_path'] = local_path
                
                scraped.append(data)
                print(f"    OK: {len(data['images'])} images")
            else:
                print(f"    FAILED")
            
            time.sleep(0.3)
        
        cat_file = category.lower().replace(' ', '_').replace('-', '_')
        with open(f'{self.output_dir}/{cat_file}_scraped.json', 'w') as f:
            json.dump({
                'category': category,
                'count': len(scraped),
                'entries': scraped
            }, f, indent=2)
        
        print(f"\nSaved {len(scraped)} entries to {self.output_dir}/{cat_file}_scraped.json")
        
        return scraped
    
    def scrape_all(self, download_images=True, categories=None):
        """Scrape all categories"""
        db = self.load_atlas_database()
        by_category = db['by_category']
        
        if categories is None:
            categories = CATEGORIES
        
        all_scraped = {}
        
        for cat in categories:
            entries = by_category.get(cat, [])
            if entries:
                scraped = self.scrape_category(cat, entries, download_images)
                all_scraped[cat] = scraped
        
        with open(f'{self.output_dir}/all_scraped.json', 'w') as f:
            json.dump(all_scraped, f, indent=2)
        
        print("\n" + "="*60)
        print("SCRAPING COMPLETE")
        print("="*60)
        
        total_entries = 0
        total_images = 0
        for cat, entries in all_scraped.items():
            num_images = sum(len(e.get('images', [])) for e in entries)
            print(f"{cat}: {len(entries)} entries, {num_images} images")
            total_entries += len(entries)
            total_images += num_images
        
        print(f"\nTotal: {total_entries} entries, {total_images} images")
        
        return all_scraped


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape EyeRounds Atlas')
    parser.add_argument('--no-images', action='store_true', help='Skip downloading images')
    parser.add_argument('--category', type=str, help='Scrape only specific category')
    parser.add_argument('--output', type=str, default='data', help='Output directory')
    
    args = parser.parse_args()
    
    scraper = EyeRoundsFullScraper(output_dir=args.output)
    
    categories = None
    if args.category:
        categories = [args.category.upper()]
    
    scraper.scrape_all(
        download_images=not args.no_images,
        categories=categories
    )


if __name__ == "__main__":
    main()
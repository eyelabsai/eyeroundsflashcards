"""
Dedicated scraper for specific RETINA conditions from EyeRounds
Scrapes the 4 requested conditions and generates clean flashcards
"""
import requests
from bs4 import BeautifulSoup
import json
import re
import os
from urllib.parse import urljoin
import time

# Specific RETINA conditions to scrape
RETINA_CONDITIONS = [
    {
        'name': 'Acute Macular Neuroretinopathy (AMN)',
        'urls': [
            'https://eyerounds.org/atlas/pages/Acute-macular-neuroretinopathy/index.htm',
        ]
    },
    {
        'name': 'Acute Posterior Multifocal Placoid Pigment Epitheliopathy (APMPPE)',
        'urls': [
            'https://eyerounds.org/atlas/pages/apmppe/index.htm',
        ]
    },
    {
        'name': 'Leukemic Pseudohypopyon',
        'urls': [
            'https://eyerounds.org/atlas/pages/leukemic-pseudohypopyon.htm',
        ]
    },
    # Additional common RETINA conditions (verified working URLs)
    {
        'name': 'Central Serous Chorioretinopathy (CSCR)',
        'urls': [
            'https://eyerounds.org/atlas/pages/Central-Serous-Retinopathy-CSR.html',
        ]
    },
    {
        'name': 'Age-Related Macular Degeneration (AMD)',
        'urls': [
            'https://webeye.ophth.uiowa.edu/eyeforum/atlas/pages/AMD.htm',
        ]
    },
    {
        'name': 'Rhegmatogenous Retinal Detachment',
        'urls': [
            'https://eyerounds.org/atlas/pages/rhegmatogenous-ret-detach.htm',
        ]
    },
    {
        'name': 'Branch Retinal Vein Occlusion (BRVO)',
        'urls': [
            'https://eyerounds.org/atlas/pages/Branched-Retinal-Vein-Occlusion.html',
        ]
    },
    # Additional verified RETINA conditions
    {
        'name': 'Central Retinal Vein Occlusion (CRVO)',
        'urls': [
            'https://eyerounds.org/atlas/pages/CRVO/index.htm',
        ]
    },
    {
        'name': 'Central Retinal Artery Occlusion (CRAO)',
        'urls': [
            'https://eyerounds.org/atlas/pages/CRAO/index.htm',
        ]
    },
    {
        'name': 'Cytomegalovirus (CMV) Retinitis',
        'urls': [
            'https://eyerounds.org/atlas/pages/CMV-retinitis/index.htm',
        ]
    },
    {
        'name': 'Proliferative Diabetic Retinopathy (PDR)',
        'urls': [
            'https://eyerounds.org/atlas/pages/proliferative-diabetic-retinopathy/index.htm',
        ]
    },
]


class RetinaScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.base_url = 'https://eyerounds.org'
    
    def scrape_page(self, url, condition_name):
        """Scrape a single atlas page and extract flashcard data"""
        print(f"  Scraping: {url}")
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
        except Exception as e:
            print(f"    Warning: Failed to fetch: {e}")
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract page title
        title = self._extract_title(soup, condition_name)
        
        # Extract category
        category = self._extract_category(soup)
        
        # Extract description
        description = self._extract_description(soup)
        
        # Extract contributor and photographer
        contributor = self._extract_contributor(soup)
        photographer = self._extract_photographer(soup)
        
        # Extract images
        images = self._extract_images(soup, url)
        
        if not images:
            print(f"    Warning: No images found")
            return None
        
        return {
            'title': title,
            'condition': condition_name,
            'category': category,
            'description': description,
            'contributor': contributor,
            'photographer': photographer,
            'images': images,
            'url': url
        }
    
    def _extract_title(self, soup, fallback):
        """Extract the condition title from the page"""
        # Try h1 first
        h1 = soup.find('h1')
        if h1:
            title = h1.get_text().strip()
            # Clean up
            title = re.sub(r'\s+', ' ', title)
            if title and len(title) > 3 and 'ophthalmology' not in title.lower():
                return title
        
        # Try h2
        h2 = soup.find('h2')
        if h2:
            title = h2.get_text().strip()
            title = re.sub(r'\s+', ' ', title)
            if title and len(title) > 3 and 'ophthalmology' not in title.lower():
                return title
        
        return fallback
    
    def _extract_category(self, soup):
        """Extract category from the page"""
        text = soup.get_text()
        
        # Look for Category pattern
        match = re.search(r'Category\(?ies?\)?[:\s]+([^\r\n]+)', text, re.I)
        if match:
            cat_text = match.group(1).lower()
            if 'retina' in cat_text or 'vitreous' in cat_text:
                return 'RETINA'
            elif 'glaucoma' in cat_text:
                return 'GLAUCOMA'
            elif 'cornea' in cat_text:
                return 'CORNEA'
            elif 'uveitis' in cat_text:
                return 'UVEITIS'
        
        return 'RETINA'  # Default for this script
    
    def _extract_description(self, soup):
        """Extract the main description text"""
        text = soup.get_text()
        
        # Try to find substantial description text
        # Look for text after Contributor/Photographer section
        patterns = [
            # Clinical description patterns
            r'(?:Photographer[s]?:[^\r\n]+[\r\n]\s*)([A-Z][^.]*(?:\.[^.]*){2,})',
            r'(?:Contributor:[^\r\n]+[\r\n]\s*)([A-Z][^.]*(?:\.[^.]*){2,})',
            # Disease description patterns
            r'([A-Z][a-z]+ is (?:a |an |the )?[^.]*(?:\.[^.]*){1,3})',
            r'(This (?:patient|case|photograph)[^.]*(?:\.[^.]*){1,3})',
            r'(These (?:photographs|images)[^.]*(?:\.[^.]*){1,3})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                desc = match.group(1).strip()
                # Clean up
                desc = re.sub(r'\s+', ' ', desc)
                desc = re.sub(r'Enlarge\s*Download', '', desc)
                desc = re.sub(r'Figure \d+[a-z]?\.?', '', desc)
                desc = desc.strip()
                
                # Stop at footer markers
                for marker in ['Image Permissions', 'Creative Commons', 'University of Iowa', 'Address', 'Related Articles']:
                    if marker in desc:
                        desc = desc.split(marker)[0].strip()
                
                if len(desc) > 50:
                    return desc
        
        return ""
    
    def _extract_contributor(self, soup):
        """Extract contributor name"""
        text = soup.get_text()
        match = re.search(r'Contributor[s]?[:\s]+([^\r\n]+?)(?=[\r\n]|Photographer|Posted|Category)', text, re.I)
        if match:
            contrib = match.group(1).strip()
            # Clean up
            contrib = re.sub(r'\s+', ' ', contrib)
            return contrib
        return ""
    
    def _extract_photographer(self, soup):
        """Extract photographer name"""
        text = soup.get_text()
        match = re.search(r'Photographer[s]?[:\s]+([^\r\n]+?)(?=[\r\n]|Posted|Category|[A-Z][a-z]+ is)', text, re.I)
        if match:
            photo = match.group(1).strip()
            photo = re.sub(r'\s+', ' ', photo)
            return photo
        return ""
    
    def _extract_images(self, soup, page_url):
        """Extract medical images from the page"""
        images = []
        skip_patterns = [
            'cc.png', 'lowerLogo', 'DomeGold', 'eyerounds-logo', 
            'facebook', 'twitter', 'instagram', 'Eyerounds-500w',
            '/i/current/', 'logo', 'Logo', 'social', 'icon'
        ]
        
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src')
            if not src:
                continue
            
            # Skip non-medical images
            if any(skip in src.lower() for skip in skip_patterns):
                continue
            
            # Resolve relative URLs
            if src.startswith('http'):
                full_url = src
            elif src.startswith('/'):
                full_url = urljoin(self.base_url, src)
            else:
                full_url = urljoin(page_url, src)
            
            # Get alt text
            alt = img.get('alt', '')
            
            images.append({
                'url': full_url,
                'alt': alt
            })
        
        return images
    
    def scrape_all_conditions(self):
        """Scrape all configured RETINA conditions"""
        all_data = []
        
        for condition in RETINA_CONDITIONS:
            print(f"\nProcessing: {condition['name']}")
            
            for url in condition['urls']:
                data = self.scrape_page(url, condition['name'])
                if data:
                    all_data.append(data)
                    print(f"    Found {len(data['images'])} images")
                
                # Be nice to the server
                time.sleep(0.5)
        
        return all_data
    
    def generate_flashcards(self, scraped_data):
        """Convert scraped data to flashcard format"""
        flashcards = []
        
        for idx, data in enumerate(scraped_data):
            # Build answer text
            answer_parts = []
            
            # Title as header
            answer_parts.append(data['title'])
            answer_parts.append("")
            
            # Description
            if data['description']:
                answer_parts.append(data['description'])
                answer_parts.append("")
            
            # Attribution
            if data['contributor']:
                answer_parts.append(f"Contributor: {data['contributor']}")
            if data['photographer']:
                answer_parts.append(f"Photographer: {data['photographer']}")
            
            # Source
            answer_parts.append(f"\nSource: {data['url']}")
            
            flashcard = {
                'id': f"{data['condition'].lower().replace(' ', '_').replace('(', '').replace(')', '')}_{idx}",
                'title': data['title'],
                'condition': data['condition'],
                'entry_index': idx,
                'images': [img['url'] for img in data['images']],
                'image_alts': [img['alt'] for img in data['images']],
                'answer': '\n'.join(answer_parts),
                'contributor': data['contributor'],
                'photographer': data['photographer'],
                'url': data['url'],
                'category': data['category']
            }
            
            flashcards.append(flashcard)
        
        return flashcards
    
    def save_flashcards(self, flashcards, filepath='data/flashcards.json'):
        """Save flashcards to JSON file"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(flashcards, f, indent=2, ensure_ascii=False)
        
        print(f"\nSaved {len(flashcards)} flashcards to {filepath}")


def main():
    print("=" * 60)
    print("EyeRounds RETINA Conditions Scraper")
    print("=" * 60)
    
    scraper = RetinaScraper()
    
    # Scrape all conditions
    print("\nScraping conditions...")
    scraped_data = scraper.scrape_all_conditions()
    
    if not scraped_data:
        print("\nNo data scraped!")
        return
    
    # Generate flashcards
    print("\nGenerating flashcards...")
    flashcards = scraper.generate_flashcards(scraped_data)
    
    # Save
    scraper.save_flashcards(flashcards)
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    for fc in flashcards:
        print(f"  - {fc['title']}: {len(fc['images'])} images")
    
    print(f"\nDone! Run 'streamlit run app.py' to view flashcards")


if __name__ == "__main__":
    main()
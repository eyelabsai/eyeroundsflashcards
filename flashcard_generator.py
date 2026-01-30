"""
Generate flashcard data structure from scraped EyeRounds data
"""
import json
import os
from pathlib import Path


class FlashcardGenerator:
    def __init__(self, data_dir='data'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.flashcards_file = self.data_dir / 'flashcards.json'
    
    def create_flashcards_from_scraped_data(self, scraped_data_file, downloaded_images_data=None):
        """Create flashcards from scraped data"""
        with open(scraped_data_file, 'r') as f:
            data = json.load(f)
        
        flashcards = []
        
        for entry_index, entry in enumerate(data.get('entries', [])):
            # Get downloaded image paths if available
            entry_images = []
            if downloaded_images_data and entry_index < len(downloaded_images_data):
                entry_images = downloaded_images_data[entry_index]
            else:
                # Use original URLs if local paths not available
                entry_images = [{'local_path': img['url'], 'original_url': img['url']} 
                               for img in entry.get('images', [])]
            
            if not entry_images:
                continue
            
            # Create answer text
            answer_parts = []
            
            if entry.get('photographers'):
                answer_parts.append(f"Photographers: {entry['photographers']}")
            elif entry.get('contributor'):
                # If no photographers, include contributor
                answer_parts.append(f"Contributor: {entry['contributor']}")
            
            if entry.get('description'):
                # Clean up description - remove HTML artifacts and extra whitespace
                import re
                desc = entry['description']
                
                # Remove footer/navigation text patterns
                desc = re.sub(r'Reference:.*?Image Permissions:.*', '', desc, flags=re.DOTALL)
                desc = re.sub(r'Image Permissions:.*', '', desc, flags=re.DOTALL)
                desc = re.sub(r'Related Articles.*', '', desc, flags=re.DOTALL)
                desc = re.sub(r'Address.*?Iowa City.*', '', desc, flags=re.DOTALL)
                desc = re.sub(r'Support Us.*', '', desc, flags=re.DOTALL)
                desc = re.sub(r'Legal.*', '', desc, flags=re.DOTALL)
                desc = re.sub(r'Copyright.*', '', desc, flags=re.DOTALL)
                desc = re.sub(r'Related Links.*', '', desc, flags=re.DOTALL)
                desc = re.sub(r'EyeRounds Social Media.*', '', desc, flags=re.DOTALL)
                desc = re.sub(r'Follow.*', '', desc, flags=re.DOTALL)
                
                # Remove figure labels and captions that are just image metadata
                desc = re.sub(r'Figure \d+[a-z]?:\s*[A-Z][^.]*', '', desc)
                desc = re.sub(r'Figure \d+[a-z]?\s*', '', desc)
                
                # Remove common HTML artifacts
                desc = desc.replace('Enlarge', '').replace('Download', '')
                
                # Remove multiple newlines and whitespace
                desc = re.sub(r'\n{3,}', '\n\n', desc)
                desc = re.sub(r'\s+', ' ', desc)  # Replace all whitespace with single space
                
                # Remove trailing figure references and stop at obvious footer text
                desc = re.sub(r'\s*Figure \d+[a-z]?[:\s]*[A-Za-z\s]*$', '', desc)
                
                # Stop at common footer markers
                for marker in ['University of Iowa', 'Carver College', '200 Hawkins', 'Report an issue']:
                    if marker in desc:
                        desc = desc.split(marker)[0]
                
                desc = desc.strip()
                
                if desc and len(desc) > 20:  # Only add if meaningful content
                    answer_parts.append(desc)
            
            # Add source URL
            source_url = data.get('url', '')
            if source_url:
                answer_parts.append(f"\n\nSource: {source_url}")
            
            answer = '\n\n'.join(answer_parts).strip()
            
            # Determine category from URL
            url = data.get('url', '')
            category = 'UNCATEGORIZED'
            category_keywords = {
                'RETINA': ['retinoblastoma', 'choroidal-hemangioma', 'acute-macular-neuroretinopathy', 'apmppe', 'retina'],
                'GLAUCOMA': ['glaucoma'],
                'CORNEA': ['cornea'],
                'CATARACT': ['cataract'],
                'UVEITIS': ['uveitis'],
                'OCULOPLASTICS': ['oculoplastics'],
                'NEURO-OP': ['neuro-op', 'neuroop'],
                'TRAUMA': ['trauma'],
                'PATHOLOGY': ['pathology'],
                'VITREOUS': ['vitreous'],
                'IRIS': ['iris'],
                'LENS': ['lens'],
                'EXTERNAL DISEASE': ['external-disease'],
                'CONTACT LENS': ['contact-lens'],
                'GENETICS': ['genetics'],
                'INHERITED DISEASE': ['inherited-disease'],
                'SYSTEMS': ['systems'],
            }
            
            for cat, keywords in category_keywords.items():
                if any(keyword in url.lower() for keyword in keywords):
                    category = cat
                    break
            
            # Create flashcard
            flashcard = {
                'id': f"{data.get('title', 'unknown').replace(' ', '_')}_entry{entry_index}",
                'title': data.get('title', 'Unknown'),
                'entry_index': entry_index,
                'images': [img.get('local_path') or img.get('original_url') for img in entry_images],
                'answer': answer,
                'contributor': entry.get('contributor', ''),
                'url': data.get('url', ''),
                'category': category
            }
            
            flashcards.append(flashcard)
        
        return flashcards
    
    def save_flashcards(self, flashcards):
        """Save flashcards to JSON file"""
        with open(self.flashcards_file, 'w', encoding='utf-8') as f:
            json.dump(flashcards, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(flashcards)} flashcards to {self.flashcards_file}")
    
    def load_flashcards(self):
        """Load flashcards from JSON file"""
        if not self.flashcards_file.exists():
            return []
        
        with open(self.flashcards_file, 'r', encoding='utf-8') as f:
            return json.load(f)


if __name__ == "__main__":
    generator = FlashcardGenerator()
    
    if os.path.exists('test_scrape.json'):
        flashcards = generator.create_flashcards_from_scraped_data('test_scrape.json')
        generator.save_flashcards(flashcards)
        print(f"\nGenerated {len(flashcards)} flashcards")

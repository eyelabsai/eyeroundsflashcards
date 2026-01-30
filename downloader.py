"""
Download images from EyeRounds and organize them
"""
import requests
import os
from urllib.parse import urlparse
import json
from pathlib import Path


class ImageDownloader:
    def __init__(self, output_dir='data/images'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def download_image(self, url, filename=None):
        """Download a single image"""
        try:
            response = self.session.get(url, timeout=10, stream=True)
            response.raise_for_status()
            
            if not filename:
                # Generate filename from URL
                parsed = urlparse(url)
                filename = os.path.basename(parsed.path)
                if not filename or '.' not in filename:
                    filename = f"image_{hash(url) % 10000}.jpg"
            
            filepath = self.output_dir / filename
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return str(filepath)
        except Exception as e:
            print(f"Error downloading {url}: {str(e)}")
            return None
    
    def download_entry_images(self, entry, entry_index=0):
        """Download all images for an entry and return local paths"""
        downloaded = []
        
        for img_index, img_info in enumerate(entry.get('images', [])):
            url = img_info['url']
            figure_label = img_info.get('figure_label', '')
            
            # Create descriptive filename
            if figure_label:
                filename = f"entry{entry_index}_fig{figure_label.replace(' ', '')}.jpg"
            else:
                filename = f"entry{entry_index}_img{img_index}.jpg"
            
            # Clean filename
            filename = "".join(c for c in filename if c.isalnum() or c in "._-")
            
            local_path = self.download_image(url, filename)
            if local_path:
                downloaded.append({
                    'original_url': url,
                    'local_path': local_path,
                    'figure_label': figure_label,
                    'alt': img_info.get('alt', '')
                })
        
        return downloaded


if __name__ == "__main__":
    # Test downloader
    downloader = ImageDownloader()
    
    # Load scraped data
    if os.path.exists('test_scrape.json'):
        with open('test_scrape.json', 'r') as f:
            data = json.load(f)
        
        for i, entry in enumerate(data.get('entries', [])):
            print(f"\nDownloading images for entry {i+1}...")
            downloaded = downloader.download_entry_images(entry, i)
            print(f"Downloaded {len(downloaded)} images")

"""
Scraper for EyeRounds atlas pages to extract images and descriptions
"""
import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin, urlparse
import os


class EyeRoundsScraper:
    def __init__(self, base_url="https://webeye.ophth.uiowa.edu"):
        self.base_url = base_url
        self.eyerounds_base = "https://eyerounds.org"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def scrape_atlas_index(self, index_url="https://eyerounds.org/atlas/index.htm", category=None):
        """
        Scrape the atlas index page to find all atlas entry links
        
        Args:
            index_url: URL of the atlas index page
            category: Optional category filter (e.g., 'RETINA', 'GLAUCOMA')
        
        Returns:
            List of dictionaries with 'title', 'url', and 'category' for each entry
        """
        try:
            response = self.session.get(index_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            atlas_entries = []
            
            # Find all links that point to atlas pages
            # Atlas pages typically have URLs like /atlas/pages/... or /eyeforum/atlas/pages/...
            all_links = soup.find_all('a', href=True)
            
            for link in all_links:
                href = link.get('href', '')
                link_text = link.get_text().strip()
                
                # Check if this is an atlas page link
                if '/atlas/pages/' in href or '/eyeforum/atlas/pages/' in href:
                    # Get full URL
                    if href.startswith('http'):
                        full_url = href
                    elif href.startswith('/'):
                        # Try both base URLs
                        if 'eyeforum' in href:
                            full_url = urljoin(self.base_url, href)
                        else:
                            full_url = urljoin(self.eyerounds_base, href)
                    else:
                        full_url = urljoin(index_url, href)
                    
                    # Get title from link text or nearby elements
                    title = link_text
                    if not title or len(title) < 3:
                        # Try to find title in parent or nearby elements
                        parent = link.find_parent(['div', 'li', 'td'])
                        if parent:
                            # Look for title in alt text of nearby image
                            img = parent.find('img')
                            if img:
                                title = img.get('alt', '') or img.get('title', '')
                            if not title:
                                title = parent.get_text().strip()[:100]
                    
                    # Try to determine category from context
                    entry_category = self._extract_category_from_context(link, category)
                    
                    if title and len(title) > 2:
                        atlas_entries.append({
                            'title': title,
                            'url': full_url,
                            'category': entry_category
                        })
            
            # Remove duplicates
            seen_urls = set()
            unique_entries = []
            for entry in atlas_entries:
                if entry['url'] not in seen_urls:
                    seen_urls.add(entry['url'])
                    unique_entries.append(entry)
            
            # Filter by category if specified
            if category:
                unique_entries = [e for e in unique_entries 
                                if e.get('category', '').upper() == category.upper()]
            
            return unique_entries
            
        except Exception as e:
            print(f"Error scraping atlas index {index_url}: {str(e)}")
            return []
    
    def _extract_category_from_context(self, link_element, default_category=None):
        """Try to determine the category of an atlas entry from its context"""
        if default_category:
            return default_category
        
        # Look for category in parent elements or sidebar
        parent = link_element.find_parent(['div', 'li', 'section'])
        if parent:
            # Check if parent has category class or data attribute
            for attr in ['class', 'data-category', 'data-topic']:
                attr_val = parent.get(attr, '')
                if isinstance(attr_val, list):
                    attr_val = ' '.join(attr_val)
                if attr_val:
                    # Common categories
                    categories = ['RETINA', 'GLAUCOMA', 'CORNEA', 'CATARACT', 'UVEITIS', 
                                'OCULOPLASTICS', 'NEURO-OP', 'TRAUMA', 'PATHOLOGY']
                    for cat in categories:
                        if cat in str(attr_val).upper():
                            return cat
        
        return default_category or 'UNCATEGORIZED'
    
    def get_categories_from_index(self, index_url="https://eyerounds.org/atlas/index.htm"):
        """Extract available categories from the atlas index page"""
        try:
            response = self.session.get(index_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            categories = []
            
            # Look for category links in sidebar or filter section
            # Categories are typically in links or list items
            category_elements = soup.find_all(['a', 'li', 'div'], 
                                            string=re.compile(r'(RETINA|GLAUCOMA|CORNEA|CATARACT|UVEITIS|OCULOPLASTICS|NEURO-OP|TRAUMA|PATHOLOGY|VITREOUS|IRIS|LENS)', re.I))
            
            for elem in category_elements:
                text = elem.get_text().strip().upper()
                # Extract category name
                for cat in ['RETINA', 'GLAUCOMA', 'CORNEA', 'CATARACT', 'UVEITIS', 
                           'OCULOPLASTICS', 'NEURO-OP', 'TRAUMA', 'PATHOLOGY', 
                           'VITREOUS', 'IRIS', 'LENS', 'EXTERNAL DISEASE', 
                           'CONTACT LENS', 'GENETICS', 'INHERITED DISEASE', 'SYSTEMS']:
                    if cat in text and cat not in categories:
                        categories.append(cat)
            
            return sorted(categories) if categories else ['ALL']
            
        except Exception as e:
            print(f"Error extracting categories: {str(e)}")
            return ['ALL']
    
    def scrape_atlas_page(self, url):
        """
        Scrape an EyeRounds atlas page and extract:
        - Images with their URLs
        - Associated text descriptions
        - Entry information (contributor, photographer, etc.)
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            # Store page URL for resolving relative image URLs
            self.current_page_url = url
            
            # Extract the actual condition title from the page
            condition_title = self._extract_condition_title(soup, url)
            
            # Extract category from the page
            page_category = self._extract_page_category(soup)
            
            # Find all entry sections
            entries = []
            
            # Find main entry sections (h4 with "Entry" in text or divs with entry content)
            entry_sections = soup.find_all(['div', 'section'], class_=re.compile('entry|Entry', re.I))
            
            # If no specific entry sections, look for h4 headings with "Entry" or numbered sections
            if not entry_sections:
                # Look for h4 or h5 tags that might indicate entries
                headings = soup.find_all(['h4', 'h5'])
                for heading in headings:
                    if 'Entry' in heading.get_text() or heading.get_text().strip().startswith('Entry'):
                        # Get the next sibling content
                        entry_content = self._extract_entry_content(heading)
                        if entry_content:
                            entries.append(entry_content)
            
            # Also try to find entries by looking for contributor patterns
            # Look for text patterns like "Contributor:" followed by content
            contributor_sections = soup.find_all(string=re.compile(r'Contributor:', re.I))
            
            for contrib_text in contributor_sections:
                parent = contrib_text.find_parent()
                if parent:
                    entry = self._extract_entry_from_section(parent)
                    if entry and entry not in entries:
                        entries.append(entry)
            
            # If still no entries, try improved extraction method
            if not entries:
                entries = self._extract_entries_improved(soup)
            
            # If still no entries, try single-page format (no Entry headings)
            if not entries:
                entries = self._extract_single_page_format(soup)
            
            # If still no entries, try fallback
            if not entries:
                entries = self._extract_all_entries_fallback(soup)
            
            # Extract main page info - use condition title extracted earlier
            return {
                'title': condition_title,
                'url': url,
                'category': page_category,
                'entries': entries
            }
            
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return None
    
    def _extract_entry_content(self, heading):
        """Extract content from an entry starting at a heading"""
        entry = {
            'contributor': '',
            'photographers': '',
            'description': '',
            'images': []
        }
        
        # Get contributor info
        current = heading
        while current:
            text = current.get_text()
            if 'Contributor:' in text:
                entry['contributor'] = text.split('Contributor:')[-1].strip()
            if 'Photographer' in text:
                entry['photographers'] = text.split('Photographer')[-1].strip().lstrip('s:').strip()
            
            # Find images in this section
            images = current.find_all_next('img', limit=10)
            base_for_url = getattr(self, 'current_page_url', self.base_url)
            for img in images:
                img_url = img.get('src') or img.get('data-src')
                if img_url:
                    if img_url.startswith('http'):
                        full_url = img_url
                    elif img_url.startswith('/'):
                        full_url = urljoin(self.base_url, img_url)
                    else:
                        full_url = urljoin(base_for_url, img_url)
                    alt_text = img.get('alt', '')
                    # Find associated figure label
                    figure_label = self._find_figure_label(img)
                    entry['images'].append({
                        'url': full_url,
                        'alt': alt_text,
                        'figure_label': figure_label
                    })
            
            # Find description text
            # Look for paragraph after the heading
            next_p = current.find_next('p')
            if next_p and next_p.get_text().strip():
                entry['description'] = next_p.get_text().strip()
                break
            
            current = current.find_next_sibling()
            if current and current.name in ['h4', 'h5', 'h3']:
                break
        
        return entry if entry['images'] or entry['description'] else None
    
    def _extract_entry_from_section(self, section):
        """Extract entry data from a section element"""
        entry = {
            'contributor': '',
            'photographers': '',
            'description': '',
            'images': []
        }
        
        text = section.get_text()
        
        # Extract contributor
        contrib_match = re.search(r'Contributor:\s*([^\n]+)', text, re.I)
        if contrib_match:
            entry['contributor'] = contrib_match.group(1).strip()
        
        # Extract photographers
        photo_match = re.search(r'Photographer[s]?:\s*([^\n]+)', text, re.I)
        if photo_match:
            entry['photographers'] = photo_match.group(1).strip()
        
        # Find all images in this section
        images = section.find_all('img')
        for img in images:
            img_url = img.get('src') or img.get('data-src')
            if img_url:
                # Resolve relative URLs using the page URL
                base_for_url = getattr(self, 'current_page_url', self.base_url)
                if img_url.startswith('http'):
                    full_url = img_url
                elif img_url.startswith('/'):
                    # Absolute path from domain root
                    full_url = urljoin(self.base_url, img_url)
                else:
                    # Relative to current page
                    full_url = urljoin(base_for_url, img_url)
                alt_text = img.get('alt', '')
                figure_label = self._find_figure_label(img)
                entry['images'].append({
                    'url': full_url,
                    'alt': alt_text,
                    'figure_label': figure_label
                })
        
        # Extract description - look for paragraph text
        paragraphs = section.find_all('p')
        descriptions = []
        for p in paragraphs:
            p_text = p.get_text().strip()
            # Skip very short paragraphs (likely navigation)
            if len(p_text) > 50:
                descriptions.append(p_text)
        
        if descriptions:
            entry['description'] = ' '.join(descriptions)
        
        return entry if entry['images'] or entry['description'] else None
    
    def _extract_entries_improved(self, soup):
        """Improved method to extract entries by finding Entry headings and their content"""
        entries = []
        full_page_text = soup.get_text()
        
        # Find all h4 and h5 headings that might indicate entries
        headings = soup.find_all(['h4', 'h5', 'h3'])
        entry_headings = []
        
        for heading in headings:
            heading_text = heading.get_text().strip()
            if 'Entry' in heading_text:
                entry_headings.append(heading)
        
        # If we found entry headings, extract content for each
        if entry_headings:
            for i, heading in enumerate(entry_headings):
                entry = {
                    'contributor': '',
                    'photographers': '',
                    'description': '',
                    'images': []
                }
                
                # Get the section between this heading and the next
                next_heading = entry_headings[i + 1] if i + 1 < len(entry_headings) else None
                
                # Collect all elements between headings
                current = heading
                section_text = ""
                section_elements = []
                
                while current:
                    current = current.next_sibling
                    if current is None:
                        break
                    if current == next_heading:
                        break
                    if hasattr(current, 'name') and current.name in ['h1', 'h2', 'h3', 'h4', 'h5']:
                        if current != next_heading:
                            continue
                        break
                    
                    if hasattr(current, 'get_text'):
                        text = current.get_text()
                        section_text += " " + text
                        section_elements.append(current)
                
                # Extract metadata from section text
                contrib_match = re.search(r'Contributor:\s*([^\n]+?)(?:\n|Photographer|$)', section_text, re.I | re.DOTALL)
                if contrib_match:
                    entry['contributor'] = contrib_match.group(1).strip()
                
                photo_match = re.search(r'Photographer[s]?:\s*([^\n]+?)(?:\n|These|Figure|$)', section_text, re.I | re.DOTALL)
                if photo_match:
                    entry['photographers'] = photo_match.group(1).strip()
                
                # Extract description - try multiple patterns
                desc_patterns = [
                    r'(These photographs show[^.]*(?:\.[^.]*){1,})',  # At least 1 sentence
                    r'(These images show[^.]*(?:\.[^.]*){1,})',
                    r'(This patient [^.]*(?:\.[^.]*){1,})',  # Entry 3 pattern
                    r'(This [^.]*(?:\.[^.]*){1,})',
                ]
                
                for pattern in desc_patterns:
                    desc_match = re.search(pattern, section_text, re.I | re.DOTALL)
                    if desc_match:
                        desc_text = desc_match.group(1).strip()
                        # Clean up - remove figure references and HTML artifacts
                        desc_text = re.sub(r'\s*Figure \d+[a-z]?[:\s]*[^.]*\.', '', desc_text)
                        desc_text = re.sub(r'\s*\(Figures? \d+[a-z]?[^)]*\)', '', desc_text)
                        desc_text = re.sub(r'\s+', ' ', desc_text).strip()
                        if len(desc_text) > 30:  # Only use if substantial
                            entry['description'] = desc_text
                            break
                
                # If no pattern matched, try to get first substantial paragraph after contributor
                if not entry['description']:
                    # Look for text that comes after "Contributor:" but before images
                    after_contrib = re.search(r'Contributor:[^\n]+\n\s*([A-Z][^.]*(?:\.[^.]*){0,2})', section_text, re.DOTALL)
                    if after_contrib:
                        potential_desc = after_contrib.group(1).strip()
                        # Remove figure references
                        potential_desc = re.sub(r'\s*\(Figures? \d+[a-z]?[^)]*\)', '', potential_desc)
                        potential_desc = re.sub(r'\s+', ' ', potential_desc).strip()
                        if len(potential_desc) > 30 and 'Figure' not in potential_desc[:50]:
                            entry['description'] = potential_desc
                
                # Find images in this section
                base_for_url = getattr(self, 'current_page_url', self.base_url)
                for elem in section_elements:
                    if hasattr(elem, 'find_all'):
                        imgs = elem.find_all('img')
                        for img in imgs:
                            img_url = img.get('src') or img.get('data-src')
                            if img_url and not any(skip in img_url for skip in ['DomeGold', 'Eyerounds', 'cc.png', 'related_case']):
                                if img_url.startswith('http'):
                                    full_url = img_url
                                elif img_url.startswith('/'):
                                    full_url = urljoin(self.base_url, img_url)
                                else:
                                    full_url = urljoin(base_for_url, img_url)
                                alt_text = img.get('alt', '')
                                figure_label = self._find_figure_label(img)
                                entry['images'].append({
                                    'url': full_url,
                                    'alt': alt_text,
                                    'figure_label': figure_label
                                })
                
                if entry['images'] or entry['description']:
                    entries.append(entry)
        
        # If no entry headings found, try to extract from full page text by grouping images
        if not entries:
            # Find all images and group them by proximity to text patterns
            all_images = soup.find_all('img')
            medical_images = [img for img in all_images 
                            if img.get('src') and not any(skip in img.get('src', '') 
                            for skip in ['DomeGold', 'Eyerounds', 'cc.png', 'related_case'])]
            
            if medical_images:
                # Try to extract entries by finding text near images
                # Look for patterns like "Entry 1", "Entry 2", etc. in the text
                entry_matches = list(re.finditer(r'Entry\s+(\d+)', full_page_text, re.I))
                
                if entry_matches:
                    for i, match in enumerate(entry_matches):
                        entry = {
                            'contributor': '',
                            'photographers': '',
                            'description': '',
                            'images': []
                        }
                        
                        # Get text around this entry
                        start_pos = match.start()
                        end_pos = entry_matches[i + 1].start() if i + 1 < len(entry_matches) else len(full_page_text)
                        entry_text = full_page_text[start_pos:end_pos]
                        
                        # Extract metadata
                        contrib_match = re.search(r'Contributor:\s*([^\n]+)', entry_text, re.I)
                        if contrib_match:
                            entry['contributor'] = contrib_match.group(1).strip()
                        
                        photo_match = re.search(r'Photographer[s]?:\s*([^\n]+)', entry_text, re.I)
                        if photo_match:
                            entry['photographers'] = photo_match.group(1).strip()
                        
                        # Try multiple description patterns
                        desc_patterns = [
                            r'(These photographs show[^.]*(?:\.[^.]*){1,})',
                            r'(This patient [^.]*(?:\.[^.]*){1,})',
                            r'(This [^.]*(?:\.[^.]*){1,})',
                        ]
                        
                        desc_found = False
                        for pattern in desc_patterns:
                            desc_match = re.search(pattern, entry_text, re.I | re.DOTALL)
                            if desc_match:
                                desc_text = desc_match.group(1).strip()
                                # Clean up figure references
                                desc_text = re.sub(r'\s*\(Figures? \d+[a-z]?[^)]*\)', '', desc_text)
                                desc_text = re.sub(r'\s+', ' ', desc_text).strip()
                                if len(desc_text) > 30:
                                    entry['description'] = desc_text
                                    desc_found = True
                                    break
                        
                        # Fallback: get text right after contributor
                        if not desc_found:
                            after_contrib = re.search(r'Contributor:[^\n]+\n\s*([A-Z][^F][^.]*(?:\.[^.]*){0,2})', entry_text, re.DOTALL)
                            if after_contrib:
                                potential_desc = after_contrib.group(1).strip()
                                # Remove figure references and HTML artifacts
                                potential_desc = re.sub(r'\s*\(Figures? \d+[a-z]?[^)]*\)', '', potential_desc)
                                potential_desc = re.sub(r'\s*Figure \d+[a-z]?[:\s]*[^.]*\.', '', potential_desc)
                                potential_desc = re.sub(r'\s+', ' ', potential_desc).strip()
                                if len(potential_desc) > 30 and 'Enlarge' not in potential_desc and 'Download' not in potential_desc:
                                    entry['description'] = potential_desc
                        
                        # Find images that might belong to this entry
                        entry_num = match.group(1)
                        for img in medical_images:
                            img_url = img.get('src') or img.get('data-src')
                            if img_url:
                                # Check if figure label matches entry number
                                figure_label = self._find_figure_label(img)
                                if entry_num in figure_label or not entries:  # First entry gets unmatched images
                                    base_for_url = getattr(self, 'current_page_url', self.base_url)
                                    if img_url.startswith('http'):
                                        full_url = img_url
                                    elif img_url.startswith('/'):
                                        full_url = urljoin(self.base_url, img_url)
                                    else:
                                        full_url = urljoin(base_for_url, img_url)
                                    entry['images'].append({
                                        'url': full_url,
                                        'alt': img.get('alt', ''),
                                        'figure_label': figure_label
                                    })
                        
                        if entry['images'] or entry['description']:
                            entries.append(entry)
        
        return entries
    
    def _extract_single_page_format(self, soup):
        """Extract content from pages that don't use Entry headings (single page format)"""
        entries = []
        full_page_text = soup.get_text()
        
        # Look for contributor pattern without Entry heading
        contrib_matches = list(re.finditer(r'Contributor:\s*([^\n]+)', full_page_text, re.I))
        
        if contrib_matches:
            # This might be a single-entry page
            entry = {
                'contributor': '',
                'photographers': '',
                'description': '',
                'images': []
            }
            
            # Get contributor
            if contrib_matches:
                entry['contributor'] = contrib_matches[0].group(1).strip()
            
            # Get photographers
            photo_match = re.search(r'Photographer[s]?:\s*([^\n]+)', full_page_text, re.I)
            if photo_match:
                entry['photographers'] = photo_match.group(1).strip()
            
            # Get description - look for substantial paragraphs after category/contributor
            # Try to find text that describes the condition
            desc_patterns = [
                r'(Leukocoria is[^.]*(?:\.[^.]*){2,})',  # Retinoblastoma pattern
                r'([A-Z][a-z]+ is the[^.]*(?:\.[^.]*){2,})',  # General pattern
                r'([A-Z][a-z]+ is[^.]*(?:\.[^.]*){2,})',
            ]
            
            for pattern in desc_patterns:
                desc_match = re.search(pattern, full_page_text, re.I | re.DOTALL)
                if desc_match:
                    desc_text = desc_match.group(1).strip()
                    # Clean up
                    desc_text = re.sub(r'\s+', ' ', desc_text).strip()
                    if len(desc_text) > 50:
                        entry['description'] = desc_text
                        break
            
            # If no pattern matched, try to get first substantial paragraph after category
            if not entry['description']:
                # Look for text after "Category" or "Contributor"
                after_cat = re.search(r'Category[^:]*:\s*[^\n]+\n\s*([A-Z][^.]*(?:\.[^.]*){1,})', full_page_text, re.DOTALL)
                if after_cat:
                    potential_desc = after_cat.group(1).strip()
                    potential_desc = re.sub(r'\s+', ' ', potential_desc).strip()
                    if len(potential_desc) > 50:
                        entry['description'] = potential_desc
                else:
                    # Try after contributor
                    after_contrib = re.search(r'Contributor:[^\n]+\n\s*([A-Z][^F][^.]*(?:\.[^.]*){1,})', full_page_text, re.DOTALL)
                    if after_contrib:
                        potential_desc = after_contrib.group(1).strip()
                        potential_desc = re.sub(r'\s+', ' ', potential_desc).strip()
                        if len(potential_desc) > 50 and 'Leukocoria' in potential_desc or 'retinoblastoma' in potential_desc.lower():
                            entry['description'] = potential_desc
            
            # Find all medical images
            base_for_url = getattr(self, 'current_page_url', self.base_url)
            all_images = soup.find_all('img')
            for img in all_images:
                img_url = img.get('src') or img.get('data-src')
                if img_url and not any(skip in img_url for skip in ['DomeGold', 'Eyerounds', 'cc.png', 'related_case', 'lowerLogo']):
                    if img_url.startswith('http'):
                        full_url = img_url
                    elif img_url.startswith('/'):
                        full_url = urljoin(self.base_url, img_url)
                    else:
                        full_url = urljoin(base_for_url, img_url)
                    alt_text = img.get('alt', '')
                    figure_label = self._find_figure_label(img)
                    entry['images'].append({
                        'url': full_url,
                        'alt': alt_text,
                        'figure_label': figure_label
                    })
            
            if entry['images'] or entry['description']:
                entries.append(entry)
        
        return entries
    
    def _extract_all_entries_fallback(self, soup):
        """Fallback method to extract entries when structure is unclear"""
        entries = []
        
        # Find all strong/bold text that might be labels
        # Look for patterns like "Contributor:", "Photographer:", etc.
        all_text = soup.get_text()
        
        # Split by common entry markers
        entry_markers = re.split(r'(Contributor:|Photographer[s]?:)', all_text)
        
        # Find all images with their context
        images = soup.find_all('img')
        base_for_url = getattr(self, 'current_page_url', self.base_url)
        
        for img in images:
                img_url = img.get('src') or img.get('data-src')
                if not img_url:
                    continue
                
                # Skip navigation/logo images
                if any(skip in img_url for skip in ['DomeGold', 'Eyerounds', 'cc.png', 'related_case']):
                    continue
                
                if img_url.startswith('http'):
                    full_url = img_url
                elif img_url.startswith('/'):
                    full_url = urljoin(self.base_url, img_url)
                else:
                    full_url = urljoin(base_for_url, img_url)
                
                    # Find the parent container
                    parent = img.find_parent(['div', 'section', 'article', 'figure'])
                    if not parent:
                        parent = img.find_parent()
                    
                    # Extract text from parent
                    parent_text = parent.get_text() if parent else ''
                    
                    # Try to find contributor and photographer info
                    contributor = ''
                    photographers = ''
                    description = ''
                    
                    contrib_match = re.search(r'Contributor:\s*([^\n]+)', parent_text, re.I)
                    if contrib_match:
                        contributor = contrib_match.group(1).strip()
                    
                    photo_match = re.search(r'Photographer[s]?:\s*([^\n]+)', parent_text, re.I)
                    if photo_match:
                        photographers = photo_match.group(1).strip()
                    
                    # Find description - look for longer paragraphs
                    desc_match = re.search(r'(These photographs show[^.]*(?:\.[^.]*){2,})', parent_text, re.I | re.DOTALL)
                    if desc_match:
                        description = desc_match.group(1).strip()
                    else:
                        # Get first substantial paragraph
                        paragraphs = parent.find_all('p') if parent else []
                        for p in paragraphs:
                            p_text = p.get_text().strip()
                            if len(p_text) > 100:
                                description = p_text
                                break
                    
                    figure_label = self._find_figure_label(img)
                    
                    # Check if we already have an entry for this contributor/photographer combo
                    existing_entry = None
                    for e in entries:
                        if e.get('contributor') == contributor and e.get('photographers') == photographers:
                            existing_entry = e
                            break
                    
                    if existing_entry:
                        existing_entry['images'].append({
                            'url': full_url,
                            'alt': img.get('alt', ''),
                            'figure_label': figure_label
                        })
                    else:
                        entries.append({
                            'contributor': contributor,
                            'photographers': photographers,
                            'description': description,
                            'images': [{
                                'url': full_url,
                                'alt': img.get('alt', ''),
                                'figure_label': figure_label
                            }]
                        })
        
        return entries
    
    def _extract_condition_title(self, soup, url):
        """Extract the actual condition/disease title from the page"""
        # Try h1 first - this usually has the condition name
        h1 = soup.find('h1')
        if h1:
            title = h1.get_text().strip()
            # Clean up common prefixes/suffixes
            title = re.sub(r'^EyeRounds\.org\s*[-–]\s*', '', title)
            title = re.sub(r'\s*[-–]\s*EyeRounds\.org$', '', title)
            if title and len(title) > 3 and title.lower() not in ['ophthalmology and visual sciences', 'eyerounds.org', 'atlas']:
                return title
        
        # Try h2 as backup
        h2 = soup.find('h2')
        if h2:
            title = h2.get_text().strip()
            if title and len(title) > 3 and 'ophthalmology' not in title.lower():
                return title
        
        # Try to extract from URL as last resort
        url_parts = url.rstrip('/').split('/')
        for part in reversed(url_parts):
            if part and part not in ['index.htm', 'index.html', 'pages', 'atlas']:
                # Convert slug to title case
                title = part.replace('-', ' ').replace('_', ' ').title()
                return title
        
        return "Unknown Condition"
    
    def _extract_page_category(self, soup):
        """Extract the category from the page content"""
        full_text = soup.get_text()
        
        # Look for "Category(ies):" pattern in the page
        cat_match = re.search(r'Category\(?ies?\)?[:\s]+([^\\n]+?)(?=Contributor|Photographer|Posted|$)', full_text, re.I)
        if cat_match:
            cat_text = cat_match.group(1).strip()
            # Map to standard categories
            cat_lower = cat_text.lower()
            if 'retina' in cat_lower or 'vitreous' in cat_lower:
                return 'RETINA'
            elif 'glaucoma' in cat_lower:
                return 'GLAUCOMA'
            elif 'cornea' in cat_lower:
                return 'CORNEA'
            elif 'cataract' in cat_lower:
                return 'CATARACT'
            elif 'uveitis' in cat_lower:
                return 'UVEITIS'
            elif 'oculoplastics' in cat_lower or 'orbit' in cat_lower:
                return 'OCULOPLASTICS'
            elif 'neuro' in cat_lower:
                return 'NEURO-OP'
            elif 'trauma' in cat_lower:
                return 'TRAUMA'
            elif 'pathology' in cat_lower:
                return 'PATHOLOGY'
            elif 'iris' in cat_lower:
                return 'IRIS'
            elif 'lens' in cat_lower:
                return 'LENS'
            elif 'external' in cat_lower:
                return 'EXTERNAL DISEASE'
            elif 'contact' in cat_lower:
                return 'CONTACT LENS'
            elif 'genetics' in cat_lower:
                return 'GENETICS'
            elif 'inherited' in cat_lower:
                return 'INHERITED DISEASE'
            elif 'system' in cat_lower:
                return 'SYSTEMS'
        
        return 'UNCATEGORIZED'
    
    def _find_figure_label(self, img_element):
        """Find the figure label associated with an image"""
        # Look for nearby text that might be a figure label
        parent = img_element.find_parent()
        if parent:
            # Look for "Figure" text nearby
            text = parent.get_text()
            figure_match = re.search(r'Figure\s+(\d+[a-z]?)', text, re.I)
            if figure_match:
                return figure_match.group(0)
            
            # Look for preceding or following siblings
            prev_sibling = img_element.find_previous_sibling(string=re.compile(r'Figure', re.I))
            if prev_sibling:
                match = re.search(r'Figure\s+(\d+[a-z]?)', prev_sibling, re.I)
                if match:
                    return match.group(0)
        
        return ''
    
    def save_scraped_data(self, data, filename='scraped_data.json'):
        """Save scraped data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Saved scraped data to {filename}")


if __name__ == "__main__":
    scraper = EyeRoundsScraper()
    
    # Test: Scrape atlas index to find entries
    print("=" * 60)
    print("Testing Atlas Index Scraper")
    print("=" * 60)
    
    index_url = "https://eyerounds.org/atlas/index.htm"
    print(f"\nScraping atlas index: {index_url}")
    entries = scraper.scrape_atlas_index(index_url)
    
    print(f"\nFound {len(entries)} atlas entries")
    if entries:
        print("\nFirst 10 entries:")
        for i, entry in enumerate(entries[:10], 1):
            print(f"{i}. {entry['title'][:60]}...")
            print(f"   URL: {entry['url']}")
            print(f"   Category: {entry.get('category', 'N/A')}")
    
    # Test: Get categories
    print("\n" + "=" * 60)
    print("Available Categories:")
    print("=" * 60)
    categories = scraper.get_categories_from_index(index_url)
    for cat in categories:
        print(f"  - {cat}")
    
    # Test: Scrape a specific page
    print("\n" + "=" * 60)
    print("Testing Individual Page Scraper")
    print("=" * 60)
    
    test_url = "https://webeye.ophth.uiowa.edu/eyeforum/atlas/pages/choroidal-hemangioma-circumscribed/index.htm"
    print(f"\nScraping {test_url}...")
    data = scraper.scrape_atlas_page(test_url)
    
    if data:
        scraper.save_scraped_data(data, 'test_scrape.json')
        print(f"\nFound {len(data.get('entries', []))} entries")
        for i, entry in enumerate(data.get('entries', []), 1):
            print(f"\nEntry {i}:")
            print(f"  Contributor: {entry.get('contributor', 'N/A')}")
            print(f"  Photographers: {entry.get('photographers', 'N/A')}")
            print(f"  Images: {len(entry.get('images', []))}")
            print(f"  Description length: {len(entry.get('description', ''))} chars")
    else:
        print("Failed to scrape page")

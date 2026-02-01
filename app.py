"""
Streamlit flashcard app for EyeRounds ophthalmology study
Modern, clean UI with image-first flashcard format.
After reveal, GPT-4o can provide oral-boards-style treatment & next steps.
"""
import os
import streamlit as st
import json
from pathlib import Path
import random

# Load .env for OpenAI API key
from dotenv import load_dotenv
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Page config - must be first Streamlit command
st.set_page_config(
    page_title="EyeRounds Flashcards",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    /* Main container - tight top/bottom to reduce wasted space */
    .main .block-container {
        padding-top: 0.5rem;
        padding-bottom: 1rem;
        max-width: 1200px;
    }
    
    /* Streamlit default top padding - reduce */
    section.main [data-testid="block-container"] {
        padding-top: 0.5rem;
    }
    
    /* Header - compact */
    .main-header {
        text-align: center;
        padding: 0.35rem 0;
        border-bottom: 1px solid #e0e0e0;
        margin-bottom: 0.75rem;
    }
    
    .main-header h1 {
        color: #1a73e8;
        margin-bottom: 0.15rem;
        font-size: 1.4rem;
    }
    
    .main-header p {
        margin: 0;
        font-size: 0.9rem;
        color: #666;
    }
    
    /* Tighter spacing for main content */
    .main .element-container { margin-bottom: 0.5rem; }
    .main h3 { margin-top: 0.5rem; margin-bottom: 0.35rem; }
    .main h4 { margin-top: 0.4rem; margin-bottom: 0.25rem; }
    .main hr { margin: 0.5rem 0; }
    
    /* Card container */
    .flashcard-container {
        background: white;
        border-radius: 12px;
        padding: 2rem;
        box-shadow: 0 2px 12px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    /* Image container */
    .image-container {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    /* Answer box */
    .answer-box {
        background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
        border-radius: 8px;
        padding: 1.5rem;
        margin-top: 1rem;
        border-left: 4px solid #4caf50;
    }
    
    .answer-box h4 {
        color: #2e7d32;
        margin-bottom: 1rem;
    }
    
    /* Category badge */
    .category-badge {
        display: inline-block;
        background: #1a73e8;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
    }
    
    /* Sidebar styling - less top padding */
    [data-testid="stSidebar"] .block-container {
        padding-top: 0.75rem;
    }
    
    /* Navigation buttons */
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Card title */
    .card-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #333;
        margin-bottom: 0.5rem;
    }
    
    /* Progress indicator */
    .progress-text {
        text-align: center;
        color: #666;
        font-size: 0.9rem;
        margin-bottom: 1rem;
    }
    
    /* Source link */
    .source-link {
        font-size: 0.85rem;
        color: #666;
    }
    
    .source-link a {
        color: #1a73e8;
    }
    
    /* Treatment box - oral boards */
    .treatment-box {
        background: linear-gradient(135deg, #f0f7ff 0%, #e8f4f8 100%);
        border: 1px solid #b3d9e6;
        border-left: 4px solid #1565c0;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        padding: 1.25rem 1.5rem;
        margin: 0.5rem 0 1rem 0;
        line-height: 1.65;
    }
    .treatment-box .treatment-title {
        font-size: 1rem;
        font-weight: 600;
        color: #1565c0;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .treatment-box p {
        margin-bottom: 0.75rem;
        color: #333;
    }
    .treatment-box p:last-child { margin-bottom: 0; }
    .treatment-box ul, .treatment-box ol {
        margin: 0.5rem 0 1rem 1.25rem;
        padding-left: 1.5rem;
    }
    .treatment-box li {
        margin-bottom: 0.4rem;
    }
    .treatment-box strong {
        color: #0d47a1;
    }
    .treatment-box h1, .treatment-box h2, .treatment-box h3, .treatment-box h4 {
        color: #1565c0;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
        font-size: 1rem;
    }
</style>
""", unsafe_allow_html=True)


CATEGORIES = [
    'CATARACT', 'CONTACT LENS', 'CORNEA', 'EXTERNAL DISEASE', 'GENETICS',
    'GLAUCOMA', 'INHERITED DISEASE', 'IRIS', 'LENS', 'NEURO-OP', 
    'PATHOLOGY', 'OCULOPLASTICS', 'RETINA', 'SYSTEMS', 'TRAUMA', 
    'UVEITIS', 'VITREOUS'
]


@st.cache_data
def load_flashcards():
    """Load flashcards from JSON file"""
    # Try new format first
    flashcard_file = Path('data/all_flashcards.json')
    if flashcard_file.exists():
        with open(flashcard_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('flashcards', [])
    
    # Fall back to old format
    old_file = Path('data/flashcards.json')
    if old_file.exists():
        with open(old_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    return []


def get_unique_categories(flashcards):
    """Get sorted list of unique categories"""
    categories = set()
    for card in flashcards:
        cat = card.get('category', 'UNCATEGORIZED')
        categories.add(cat)
    return ['ALL'] + sorted(list(categories))


def filter_flashcards(flashcards, category):
    """Filter flashcards by category"""
    if category == 'ALL':
        return flashcards
    return [c for c in flashcards if c.get('category', 'UNCATEGORIZED') == category]


def filter_by_search(cards, query):
    """Filter cards by keyword search (title, description, keywords). Case-insensitive."""
    if not query or not query.strip():
        return cards
    q = query.strip().lower()
    out = []
    for c in cards:
        title = (c.get("title") or "").lower()
        description = (c.get("description") or c.get("answer") or "").lower()
        keywords = (c.get("keywords") or "").lower()
        if q in title or q in description or q in keywords:
            out.append(c)
    return out


def get_oral_boards_treatment(card):
    """Call GPT-4o with ABO oral boards structure: Data Acquisition, Diagnosis, Management."""
    if not OPENAI_API_KEY or OPENAI_API_KEY.strip() == "your_openai_api_key_here":
        return None, "Add your OpenAI API key to `.env` (OPENAI_API_KEY=...) to use this."
    try:
        import httpx
        from openai import OpenAI
        diagnosis = card.get("title", "Unknown")
        description = (card.get("description") or card.get("answer") or "").strip()
        contributor = card.get("contributor", "")
        photographer = card.get("photographer", "")
        context = f"Diagnosis: {diagnosis}.\nFindings/context: {description}"
        if contributor:
            context += f"\nContributor: {contributor}."
        if photographer:
            context += f"\nPhotographer: {photographer}."
        # Custom httpx client without env proxies to avoid "proxies" argument errors
        with httpx.Client(trust_env=False) as http_client:
            client = OpenAI(api_key=OPENAI_API_KEY, http_client=http_client)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an ABO-style ophthalmology oral boards examiner. Cases are scored on Data Acquisition, Diagnosis, and Management. Examiners may ask: "Why is this information useful?" "How would you perform this surgery?" "What if that therapy didn't help?" They do not encourage, teach, or acknowledge right/wrong—they assess. Give output a candidate could use to prepare: clear, systematic, concise. Use bullet points and short paragraphs. Structure your response using the three ABO categories below."""
                    },
                    {
                        "role": "user",
                        "content": f"""{context}

Using ABO Candidate Performance Criteria, provide a concise study outline in three sections:

**1. Data Acquisition**
- What relevant history to elicit (onset, progression, trauma, surgery, systemic risk factors).
- Important exam findings and ancillary testing to order (e.g., A/B scan, imaging, labs).

**2. Diagnosis**
- Differential diagnosis (what else to consider).
- Most likely diagnosis and key investigations that support it.

**3. Management**
- Safe, effective treatment plan: first-line and alternatives (dosing/renal adjustment if relevant), referral when appropriate.
- Potential complications of proposed treatment and expected outcomes/prognosis (cite trials if relevant, e.g., COMS).
- How to communicate the management plan and prognosis to the patient/family (clear, ethical).

End with 1–2 classic examiner follow-up questions (e.g., "How would you discuss prognosis with the patient?" "What if that didn't help? What other treatment might you consider?"). Be concise and board-style."""
                    }
                ],
                max_tokens=1200,
            )
        text = response.choices[0].message.content
        return text.strip(), None
    except Exception as e:
        return None, str(e)


def render_treatment_html(text):
    """Convert treatment markdown to styled HTML for the treatment box."""
    try:
        import markdown
        body = markdown.markdown(text, extensions=["nl2br"])
        return f'<div class="treatment-box"><div class="treatment-title">📋 Treatment & next steps (oral boards)</div>{body}</div>'
    except Exception:
        # Fallback: escape and wrap in <p> with line breaks
        import html
        escaped = html.escape(text).replace("\n", "<br>")
        return f'<div class="treatment-box"><div class="treatment-title">📋 Treatment & next steps (oral boards)</div><p>{escaped}</p></div>'


def display_images(images, show_captions=False):
    """Display images in a responsive grid."""
    if not images:
        st.warning("No images available for this card.")
        return
    
    # Filter out duplicates and extract URLs
    unique_images = []
    seen = set()
    for img in images:
        # Handle both old format (string URLs) and new format (dict with url key)
        if isinstance(img, str):
            url = img
            alt = ""
        else:
            url = img.get('url', '')
            alt = img.get('alt', '')
        
        if url and url not in seen:
            seen.add(url)
            unique_images.append({'url': url, 'alt': alt})
    
    num_images = len(unique_images)
    
    if num_images == 0:
        st.warning("No images available for this card.")
        return
    
    if num_images == 1:
        img = unique_images[0]
        caption = img['alt'] if (show_captions and img['alt']) else None
        st.image(img['url'], caption=caption, use_container_width=True)
    elif num_images == 2:
        col1, col2 = st.columns(2)
        with col1:
            img = unique_images[0]
            caption = img['alt'] if (show_captions and img['alt']) else None
            st.image(img['url'], caption=caption, use_container_width=True)
        with col2:
            img = unique_images[1]
            caption = img['alt'] if (show_captions and img['alt']) else None
            st.image(img['url'], caption=caption, use_container_width=True)
    else:
        # Multiple images in grid (max 3 columns)
        cols = st.columns(min(3, num_images))
        for i, img in enumerate(unique_images):
            with cols[i % len(cols)]:
                caption = img['alt'] if (show_captions and img['alt']) else None
                st.image(img['url'], caption=caption, use_container_width=True)


def main():
    flashcards = load_flashcards()
    
    if not flashcards:
        st.error("No flashcards found!")
        st.info("""
        **To get started:**
        1. Run `python extract_atlas.py` to extract the atlas database
        2. Run `python scrape_all.py --no-images` to scrape all conditions
        3. Run `python generate_flashcards.py` to generate flashcards
        4. Then refresh this page
        """)
        return
    
    # Get categories
    categories = get_unique_categories(flashcards)
    
    # Initialize session state
    if 'current_index' not in st.session_state:
        st.session_state.current_index = 0
    if 'show_answer' not in st.session_state:
        st.session_state.show_answer = False
    if 'selected_category' not in st.session_state:
        st.session_state.selected_category = 'ALL'
    if 'treatment_cache' not in st.session_state:
        st.session_state.treatment_cache = {}
    if 'random_start_done' not in st.session_state:
        st.session_state.random_start_done = False
    
    # Sidebar: search and category (so we have search term before filtering)
    with st.sidebar:
        st.markdown("## 👁️ EyeRounds Study")
        st.markdown("---")
        st.markdown("### 🔍 Keyword search")
        search_term = st.text_input(
            "Search",
            placeholder="e.g. retinitis pigmentosa",
            key="search",
            label_visibility="collapsed"
        )
        search_term = (search_term or "").strip()
        
        st.markdown("### Filter by Topic")
        
        new_category = st.selectbox(
            "Category",
            categories,
            index=categories.index(st.session_state.selected_category) if st.session_state.selected_category in categories else 0,
            key="category_select",
            label_visibility="collapsed"
        )
        
        # Handle category change (pick random card in new category)
        if new_category != st.session_state.selected_category:
            st.session_state.selected_category = new_category
            new_filtered = filter_flashcards(flashcards, new_category)
            new_filtered = filter_by_search(new_filtered, search_term) if search_term else new_filtered
            st.session_state.current_index = random.randint(0, len(new_filtered) - 1) if new_filtered else 0
            st.session_state.show_answer = False
            st.rerun()
    
    # Filter by category, then by search
    category_filtered = filter_flashcards(flashcards, st.session_state.selected_category)
    filtered_cards = filter_by_search(category_filtered, search_term) if search_term else category_filtered
    
    # Start with a random card on first load (and when changing category)
    if filtered_cards and not st.session_state.random_start_done:
        st.session_state.random_start_done = True
        st.session_state.current_index = random.randint(0, len(filtered_cards) - 1)
        st.rerun()
    
    # Keyboard shortcuts via query params (Enter/Space = reveal, ArrowRight = next)
    if "action" in st.query_params:
        action = st.query_params["action"]
        if isinstance(action, list):
            action = action[0] if action else None
        if action == "reveal":
            st.session_state.show_answer = True
        elif action == "next":
            st.session_state.current_index = (st.session_state.current_index + 1) % len(filtered_cards)
            st.session_state.show_answer = False
        # Remove param so we don't loop
        q = dict(st.query_params)
        q.pop("action", None)
        st.query_params.update(q)
        st.rerun()
    
    # Sidebar (continued): stats, navigation, card selector
    with st.sidebar:
        st.markdown("---")
        
        # Stats
        st.metric("Cards Available", len(filtered_cards))
        st.metric("Total in Database", len(flashcards))
        
        if len(filtered_cards) > 0:
            st.markdown("---")
            st.markdown("### Navigation")
            
            # Navigation buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("⬅️ Prev", use_container_width=True):
                    st.session_state.current_index = (st.session_state.current_index - 1) % len(filtered_cards)
                    st.session_state.show_answer = False
                    st.rerun()
            with col2:
                if st.button("Next ➡️", use_container_width=True):
                    st.session_state.current_index = (st.session_state.current_index + 1) % len(filtered_cards)
                    st.session_state.show_answer = False
                    st.rerun()
            
            if st.button("🎲 Random Card", use_container_width=True):
                st.session_state.current_index = random.randint(0, len(filtered_cards) - 1)
                st.session_state.show_answer = False
                st.rerun()
            
            st.caption("⌨️ Enter/Space = Reveal · → = Next")
            st.markdown("---")
            
            # Card selector
            st.markdown("### Jump to Card")
            card_options = [f"{i+1}. {c.get('title', 'Unknown')[:25]}..." for i, c in enumerate(filtered_cards)]
            selected_card = st.selectbox(
                "Select card",
                range(len(filtered_cards)),
                index=st.session_state.current_index,
                format_func=lambda x: card_options[x],
                label_visibility="collapsed"
            )
            
            if selected_card != st.session_state.current_index:
                st.session_state.current_index = selected_card
                st.session_state.show_answer = False
                st.rerun()
    
    # Main content
    if len(filtered_cards) == 0:
        st.warning(f"No flashcards found for category: {st.session_state.selected_category}")
        return
    
    # Ensure index is valid
    if st.session_state.current_index >= len(filtered_cards):
        st.session_state.current_index = 0
    
    current_card = filtered_cards[st.session_state.current_index]
    
    # Keyboard shortcuts: focusable iframe captures Enter/Space (reveal) and ArrowRight (next)
    # Sandbox may block location change; try parent + open(..., "_top") and ensure zone gets focus on click
    st.components.v1.html("""
    <div id="kb-zone" tabindex="0" style="
      outline: none; margin: 0; padding: 8px 10px; font-size: 13px; color: #333;
      background: #e3f2fd; border-radius: 8px; border: 1px solid #90caf9;
      cursor: pointer; text-align: center; font-weight: 500;
    " title="Click here first, then use Enter/Space to reveal, Arrow Right for next card">
      ⌨️ Click here first, then: <b>Enter</b> / <b>Space</b> = reveal · <b>→</b> = next card
    </div>
    <form id="kb-form" method="GET" target="_top" style="display:none;"></form>
    <script>
    (function() {
      var zone = document.getElementById("kb-zone");
      var form = document.getElementById("kb-form");
      function go(path) {
        var top = window.top;
        var base = (top.location.origin || "") + (top.location.pathname || "/");
        var url = base + path;
        try {
          form.action = url;
          form.submit();
        } catch (e) {
          try { top.location.href = url; } catch (e2) {
            try { window.open(url, "_top"); } catch (e3) {}
          }
        }
      }
      zone.addEventListener("click", function() { zone.focus(); });
      zone.addEventListener("keydown", function(e) {
        var k = e.key;
        if (k === "Enter" || k === " ") {
          e.preventDefault();
          e.stopPropagation();
          go("?action=reveal");
        } else if (k === "ArrowRight") {
          e.preventDefault();
          e.stopPropagation();
          go("?action=next");
        }
      });
    })();
    </script>
    """, height=48)
    
    # Header (and search caption when active)
    if search_term:
        st.caption(f"🔍 Showing {len(filtered_cards)} result(s) for \"{search_term}\"")
    st.markdown(f"""
    <div class="main-header">
        <h1>👁️ EyeRounds Flashcards</h1>
        <p>Card {st.session_state.current_index + 1} of {len(filtered_cards)}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Category badge
    category = current_card.get('category', 'UNCATEGORIZED')
    st.markdown(f'<span class="category-badge">{category}</span>', unsafe_allow_html=True)
    
    # Title - only show after reveal
    if st.session_state.show_answer:
        st.markdown(f"### {current_card.get('title', 'Unknown Condition')}")
    else:
        st.markdown("### What is the diagnosis?")
    
    # Images section
    st.markdown("---")
    st.markdown("#### 🖼️ Clinical Images")
    
    images = current_card.get('images', [])
    display_images(images, show_captions=st.session_state.show_answer)
    
    # Answer section
    st.markdown("---")
    
    if not st.session_state.show_answer:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("👁️ Reveal Answer", type="primary", use_container_width=True):
                st.session_state.show_answer = True
                st.rerun()
        
        st.markdown("""
        <div style="text-align: center; color: #666; margin-top: 0.4rem; font-size: 0.85rem;">
            <em>Study the images, then click or press <strong>Enter</strong> / <strong>Space</strong> to reveal · <strong>→</strong> next card</em>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Show answer
        st.markdown("#### ✅ Answer")
        st.markdown(f"**{current_card.get('title', 'Unknown')}**")
        
        description = current_card.get('description') or current_card.get('answer', '')
        if description:
            st.markdown(description)
        
        # Contributor info
        st.markdown("---")
        
        contributor = current_card.get('contributor', '')
        photographer = current_card.get('photographer', '')
        source_url = current_card.get('source_url') or current_card.get('url', '')
        
        if contributor:
            st.markdown(f"**Contributor:** {contributor}")
        if photographer:
            st.markdown(f"**Photographer:** {photographer}")
        if source_url:
            st.markdown(f"**Source:** [{source_url}]({source_url})")
        
        # Oral boards: treatment & next steps (GPT-4o) — runs automatically on reveal
        st.markdown("---")
        card_id = current_card.get("id", current_card.get("title", ""))
        cached = st.session_state.treatment_cache.get(card_id)
        
        if cached:
            st.markdown(render_treatment_html(cached), unsafe_allow_html=True)
        elif OPENAI_API_KEY and OPENAI_API_KEY.strip() != "your_openai_api_key_here":
            with st.spinner("Getting treatment & next steps..."):
                text, err = get_oral_boards_treatment(current_card)
            if err:
                st.error(err)
            else:
                st.session_state.treatment_cache[card_id] = text
                st.markdown(render_treatment_html(text), unsafe_allow_html=True)
        else:
            st.caption("Add `OPENAI_API_KEY` to `.env` to use treatment lookup.")
        
        # Next card button
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("➡️ Next Card", type="primary", use_container_width=True):
                st.session_state.current_index = (st.session_state.current_index + 1) % len(filtered_cards)
                st.session_state.show_answer = False
                st.rerun()
        st.caption("⌨️ Press → for next card")


if __name__ == "__main__":
    main()

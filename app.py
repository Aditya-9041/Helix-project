import streamlit as st
import requests
import re
import json
from datetime import datetime
import time

# Set page config
st.set_page_config(
    page_title="TruFact - Hallucination Audit Trail",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for styling
st.markdown("""
<style>
    :root {
        --green: #00ff88;
        --red: #ff3366;
        --orange: #ffaa00;
        --bg: #04040a;
    }
    .main {
        background-color: #0a0a12;
        color: #ffffff;
    }
    .stTextArea {
        background-color: #080812 !important;
    }
    .metric-box {
        background-color: #0c0c1a;
        border: 1px solid #ffffff14;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
    }
    .verified {
        border-left: 4px solid #00ff88;
        background-color: #00ff8805;
    }
    .hallucination {
        border-left: 4px solid #ff3366;
        background-color: #ff336605;
    }
    .unverified {
        border-left: 4px solid #ffaa00;
        background-color: #ffaa0005;
    }
    .claim-card {
        padding: 15px;
        margin: 10px 0;
        border-radius: 10px;
        border: 1px solid #ffffff14;
    }
</style>
""", unsafe_allow_html=True)

# API Credentials
CSE_ID = '4539d2e0d6d2c4332'
API_KEY = 'AIzaSyDY8xrumjkUGhGRs_NXOeWpRZ1J-Okk7KE'

def extract_claim_candidates(full_text):
    """Extract verifiable claims from text"""
    sentences = re.findall(r'[^.!?\n]+[.!?\n]+', full_text)
    seen = set()
    candidates = []
    
    for raw in sentences:
        s = raw.strip()
        if len(s) < 25 or len(s) > 500:
            continue
        
        # Check if sentence has verifiable content
        if not re.search(r'\b(\d{4}|\d+\s*%|\d+\s*(meter|km|miles?|ft|kg|°C|percent)|first|largest|smallest|most|tallest|never|always|only|invented|proved|cause|linked|visible|brain|vaccine|Einstein|Napoleon|Eiffel|Everest|speed of light)\b', s, re.IGNORECASE):
            continue
        
        key = s[:65].lower()
        if key in seen:
            continue
        seen.add(key)
        candidates.append(s)
    
    return candidates[:15]

def fetch_wikipedia_evidence(claim_text):
    """Search Wikipedia for evidence"""
    try:
        search_query = claim_text[:180].replace(r'[^\w\s]', ' ')
        search_url = f'https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={search_query}&srlimit=1&format=json&origin=*'
        
        response = requests.get(search_url, timeout=3.8)
        search_data = response.json()
        
        pages = search_data.get('query', {}).get('search', [])
        if not pages:
            return {'found': False, 'reason': 'No relevant Wikipedia page found'}
        
        page_title = pages[0]['title']
        extract_url = f'https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro&explaintext&titles={page_title}&format=json&origin=*'
        
        extract_response = requests.get(extract_url, timeout=3.5)
        extract_data = extract_response.json()
        
        pages_obj = extract_data.get('query', {}).get('pages', {})
        page_id = list(pages_obj.keys())[0]
        extract = pages_obj[page_id].get('extract', '')
        
        page_url = f'https://en.wikipedia.org/wiki/{page_title.replace(" ", "_")}'
        
        return {
            'found': True,
            'title': page_title,
            'extract': extract[:1800],
            'url': page_url
        }
    except Exception as e:
        return {'found': False, 'reason': f'Error: {str(e)}'}

def fetch_web_evidence(claim_text):
    """Search web using Google Custom Search"""
    try:
        search_query = claim_text[:180]
        search_url = f'https://www.googleapis.com/customsearch/v1?key={API_KEY}&cx={CSE_ID}&q={search_query}&num=1'
        
        response = requests.get(search_url, timeout=4)
        search_data = response.json()
        
        if 'error' in search_data:
            return {'found': False}
        
        items = search_data.get('items', [])
        if not items:
            return {'found': False}
        
        item = items[0]
        return {
            'found': True,
            'title': item.get('title'),
            'extract': item.get('snippet'),
            'url': item.get('link')
        }
    except Exception as e:
        return {'found': False}

def analyze_claim_with_extract(claim_text, wiki_data):
    """Analyze claim against Wikipedia evidence"""
    if not wiki_data.get('found') or not wiki_data.get('extract'):
        return {
            'status': 'unverified',
            'confidence': 34,
            'reasoning': wiki_data.get('reason', 'Could not retrieve authoritative sources.')
        }
    
    extract = wiki_data['extract'].lower()
    claim_lower = claim_text.lower()
    
    # Check for contradictions
    is_contradicted = bool(re.search(r'myth|false|incorrect|not visible|cannot be seen|debunked|no evidence|does not exist|not true|actually', extract, re.IGNORECASE))
    
    # Check for direct support
    positive_indicators = ["is", "was built", "stands", "confirmed", "has", "measured", "reaches", "located", "known as", "exactly"]
    supports_direct = any(ind in extract for ind in positive_indicators) and len(extract) > 80
    
    status = 'unverified'
    confidence = 45
    reasoning = ''
    
    if is_contradicted:
        status = 'hallucination'
        confidence = 24
        reasoning = f'Wikipedia contradicts this: "{extract[:200]}"'
    elif supports_direct:
        status = 'verified'
        confidence = 85
        reasoning = f'Wikipedia supports this: "{extract[:200]}"'
    else:
        overlap_score = len([w for w in extract.split() if w in claim_lower and len(w) > 4])
        if overlap_score > 2 and len(extract) > 200:
            status = 'verified'
            confidence = 68
            reasoning = f'Wikipedia provides related context: "{extract[:200]}"'
        else:
            status = 'unverified'
            confidence = 38
            reasoning = f'Limited evidence found: "{extract[:200]}"'
    
    return {
        'status': status,
        'confidence': min(100, max(0, confidence)),
        'reasoning': reasoning
    }

def verify_claim_live(claim_text):
    """Verify a single claim"""
    # Try Wikipedia first
    wiki_evidence = fetch_wikipedia_evidence(claim_text)
    
    if wiki_evidence.get('found'):
        analysis = analyze_claim_with_extract(claim_text, wiki_evidence)
        sources = [{'title': wiki_evidence['title'], 'url': wiki_evidence['url']}]
    else:
        # Try web search as fallback
        web_evidence = fetch_web_evidence(claim_text)
        if web_evidence.get('found'):
            extract = web_evidence['extract'].lower()
            has_debunking = bool(re.search(r'myth|false|incorrect|debunked', extract, re.IGNORECASE))
            
            if has_debunking:
                analysis = {
                    'status': 'hallucination',
                    'confidence': 28,
                    'reasoning': f'Web search found contradictions: "{web_evidence["extract"][:200]}"'
                }
            else:
                analysis = {
                    'status': 'unverified',
                    'confidence': 35,
                    'reasoning': f'Web search found: "{web_evidence["extract"][:200]}"'
                }
            sources = [{'title': web_evidence['title'], 'url': web_evidence['url']}]
        else:
            analysis = {
                'status': 'unverified',
                'confidence': 28,
                'reasoning': 'Could not find reliable sources to verify this claim.'
            }
            sources = []
    
    return {
        'id': str(time.time()),
        'text': claim_text,
        'status': analysis['status'],
        'confidence': analysis['confidence'],
        'category': 'Fact' if analysis['status'] == 'verified' else ('Debunked' if analysis['status'] == 'hallucination' else 'Uncertain'),
        'reasoning': analysis['reasoning'],
        'sources': sources
    }

# UI Layout
st.markdown("# 🔍 TruFact")
st.markdown("### Hallucination Audit Trail for LLM-Generated Documents")
st.markdown("---")

# Input section
col1, col2 = st.columns([4, 1])
with col1:
    user_text = st.text_area(
        "Paste your text here to audit for hallucinations:",
        height=180,
        placeholder="Enter text with claims to verify...",
        label_visibility="collapsed"
    )

with col2:
    st.write("")
    st.write("")
    audit_button = st.button("🔍 AUDIT", use_container_width=True, key="audit_btn")

# Process and display results
if audit_button and user_text:
    with st.spinner("Analyzing claims..."):
        claims = extract_claim_candidates(user_text)
        
        if not claims:
            st.warning("⚠️ No verifiable claims found in the text. Add specific facts with dates, numbers, or well-known entities.")
        else:
            results = []
            progress_bar = st.progress(0)
            
            for idx, claim in enumerate(claims):
                result = verify_claim_live(claim)
                results.append(result)
                progress_bar.progress((idx + 1) / len(claims))
            
            st.markdown("---")
            
            # Summary Statistics
            col1, col2, col3, col4 = st.columns(4)
            
            verified_count = len([r for r in results if r['status'] == 'verified'])
            unverified_count = len([r for r in results if r['status'] == 'unverified'])
            hallucination_count = len([r for r in results if r['status'] == 'hallucination'])
            avg_confidence = sum(r['confidence'] for r in results) / len(results) if results else 0
            
            with col1:
                st.markdown('<div class="metric-box">', unsafe_allow_html=True)
                st.metric("Total Claims", len(results))
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="metric-box">', unsafe_allow_html=True)
                st.metric("Verified ✓", verified_count)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col3:
                st.markdown('<div class="metric-box">', unsafe_allow_html=True)
                st.metric("Unverified ?", unverified_count)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col4:
                st.markdown('<div class="metric-box">', unsafe_allow_html=True)
                st.metric("Hallucinations ✗", hallucination_count)
                st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown("---")
            st.metric("Average Confidence", f"{int(avg_confidence)}%")
            
            st.markdown("---")
            st.subheader("📋 Detailed Results")
            
            # Filter options
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                show_verified = st.checkbox("Verified", value=True)
            with col2:
                show_unverified = st.checkbox("Unverified", value=True)
            with col3:
                show_hallucinations = st.checkbox("Hallucinations", value=True)
            
            # Display claims
            for result in results:
                if (result['status'] == 'verified' and not show_verified) or \
                   (result['status'] == 'unverified' and not show_unverified) or \
                   (result['status'] == 'hallucination' and not show_hallucinations):
                    continue
                
                status_color = 'verified' if result['status'] == 'verified' else \
                              ('hallucination' if result['status'] == 'hallucination' else 'unverified')
                
                with st.container():
                    st.markdown(f"""
                    <div class="claim-card {status_color}">
                        <div style="display: flex; justify-content: space-between; align-items: start;">
                            <div style="flex: 1;">
                                <span style="display: inline-block; background: {'#00ff8820' if result['status'] == 'verified' else '#ffaa0020' if result['status'] == 'unverified' else '#ff336620'}; color: {'#00ff88' if result['status'] == 'verified' else '#ffaa00' if result['status'] == 'unverified' else '#ff3366'}; padding: 5px 10px; border-radius: 5px; font-weight: bold; margin-right: 10px;">
                                    {result['category'].upper()}
                                </span>
                                <span style="display: inline-block; background: #ffffff10; padding: 5px 10px; border-radius: 5px; font-size: 12px;">
                                    {result['status'].upper()}
                                </span>
                                <p style="margin-top: 10px; font-size: 14px; color: #ffffffcc;">
                                    {result['text']}
                                </p>
                                <p style="margin-top: 10px; font-size: 12px; color: #ffffff99;">
                                    <strong>Analysis:</strong> {result['reasoning']}
                                </p>
                                {f'<p style="margin-top: 8px; font-size: 11px; color: #00ff88;"><strong>Source:</strong> <a href="{result["sources"][0]["url"]}" target="_blank">{result["sources"][0]["title"]}</a></p>' if result['sources'] else ''}
                            </div>
                            <div style="text-align: center; margin-left: 20px;">
                                <div style="font-size: 24px; font-weight: bold; color: {'#00ff88' if result['status'] == 'verified' else '#ffaa00' if result['status'] == 'unverified' else '#ff3366'};">
                                    {result['confidence']}%
                                </div>
                                <div style="font-size: 11px; color: #ffffff77;">Confidence</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #ffffff66; font-size: 12px; margin-top: 30px;">
    <p>🔍 TruFact - Real-time Hallucination Detection | Powered by Wikipedia & Web Search</p>
    <p style="margin-top: 10px;">Audit your AI-generated content for factual accuracy</p>
</div>
""", unsafe_allow_html=True)

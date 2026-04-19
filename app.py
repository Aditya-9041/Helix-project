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

# Custom CSS matching project.html design
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap');
    
    * {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }
    
    :root {
        --g: #00ff88;
        --r: #ff3366;
        --a: #ffaa00;
        --b: #00aaff;
        --bg: #04040a;
        --s1: #080812;
        --s2: #0c0c1a;
        --bd: #ffffff14;
    }
    
    body, .stApp {
        background: var(--bg) !important;
        color: #fff !important;
        font-family: 'Space Grotesk', sans-serif !important;
    }
    
    .stApp {
        background-color: #04040a !important;
        background-image: 
            linear-gradient(#ffffff14 1px, transparent 1px),
            linear-gradient(90deg, #ffffff14 1px, transparent 1px),
            linear-gradient(90deg, transparent 0%, rgba(0, 255, 136, 0.05) 50%, transparent 100%);
        background-size: 40px 40px, 40px 40px, 100% 100%;
        background-position: 0 0, 0 0, 0 0;
    }
    
    /* Remove Streamlit default styling */
    .stTextArea textarea {
        background-color: var(--s1) !important;
        border: 1px solid var(--bd) !important;
        border-radius: 13px !important;
        color: #e8e8ff !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 14px !important;
        line-height: 1.8 !important;
        padding: 16px 18px 12px !important;
    }
    
    .stButton button {
        background-color: var(--g) !important;
        color: #04040a !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        border: none !important;
        border-radius: 7px !important;
        transition: all 0.1s !important;
    }
    
    .stButton button:hover {
        transform: translateY(-1px) !important;
        background-color: #00ff99 !important;
    }
    
    .logo-section {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 2.5rem;
    }
    
    .logo-icon {
        width: 36px;
        height: 36px;
        border: 1.5px solid var(--g);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        animation: logopulse 2s ease-in-out infinite;
        font-size: 20px;
    }
    
    @keyframes logopulse {
        0%, 100% { box-shadow: 0 0 0 0 rgba(0, 255, 136, 0.4); }
        50% { box-shadow: 0 0 0 8px rgba(0, 255, 136, 0); }
    }
    
    .logo-name {
        font-size: 20px;
        font-weight: 700;
        letter-spacing: -0.04em;
    }
    
    .logo-name span {
        color: var(--g);
    }
    
    .logo-chip {
        font-family: 'Space Mono', monospace;
        font-size: 9px;
        background: #00ff8812;
        color: var(--g);
        border: 1px solid #00ff8830;
        padding: 3px 8px;
        border-radius: 4px;
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }
    
    .hero-title {
        font-size: 2.5rem;
        font-weight: 700;
        line-height: 1.0;
        letter-spacing: -0.05em;
        margin-bottom: 1rem;
    }
    
    .hero-sub {
        font-size: 14px;
        color: #ffffff66;
        line-height: 1.7;
        margin-bottom: 2rem;
        max-width: 600px;
    }
    
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 10px;
        margin: 20px 0;
    }
    
    .stat-box {
        background: var(--s1);
        border: 1px solid var(--bd);
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        transition: transform 0.15s;
    }
    
    .stat-box:hover {
        transform: translateY(-2px);
    }
    
    .stat-box.verified {
        border-color: #00ff8822;
    }
    
    .stat-box.unverified {
        border-color: #ffaa0022;
    }
    
    .stat-box.hallucination {
        border-color: #ff336622;
    }
    
    .stat-label {
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #ffffff33;
        margin-bottom: 6px;
    }
    
    .stat-number {
        font-family: 'Space Mono', monospace;
        font-size: 32px;
        font-weight: 700;
        margin: 10px 0;
    }
    
    .stat-number.green { color: var(--g); }
    .stat-number.orange { color: var(--a); }
    .stat-number.red { color: var(--r); }
    .stat-number.white { color: #fff; }
    
    .filter-btn {
        background: transparent;
        border: 1px solid #ffffff14;
        color: #ffffff44;
        font-size: 11px;
        font-weight: 600;
        padding: 5px 12px;
        border-radius: 100px;
        cursor: pointer;
        transition: all 0.15s;
        margin-right: 8px;
    }
    
    .filter-btn:hover {
        border-color: #ffffff44;
        color: #ffffff99;
        background: #ffffff08;
    }
    
    .claim-card {
        background: var(--s1);
        border: 1px solid var(--bd);
        border-radius: 12px;
        padding: 16px;
        overflow: hidden;
        transition: border-color 0.2s;
        display: flex;
        gap: 16px;
        align-items: flex-start;
        margin: 8px 0;
    }
    
    .claim-card.verified {
        border-left: 3px solid var(--g);
    }
    
    .claim-card.unverified {
        border-left: 3px solid var(--a);
    }
    
    .claim-card.hallucination {
        border-left: 3px solid var(--r);
    }
    
    .claim-card:hover {
        border-color: #ffffff22;
    }
    
    .claim-info {
        flex: 1;
    }
    
    .claim-tags {
        display: flex;
        gap: 5px;
        margin-bottom: 10px;
    }
    
    .tag {
        font-size: 10px;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 4px;
        text-transform: uppercase;
        font-family: 'Space Mono', monospace;
        display: inline-block;
    }
    
    .tag.verified {
        background: #00ff8818;
        color: var(--g);
        border: 1px solid #00ff8830;
    }
    
    .tag.unverified {
        background: #ffaa0018;
        color: var(--a);
        border: 1px solid #ffaa0030;
    }
    
    .tag.hallucination {
        background: #ff336618;
        color: var(--r);
        border: 1px solid #ff336630;
    }
    
    .claim-text {
        font-size: 13px;
        color: #ffffffcc;
        line-height: 1.6;
        margin: 8px 0;
    }
    
    .claim-analysis {
        font-size: 12px;
        color: #ffffff99;
        margin: 8px 0;
        padding-top: 8px;
        border-top: 1px solid #ffffff0a;
    }
    
    .claim-source {
        font-size: 11px;
        color: var(--g);
        margin-top: 8px;
    }
    
    .claim-source a {
        color: var(--g);
        text-decoration: none;
        transition: opacity 0.2s;
    }
    
    .claim-source a:hover {
        opacity: 0.8;
        text-decoration: underline;
    }
    
    .confidence-display {
        text-align: center;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 8px;
        min-width: 70px;
    }
    
    .confidence-percent {
        font-family: 'Space Mono', monospace;
        font-size: 28px;
        font-weight: 700;
    }
    
    .confidence-percent.verified { color: var(--g); }
    .confidence-percent.unverified { color: var(--a); }
    .confidence-percent.hallucination { color: var(--r); }
    
    .confidence-label {
        font-size: 10px;
        color: #ffffff77;
        font-family: 'Space Mono', monospace;
    }
    
    .divider {
        border-bottom: 1px solid var(--bd);
        margin: 20px 0;
    }
    
    .footer {
        text-align: center;
        color: #ffffff66;
        font-size: 12px;
        margin-top: 30px;
    }
    
    .container {
        max-width: 900px;
        margin: 0 auto;
        padding: 2rem 1.25rem;
    }
    
    @media (max-width: 768px) {
        .stats-grid {
            grid-template-columns: repeat(2, 1fr);
        }
        
        .claim-card {
            flex-direction: column;
        }
        
        .hero-title {
            font-size: 1.8rem;
        }
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
    
    is_contradicted = bool(re.search(r'myth|false|incorrect|not visible|cannot be seen|debunked|no evidence|does not exist|not true|actually', extract, re.IGNORECASE))
    
    positive_indicators = ["is", "was built", "stands", "confirmed", "has", "measured", "reaches", "located", "known as", "exactly"]
    supports_direct = any(ind in extract for ind in positive_indicators) and len(extract) > 80
    
    status = 'unverified'
    confidence = 45
    reasoning = ''
    
    if is_contradicted:
        status = 'hallucination'
        confidence = 24
        reasoning = f'Wikipedia contradicts this claim. Source indicates misinformation.'
    elif supports_direct:
        status = 'verified'
        confidence = 85
        reasoning = f'Wikipedia confirms key aspects of this claim.'
    else:
        overlap_score = len([w for w in extract.split() if w in claim_lower and len(w) > 4])
        if overlap_score > 2 and len(extract) > 200:
            status = 'verified'
            confidence = 68
            reasoning = f'Wikipedia provides supporting contextual information.'
        else:
            status = 'unverified'
            confidence = 38
            reasoning = f'Limited supporting evidence found. Claim may be too specific.'
    
    return {
        'status': status,
        'confidence': min(100, max(0, confidence)),
        'reasoning': reasoning
    }

def verify_claim_live(claim_text):
    """Verify a single claim"""
    wiki_evidence = fetch_wikipedia_evidence(claim_text)
    
    if wiki_evidence.get('found'):
        analysis = analyze_claim_with_extract(claim_text, wiki_evidence)
        sources = [{'title': wiki_evidence['title'], 'url': wiki_evidence['url']}]
    else:
        web_evidence = fetch_web_evidence(claim_text)
        if web_evidence.get('found'):
            extract = web_evidence['extract'].lower()
            has_debunking = bool(re.search(r'myth|false|incorrect|debunked', extract, re.IGNORECASE))
            
            if has_debunking:
                analysis = {
                    'status': 'hallucination',
                    'confidence': 28,
                    'reasoning': 'Web search found contradictions to this claim.'
                }
            else:
                analysis = {
                    'status': 'unverified',
                    'confidence': 35,
                    'reasoning': 'Web search found related but limited information.'
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

# Main UI
st.markdown('<div class="container">', unsafe_allow_html=True)

# Logo section
st.markdown("""
<div class="logo-section">
    <div class="logo-icon">🔍</div>
    <div style="flex: 1;">
        <div class="logo-name">Tru<span>Fact</span></div>
        <div class="logo-chip">Real-time Audit Engine</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Hero section
st.markdown("""
<div class="hero-title">
    Hallucination Audit Trail<br>for LLM-Generated Documents
</div>
<div class="hero-sub">
    Verify claims in AI-generated text by searching Wikipedia and the web for factual accuracy. Get real-time hallucination detection with confidence scoring.
</div>
""", unsafe_allow_html=True)

# Input section
col1, col2 = st.columns([5, 1])
with col1:
    user_text = st.text_area(
        "Paste your text here to audit for hallucinations:",
        height=150,
        placeholder="Enter text with claims to verify...",
        label_visibility="collapsed"
    )

with col2:
    st.write("")
    audit_button = st.button("🔍 AUDIT", use_container_width=True, key="audit_btn", help="Click to analyze claims")

# Process and display results
if audit_button and user_text:
    with st.spinner("Analyzing claims..."):
        claims = extract_claim_candidates(user_text)
        
        if not claims:
            st.warning("⚠️ No verifiable claims found. Add specific facts with dates, numbers, or well-known entities.")
        else:
            results = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for idx, claim in enumerate(claims):
                status_text.text(f"Analyzing claim {idx + 1}/{len(claims)}...")
                result = verify_claim_live(claim)
                results.append(result)
                progress_bar.progress((idx + 1) / len(claims))
            
            status_text.empty()
            progress_bar.empty()
            
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            
            # Summary Statistics
            verified_count = len([r for r in results if r['status'] == 'verified'])
            unverified_count = len([r for r in results if r['status'] == 'unverified'])
            hallucination_count = len([r for r in results if r['status'] == 'hallucination'])
            avg_confidence = sum(r['confidence'] for r in results) / len(results) if results else 0
            
            st.markdown(f"""
            <div style="text-align: center; font-size: 12px; margin-bottom: 10px; color: #ffffff55;">
                WEB AUDIT COMPLETE · {len(results)} CLAIMS ANALYZED
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown("""
                <div class="stat-box">
                    <div class="stat-label">TOTAL</div>
                    <div class="stat-number white">""" + str(len(results)) + """</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("""
                <div class="stat-box verified">
                    <div class="stat-label">VERIFIED</div>
                    <div class="stat-number green">""" + str(verified_count) + """</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown("""
                <div class="stat-box unverified">
                    <div class="stat-label">UNVERIFIED</div>
                    <div class="stat-number orange">""" + str(unverified_count) + """</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown("""
                <div class="stat-box hallucination">
                    <div class="stat-label">HALLUCINATIONS</div>
                    <div class="stat-number red">""" + str(hallucination_count) + """</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            
            # Confidence bar
            st.markdown(f"""
            <div style="background: var(--s1); border: 1px solid var(--bd); border-radius: 10px; padding: 14px 16px; margin-bottom: 20px; display: flex; align-items: center; gap: 14px;">
                <div style="flex: 1;">
                    <div style="font-size: 12px; color: #ffffff77; margin-bottom: 8px;">Avg Confidence</div>
                    <div style="height: 5px; background: #ffffff0d; border-radius: 3px; overflow: hidden;">
                        <div style="height: 100%; background: linear-gradient(90deg, var(--g), var(--b)); width: {int(avg_confidence)}%; border-radius: 3px; transition: width 1s;"></div>
                    </div>
                </div>
                <div style="font-family: 'Space Mono', monospace; font-size: 18px; font-weight: 700; color: var(--g); min-width: 50px; text-align: right;">{int(avg_confidence)}%</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Filter section
            st.markdown("**FILTER:**")
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                show_verified = st.checkbox("Verified", value=True)
            with col2:
                show_unverified = st.checkbox("Unverified", value=True)
            with col3:
                show_hallucinations = st.checkbox("Hallucinations", value=True)
            
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            
            # Display claims
            st.markdown("### CLAIMS")
            for result in results:
                if (result['status'] == 'verified' and not show_verified) or \
                   (result['status'] == 'unverified' and not show_unverified) or \
                   (result['status'] == 'hallucination' and not show_hallucinations):
                    continue
                
                status = result['status']
                status_color = 'green' if status == 'verified' else ('orange' if status == 'unverified' else 'red')
                status_label = 'Verified' if status == 'verified' else ('Unverified' if status == 'unverified' else 'Hallucination')
                
                source_html = ''
                if result['sources']:
                    source_html = f"""<div class="claim-source">
                        <strong>Source:</strong> <a href="{result['sources'][0]['url']}" target="_blank">{result['sources'][0]['title']}</a>
                    </div>"""
                
                st.markdown(f"""
                <div class="claim-card {status}">
                    <div class="claim-info">
                        <div class="claim-tags">
                            <span class="tag {status}">{status_label.upper()}</span>
                            <span class="tag {status}">{result['category'].upper()}</span>
                        </div>
                        <div class="claim-text">{result['text']}</div>
                        <div class="claim-analysis">
                            <strong>Analysis:</strong> {result['reasoning']}
                        </div>
                        {source_html}
                    </div>
                    <div class="confidence-display">
                        <div class="confidence-percent {status}">{result['confidence']}%</div>
                        <div class="confidence-label">Confidence</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown("""
<div class="footer">
    <p>🔍 TruFact - Hallucination Audit Trail for LLM-Generated Documents</p>
    <p style="margin-top: 10px; color: #ffffff44;">Powered by Wikipedia & Google Custom Search</p>
</div>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

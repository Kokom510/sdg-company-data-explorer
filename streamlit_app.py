
import re
import requests
import streamlit as st
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

st.set_page_config(page_title="SDG Company Data Explorer", page_icon="🌍", layout="wide")

SDGS = {
    1: ("No Poverty", ["poverty", "living wage", "financial inclusion", "community investment"]),
    2: ("Zero Hunger", ["hunger", "food security", "nutrition", "food waste", "agriculture"]),
    3: ("Good Health and Well-being", ["health", "wellbeing", "occupational health", "safety", "mental health"]),
    4: ("Quality Education", ["education", "training", "skills", "scholarship", "literacy"]),
    5: ("Gender Equality", ["gender equality", "women", "female leadership", "pay gap", "diversity"]),
    6: ("Clean Water and Sanitation", ["water", "wastewater", "sanitation", "water efficiency"]),
    7: ("Affordable and Clean Energy", ["renewable energy", "solar", "wind", "clean energy", "energy efficiency"]),
    8: ("Decent Work and Economic Growth", ["decent work", "employment", "labour", "human rights", "economic impact"]),
    9: ("Industry, Innovation and Infrastructure", ["innovation", "infrastructure", "technology", "research and development"]),
    10: ("Reduced Inequalities", ["inequality", "inclusion", "access", "underserved", "equal opportunity"]),
    11: ("Sustainable Cities and Communities", ["cities", "housing", "transport", "community development", "urban"]),
    12: ("Responsible Consumption and Production", ["circular economy", "recycling", "waste", "sustainable sourcing", "resource efficiency"]),
    13: ("Climate Action", ["climate", "carbon", "emissions", "net zero", "decarbonisation"]),
    14: ("Life Below Water", ["ocean", "marine", "fisheries", "plastic pollution", "water ecosystems"]),
    15: ("Life on Land", ["biodiversity", "deforestation", "forests", "land", "ecosystems"]),
    16: ("Peace, Justice and Strong Institutions", ["governance", "ethics", "anti-corruption", "human rights", "compliance"]),
    17: ("Partnerships for the Goals", ["partnership", "stakeholder", "collaboration", "sdg", "sustainable development"]),
}

def search_web(company, max_results=8):
    """Uses DuckDuckGo's public HTML results as a no-key prototype source."""
    q = quote_plus(f'"{company}" sustainability ESG SDG report')
    url = f"https://html.duckduckgo.com/html/?q={q}"
    headers = {"User-Agent": "Mozilla/5.0 SDG-Company-Data-Explorer/1.0"}
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    results = []
    for item in soup.select(".result")[:max_results]:
        a = item.select_one(".result__a")
        snip = item.select_one(".result__snippet")
        if a:
            results.append({
                "title": a.get_text(" ", strip=True),
                "url": a.get("href", ""),
                "snippet": snip.get_text(" ", strip=True) if snip else ""
            })
    return results

def fetch_page(url):
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 SDG-Company-Data-Explorer/1.0"},
                          timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        return soup.get_text(" ", strip=True)[:150000]
    except Exception:
        return ""

def score_sdgs(text):
    low = text.lower()
    scores = {}
    evidence = {}
    for n, (name, keywords) in SDGS.items():
        hits = []
        for kw in keywords:
            count = len(re.findall(r"\b" + re.escape(kw.lower()) + r"\b", low))
            if count:
                hits.append((kw, count))
        # 0-100 proxy score; intentionally capped and frequency-normalised
        raw = sum(min(c, 8) for _, c in hits)
        score = min(100, round(raw / max(1, len(keywords)) * 18))
        scores[n] = score
        evidence[n] = [x[0] for x in sorted(hits, key=lambda z: z[1], reverse=True)[:4]]
    return scores, evidence

st.title("🌍 SDG Impact Scorecard")
st.caption("SDG Sector Impact Scoring Model to assess a potential or existing investment company's contribution to the UN Sustainable Development Goals (SDGs), scored against the sector-relevant targets and indicators of a chosen framework.")

with st.sidebar:
    st.header("Company")
    company = st.text_input("Company name", "Nedbank")
    st.header("Enter Company Name")

company_options = [
    f"{name} ({ticker})"
    for name, ticker in jse_companies.items()
]

company_selected = st.selectbox(
    "Company",
    company_options,
    index=None,
    placeholder="Start typing a company name..."
)

if company_selected:
    company = company_selected.rsplit(" (", 1)[0]
    ticker = company_selected.rsplit("(", 1)[1].replace(")", "")
    n = st.slider("Web results to collect", 3, 12, 8)
    run = st.button("Enter", type="primary")
    st.divider()
    st.markdown("**Important:** Scores are a transparent keyword-based research proxy, not an official SDG rating. Validate evidence before using it for investment, reporting or client decisions.")

if run:
    with st.spinner("Searching the internet and analysing public disclosures..."):
        try:
            results = search_web(company, n)
        except Exception as e:
            st.error(f"Web search failed: {e}")
            st.stop()

        if not results:
            st.warning("No search results were returned. Try a more specific company name.")
            st.stop()

        combined = ""
        analysed = []
        for item in results:
            text = fetch_page(item["url"])
            combined += " " + item["title"] + " " + item["snippet"] + " " + text
            analysed.append({**item, "page_text": text})

        scores, evidence = score_sdgs(combined)

    st.subheader(f"SDG profile: {company}")
    cols = st.columns(4)
    for i, (sdg, (name, _)) in enumerate(SDGS.items()):
        with cols[i % 4]:
            st.metric(f"SDG {sdg}", f"{scores[sdg]}/100", name)
            if evidence[sdg]:
                st.caption("Evidence terms: " + ", ".join(evidence[sdg]))
            else:
                st.caption("No matching evidence found")

    st.divider()
    st.subheader("Internet sources collected")
    for item in analysed:
        st.markdown(f"**{item['title']}**")
        st.write(item["snippet"] or "No search snippet available.")
        st.link_button("Open source", item["url"])

    st.divider()
    st.subheader("How the score works")
    st.write(
        "The prototype searches public web results for the company, retrieves accessible pages, "
        "looks for SDG-relevant evidence terms, and converts the observed evidence into a 0–100 "
        "research score. It does not claim that a company contributes positively to an SDG merely "
        "because the topic is mentioned."
    )

else:
    st.info("Enter a company and click **Collect SDG data**.")
    st.markdown("""
### What this prototype can do
- Search the public internet for company sustainability / ESG / SDG disclosures.
- Retrieve accessible web pages.
- Map evidence to all **17 SDGs**.
- Produce a company-level SDG profile.
- Show the source pages used for the analysis.

### Recommended next version
For a serious investment/ESG workflow, replace the keyword score with a **sector-based SDG methodology**:
1. Define expected SDG contributions by sector.
2. Collect quantitative KPIs from annual/sustainability reports.
3. Store source, reporting year, metric, unit and page reference.
4. Separate **positive contribution, negative impact, risk and no evidence**.
5. Calculate scores consistently across companies.
6. Add an analyst review/override and an audit trail.
""")


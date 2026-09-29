import re
import requests
import streamlit as st
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from datetime import datetime


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="SDG Company Scorecard",
    page_icon="🌍",
    layout="wide"
)


# ============================================================
# SDG DEFINITIONS
# ============================================================

SDGS = {
    1: {
        "name": "No Poverty",
        "keywords": [
            "poverty",
            "living wage",
            "financial inclusion",
            "community investment",
            "economic inclusion"
        ]
    },

    2: {
        "name": "Zero Hunger",
        "keywords": [
            "hunger",
            "food security",
            "nutrition",
            "food waste",
            "agriculture"
        ]
    },

    3: {
        "name": "Good Health and Well-being",
        "keywords": [
            "health",
            "wellbeing",
            "occupational health",
            "safety",
            "mental health"
        ]
    },

    4: {
        "name": "Quality Education",
        "keywords": [
            "education",
            "training",
            "skills",
            "scholarship",
            "literacy",
            "learnership"
        ]
    },

    5: {
        "name": "Gender Equality",
        "keywords": [
            "gender equality",
            "women",
            "female leadership",
            "pay gap",
            "diversity",
            "gender"
        ]
    },

    6: {
        "name": "Clean Water and Sanitation",
        "keywords": [
            "water",
            "wastewater",
            "sanitation",
            "water efficiency",
            "water consumption"
        ]
    },

    7: {
        "name": "Affordable and Clean Energy",
        "keywords": [
            "renewable energy",
            "solar",
            "wind",
            "clean energy",
            "energy efficiency",
            "renewable"
        ]
    },

    8: {
        "name": "Decent Work and Economic Growth",
        "keywords": [
            "decent work",
            "employment",
            "labour",
            "human rights",
            "economic impact",
            "jobs"
        ]
    },

    9: {
        "name": "Industry, Innovation and Infrastructure",
        "keywords": [
            "innovation",
            "infrastructure",
            "technology",
            "research and development",
            "digital transformation"
        ]
    },

    10: {
        "name": "Reduced Inequalities",
        "keywords": [
            "inequality",
            "inclusion",
            "access",
            "underserved",
            "equal opportunity",
            "financial inclusion"
        ]
    },

    11: {
        "name": "Sustainable Cities and Communities",
        "keywords": [
            "cities",
            "housing",
            "transport",
            "community development",
            "urban",
            "sustainable cities"
        ]
    },

    12: {
        "name": "Responsible Consumption and Production",
        "keywords": [
            "circular economy",
            "recycling",
            "waste",
            "sustainable sourcing",
            "resource efficiency",
            "responsible consumption"
        ]
    },

    13: {
        "name": "Climate Action",
        "keywords": [
            "climate",
            "carbon",
            "emissions",
            "net zero",
            "decarbonisation",
            "greenhouse gas"
        ]
    },

    14: {
        "name": "Life Below Water",
        "keywords": [
            "ocean",
            "marine",
            "fisheries",
            "plastic pollution",
            "water ecosystems",
            "marine ecosystem"
        ]
    },

    15: {
        "name": "Life on Land",
        "keywords": [
            "biodiversity",
            "deforestation",
            "forests",
            "land",
            "ecosystems",
            "nature"
        ]
    },

    16: {
        "name": "Peace, Justice and Strong Institutions",
        "keywords": [
            "governance",
            "ethics",
            "anti-corruption",
            "human rights",
            "compliance",
            "integrity"
        ]
    },

    17: {
        "name": "Partnerships for the Goals",
        "keywords": [
            "partnership",
            "stakeholder",
            "collaboration",
            "sdg",
            "sustainable development",
            "partnerships"
        ]
    }
}


# ============================================================
# SECTOR METHODOLOGY
# ============================================================

SECTOR_WEIGHTS = {

    "Banking & Financial Services": {
        1: 5,
        2: 2,
        3: 4,
        4: 4,
        5: 5,
        6: 2,
        7: 5,
        8: 5,
        9: 4,
        10: 5,
        11: 3,
        12: 3,
        13: 5,
        14: 1,
        15: 2,
        16: 5,
        17: 4
    },

    "Mining & Metals": {
        1: 4,
        2: 2,
        3: 5,
        4: 3,
        5: 3,
        6: 5,
        7: 4,
        8: 5,
        9: 4,
        10: 3,
        11: 3,
        12: 5,
        13: 5,
        14: 4,
        15: 5,
        16: 5,
        17: 3
    },

    "Energy & Utilities": {
        1: 3,
        2: 2,
        3: 4,
        4: 3,
        5: 3,
        6: 4,
        7: 5,
        8: 5,
        9: 5,
        10: 3,
        11: 4,
        12: 5,
        13: 5,
        14: 3,
        15: 4,
        16: 4,
        17: 4
    },

    "Consumer Goods": {
        1: 3,
        2: 4,
        3: 4,
        4: 3,
        5: 4,
        6: 4,
        7: 3,
        8: 5,
        9: 3,
        10: 4,
        11: 3,
        12: 5,
        13: 4,
        14: 4,
        15: 4,
        16: 3,
        17: 3
    },

    "Technology": {
        1: 3,
        2: 2,
        3: 4,
        4: 5,
        5: 5,
        6: 2,
        7: 3,
        8: 5,
        9: 5,
        10: 4,
        11: 3,
        12: 3,
        13: 3,
        14: 1,
        15: 2,
        16: 5,
        17: 4
    },

    "Real Estate": {
        1: 3,
        2: 1,
        3: 4,
        4: 3,
        5: 3,
        6: 5,
        7: 5,
        8: 5,
        9: 4,
        10: 3,
        11: 5,
        12: 5,
        13: 5,
        14: 2,
        15: 4,
        16: 4,
        17: 3
    },

    "Healthcare": {
        1: 3,
        2: 4,
        3: 5,
        4: 4,
        5: 4,
        6: 4,
        7: 3,
        8: 5,
        9: 5,
        10: 4,
        11: 3,
        12: 3,
        13: 3,
        14: 2,
        15: 2,
        16: 4,
        17: 4
    },

    "General / Other": {
        sdg: 3
        for sdg in range(1, 18)
    }
}


# ============================================================
# SEARCH FUNCTION
# ============================================================

def search_web(company, max_results=8):

    query = f'"{company}" sustainability ESG SDG report'

    q = quote_plus(query)

    endpoints = [
        f"https://html.duckduckgo.com/html/?q={q}",
        f"https://lite.duckduckgo.com/lite/?q={q}"
    ]

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/150.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,"
            "application/xml;q=0.9,*/*;q=0.8"
        ),
        "Accept-Language": "en-US,en;q=0.9"
    }

    last_error = None

    for endpoint in endpoints:

        for attempt in range(2):

            try:

                response = requests.get(
                    endpoint,
                    headers=headers,
                    timeout=30
                )

                response.raise_for_status()

                soup = BeautifulSoup(
                    response.text,
                    "html.parser"
                )

                results = []

                # Standard DuckDuckGo results
                for item in soup.select(".result")[:max_results]:

                    link = item.select_one(".result__a")
                    snippet = item.select_one(".result__snippet")

                    if link:

                        results.append({
                            "title": link.get_text(
                                " ",
                                strip=True
                            ),

                            "url": link.get(
                                "href",
                                ""
                            ),

                            "snippet": (
                                snippet.get_text(
                                    " ",
                                    strip=True
                                )
                                if snippet else ""
                            )
                        })

                if results:
                    return results

            except requests.exceptions.Timeout:

                last_error = (
                    f"Search timed out on attempt "
                    f"{attempt + 1}"
                )

            except requests.exceptions.RequestException as e:

                last_error = str(e)

    raise RuntimeError(
        "Unable to retrieve web search results. "
        + str(last_error)
    )


# ============================================================
# PAGE RETRIEVAL
# ============================================================

def fetch_page(url):

    try:

        response = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 SDG-Company-Scorecard/2.0"
            },
            timeout=20
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        for tag in soup(
            ["script", "style", "noscript"]
        ):
            tag.decompose()

        text = soup.get_text(
            " ",
            strip=True
        )

        return text[:150000]

    except Exception:

        return ""


# ============================================================
# REPORTING YEAR DETECTION
# ============================================================

def detect_year(text):

    years = re.findall(
        r"\b(20[1-2][0-9])\b",
        text
    )

    if not years:
        return "Unknown"

    year_counts = {}

    for year in years:

        year_counts[year] = (
            year_counts.get(year, 0) + 1
        )

    return max(
        year_counts,
        key=year_counts.get
    )


# ============================================================
# EVIDENCE CLASSIFICATION
# ============================================================

def classify_evidence(text):

    low = text.lower()

    positive_terms = [
        "increased",
        "improved",
        "reduced",
        "supported",
        "invested",
        "provided",
        "renewable",
        "achieved",
        "target achieved",
        "progress"
    ]

    negative_terms = [
        "increase in emissions",
        "negative impact",
        "incident",
        "spill",
        "violation",
        "breach",
        "controversy",
        "penalty",
        "non-compliance"
    ]

    risk_terms = [
        "risk",
        "exposure",
        "material risk",
        "potential impact",
        "transition risk",
        "physical risk"
    ]

    positive_hits = sum(
        low.count(term)
        for term in positive_terms
    )

    negative_hits = sum(
        low.count(term)
        for term in negative_terms
    )

    risk_hits = sum(
        low.count(term)
        for term in risk_terms
    )

    if negative_hits > positive_hits and negative_hits > risk_hits:
        return "Negative Impact"

    if positive_hits > risk_hits:
        return "Positive Contribution"

    if risk_hits > 0:
        return "Risk / Exposure"

    return "Evidence Identified"


# ============================================================
# SDG EVIDENCE EXTRACTION
# ============================================================

def extract_sdg_evidence(text, sdg_number):

    if not text:
        return []

    low = text.lower()

    keywords = SDGS[sdg_number]["keywords"]

    evidence = []

    for keyword in keywords:

        matches = list(
            re.finditer(
                re.escape(keyword.lower()),
                low
            )
        )

        for match in matches[:3]:

            start = max(
                0,
                match.start() - 180
            )

            end = min(
                len(text),
                match.end() + 300
            )

            passage = text[start:end].strip()

            if len(passage) > 40:

                evidence.append({
                    "keyword": keyword,
                    "text": passage
                })

    return evidence[:6]


# ============================================================
# SCORE SDG
# ============================================================

def calculate_sdg_score(
    evidence_count,
    sector_weight,
    evidence_type
):

    if evidence_count == 0:
        base_score = 0

    elif evidence_count == 1:
        base_score = 30

    elif evidence_count == 2:
        base_score = 50

    elif evidence_count == 3:
        base_score = 65

    elif evidence_count == 4:
        base_score = 75

    elif evidence_count == 5:
        base_score = 85

    else:
        base_score = 90

    # Sector materiality adjustment
    materiality_factor = sector_weight / 5

    score = base_score * materiality_factor

    # Evidence type adjustment
    if evidence_type == "Positive Contribution":
        score *= 1.0

    elif evidence_type == "Risk / Exposure":
        score *= 0.65

    elif evidence_type == "Negative Impact":
        score *= 0.25

    score = max(
        0,
        min(
            100,
            round(score)
        )
    )

    return score


# ============================================================
# ANALYSE COMPANY
# ============================================================

def analyse_company(
    company,
    sector,
    analysed_pages
):

    combined_text = ""

    for page in analysed_pages:

        combined_text += (
            " "
            + page["title"]
            + " "
            + page["snippet"]
            + " "
            + page["page_text"]
        )

    sector_weights = SECTOR_WEIGHTS[sector]

    results = {}

    for sdg_number in SDGS:

        evidence = extract_sdg_evidence(
            combined_text,
            sdg_number
        )

        if evidence:

            evidence_type = classify_evidence(
                " ".join(
                    x["text"]
                    for x in evidence
                )
            )

        else:

            evidence_type = "No Evidence"

        score = calculate_sdg_score(
            len(evidence),
            sector_weights[sdg_number],
            evidence_type
        )

        results[sdg_number] = {

            "score": score,

            "evidence_count": len(
                evidence
            ),

            "evidence_type": evidence_type,

            "evidence": evidence,

            "materiality": sector_weights[
                sdg_number
            ]
        }

    return results


# ============================================================
# APP HEADER
# ============================================================

st.title(
    "🌍 SDG Company Scorecard"
)

st.caption(
    "Version 2 — sector-based research prototype "
    "for analysing public company sustainability disclosures."
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("Company")

    company = st.text_input(
        "Company name",
        "Nedbank"
    )

    sector = st.selectbox(
        "Company sector",
        list(
            SECTOR_WEIGHTS.keys()
        )
    )

    n = st.slider(
        "Web results to collect",
        3,
        12,
        8
    )

    run = st.button(
        "Collect SDG data",
        type="primary"
    )

    st.divider()

    st.markdown(
        """
        **Methodology**

        The scorecard considers:

        - Sector materiality
        - Public sustainability evidence
        - Evidence volume
        - Evidence direction
        - Reporting year
        - Source transparency

        Scores are a research prototype and
        should be reviewed by an analyst before
        being used for investment, reporting or
        client decisions.
        """
    )


# ============================================================
# RUN ANALYSIS
# ============================================================

if run:

    with st.spinner(
        "Searching public disclosures and analysing SDG evidence..."
    ):

        # ----------------------------------------------------
        # SEARCH
        # ----------------------------------------------------

        try:

            results = search_web(
                company,
                n
            )

        except Exception as e:

            st.error(
                "The web search service could not be reached."
            )

            st.info(
                "Please try again in a few seconds."
            )

            st.caption(
                f"Technical detail: {e}"
            )

            st.stop()

        if not results:

            st.warning(
                "No search results were returned."
            )

            st.stop()

        # ----------------------------------------------------
        # FETCH SOURCES
        # ----------------------------------------------------

        analysed = []

        progress = st.progress(0)

        for i, item in enumerate(results):

            page_text = fetch_page(
                item["url"]
            )

            analysed.append({

                **item,

                "page_text": page_text,

                "reporting_year": detect_year(
                    page_text
                )
            })

            progress.progress(
                (i + 1) / len(results)
            )

        progress.empty()

        # ----------------------------------------------------
        # ANALYSE
        # ----------------------------------------------------

        sdg_results = analyse_company(
            company,
            sector,
            analysed
        )


    # ========================================================
    # COMPANY SUMMARY
    # ========================================================

    st.subheader(
        f"SDG Profile: {company}"
    )

    st.write(
        f"**Sector:** {sector}"
    )

    st.write(
        "The analysis identifies publicly disclosed "
        "evidence relevant to each SDG and adjusts "
        "the research score according to sector materiality."
    )


    # ========================================================
    # OVERALL SCORE
    # ========================================================

    weighted_scores = []

    total_weight = 0

    for sdg_number, result in sdg_results.items():

        weight = result["materiality"]

        weighted_scores.append(
            result["score"] * weight
        )

        total_weight += weight

    if total_weight:

        overall_score = round(
            sum(weighted_scores)
            / total_weight
        )

    else:

        overall_score = 0


    st.metric(
        "Overall SDG Research Score",
        f"{overall_score}/100"
    )

    st.caption(
        "This is a research proxy, not an official "
        "company ESG or SDG rating."
    )


    # ========================================================
    # SDG SCORECARDS
    # ========================================================

    st.divider()

    st.subheader(
        "SDG-by-SDG Assessment"
    )

    cols = st.columns(3)

    for i, (
        sdg_number,
        sdg_info
    ) in enumerate(SDGS.items()):

        result = sdg_results[
            sdg_number
        ]

        with cols[i % 3]:

            st.markdown(
                f"### SDG {sdg_number}"
            )

            st.markdown(
                f"**{sdg_info['name']}**"
            )

            st.metric(
                "Research score",
                f"{result['score']}/100"
            )

            st.write(
                f"**Materiality:** "
                f"{result['materiality']}/5"
            )

            st.write(
                f"**Evidence:** "
                f"{result['evidence_count']} "
                f"items"
            )

            st.write(
                f"**Assessment:** "
                f"{result['evidence_type']}"
            )

            if result["evidence"]:

                with st.expander(
                    "View evidence"
                ):

                    for evidence in result[
                        "evidence"
                    ]:

                        st.markdown(
                            f"**Keyword:** "
                            f"{evidence['keyword']}"
                        )

                        st.write(
                            evidence["text"]
                        )

                        st.divider()

            else:

                st.caption(
                    "No relevant public evidence identified."
                )


    # ========================================================
    # DETAILED EVIDENCE TABLE
    # ========================================================

    st.divider()

    st.subheader(
        "Evidence Summary"
    )

    evidence_rows = []

    for sdg_number, result in sdg_results.items():

        if result["evidence"]:

            for evidence in result[
                "evidence"
            ][:3]:

                evidence_rows.append({

                    "SDG": (
                        f"SDG {sdg_number}"
                    ),

                    "SDG Name": SDGS[
                        sdg_number
                    ]["name"],

                    "Evidence Type":
                        result[
                            "evidence_type"
                        ],

                    "Materiality":
                        result[
                            "materiality"
                        ],

                    "Keyword":
                        evidence[
                            "keyword"
                        ],

                    "Evidence":
                        evidence[
                            "text"
                        ][:500]
                })

    if evidence_rows:

        st.dataframe(
            evidence_rows,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No evidence was identified."
        )


    # ========================================================
    # SOURCE INFORMATION
    # ========================================================

    st.divider()

    st.subheader(
        "Internet Sources Collected"
    )

    for item in analysed:

        with st.expander(
            item["title"]
        ):

            st.write(
                f"**Reporting year detected:** "
                f"{item['reporting_year']}"
            )

            st.write(
                item["snippet"]
                or
                "No search snippet available."
            )

            st.link_button(
                "Open source",
                item["url"]
            )


    # ========================================================
    # ANALYST REVIEW
    # ========================================================

    st.divider()

    st.subheader(
        "👩‍💼 Analyst Review"
    )

    st.info(
        "The automated assessment should be reviewed "
        "before the score is used for investment, "
        "client or reporting purposes."
    )

    review_status = st.selectbox(
        "Review status",
        [
            "Not reviewed",
            "Reviewed",
            "Reviewed - requires adjustment"
        ]
    )

    analyst_comment = st.text_area(
        "Analyst comments",
        placeholder=(
            "Add supporting evidence, "
            "adjustments or methodology notes..."
        )
    )

    st.write(
        f"**Review status:** {review_status}"
    )

    if analyst_comment:

        st.write(
            f"**Analyst note:** {analyst_comment}"
        )


    # ========================================================
    # METHODOLOGY
    # ========================================================

    st.divider()

    st.subheader(
        "How Version 2 Works"
    )

    st.markdown(
        """
### 1. Company identification

The user provides the company and its sector.

### 2. Public disclosure collection

The application searches publicly available information
for sustainability, ESG and SDG-related disclosures.

### 3. Evidence extraction

Relevant passages are identified using SDG-specific
evidence terms.

### 4. Sector materiality

Each SDG receives a sector-specific materiality weight.

This means the same evidence can have a different
materiality depending on the company's industry.

### 5. Evidence classification

Evidence is classified into:

- Positive Contribution
- Risk / Exposure
- Negative Impact
- Evidence Identified
- No Evidence

### 6. SDG research score

The prototype combines:

**Evidence + sector materiality + evidence direction**

to produce a research score.

### 7. Analyst review

The analyst can review the evidence and record
comments or adjustments.

The automated score should therefore be treated
as a starting point for research rather than a
final ESG judgement.
"""
    )


# ============================================================
# LANDING PAGE
# ============================================================

else:

    st.info(
        "Enter a company, select its sector and click "
        "**Collect SDG data**."
    )

    st.markdown(
        """
## What Version 2 can do

### 🌍 Analyse all 17 SDGs

The application looks for evidence relevant to
each of the 17 United Nations Sustainable
Development Goals.

### 🏭 Apply sector materiality

Different industries have different sustainability
impacts and opportunities.

The scorecard therefore uses different materiality
weights for different sectors.

### 📊 Identify evidence

The application attempts to identify actual
disclosure evidence rather than simply counting
how often a word appears.

### ↔️ Distinguish impact types

Evidence can be classified as:

- Positive contribution
- Negative impact
- Risk / exposure
- Evidence identified
- No evidence

### 📅 Identify reporting years

The application attempts to identify the year
associated with the information collected.

### 🔎 Maintain source transparency

The underlying webpages are displayed so an analyst
can inspect the source information.

### 👩‍💼 Include analyst review

The final assessment should remain subject to
human review and documented judgement.

---

## Recommended Version 3

For a production ESG / investment workflow, the next
step would be to move away from keyword-based evidence
extraction and build a structured methodology around:

**Company → Sector → SDG → KPI → Metric → Value → Unit → Year → Source → Page → Impact → Score**

This would allow the scorecard to use quantitative
company data rather than relying primarily on text.
"""
    )

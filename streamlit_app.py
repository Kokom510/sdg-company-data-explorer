import re
import io
import time
from datetime import datetime

import requests
import streamlit as st
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urlparse

# Optional PDF library
try:
    from pypdf import PdfReader
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="SDG Company Data Explorer",
    page_icon="🌍",
    layout="wide"
)


# ============================================================
# SDG MASTER LIST
# ============================================================

SDGS = {
    1: "No Poverty",
    2: "Zero Hunger",
    3: "Good Health and Well-being",
    4: "Quality Education",
    5: "Gender Equality",
    6: "Clean Water and Sanitation",
    7: "Affordable and Clean Energy",
    8: "Decent Work and Economic Growth",
    9: "Industry, Innovation and Infrastructure",
    10: "Reduced Inequalities",
    11: "Sustainable Cities and Communities",
    12: "Responsible Consumption and Production",
    13: "Climate Action",
    14: "Life Below Water",
    15: "Life on Land",
    16: "Peace, Justice and Strong Institutions",
    17: "Partnerships for the Goals",
}


# ============================================================
# SDG IDENTIFICATION TERMS
#
# These are used to identify explicit SDG references.
# They are NOT used to score companies.
# ============================================================

SDG_PATTERNS = {
    1: [
        r"\bsd[gS]\s*1\b",
        r"\bgoal\s*1\b",
        r"\bno poverty\b",
    ],
    2: [
        r"\bsd[gG]\s*2\b",
        r"\bgoal\s*2\b",
        r"\bzero hunger\b",
    ],
    3: [
        r"\bsd[gG]\s*3\b",
        r"\bgoal\s*3\b",
        r"\bgood health and well[- ]being\b",
    ],
    4: [
        r"\bsd[gG]\s*4\b",
        r"\bgoal\s*4\b",
        r"\bquality education\b",
    ],
    5: [
        r"\bsd[gG]\s*5\b",
        r"\bgoal\s*5\b",
        r"\bgender equality\b",
    ],
    6: [
        r"\bsd[gG]\s*6\b",
        r"\bgoal\s*6\b",
        r"\bclean water and sanitation\b",
    ],
    7: [
        r"\bsd[gG]\s*7\b",
        r"\bgoal\s*7\b",
        r"\baffordable and clean energy\b",
    ],
    8: [
        r"\bsd[gG]\s*8\b",
        r"\bgoal\s*8\b",
        r"\bdecent work and economic growth\b",
    ],
    9: [
        r"\bsd[gG]\s*9\b",
        r"\bgoal\s*9\b",
        r"\bindustry, innovation and infrastructure\b",
    ],
    10: [
        r"\bsd[gG]\s*10\b",
        r"\bgoal\s*10\b",
        r"\breduced inequalities\b",
    ],
    11: [
        r"\bsd[gG]\s*11\b",
        r"\bgoal\s*11\b",
        r"\bsustainable cities and communities\b",
    ],
    12: [
        r"\bsd[gG]\s*12\b",
        r"\bgoal\s*12\b",
        r"\bresponsible consumption and production\b",
    ],
    13: [
        r"\bsd[gG]\s*13\b",
        r"\bgoal\s*13\b",
        r"\bclimate action\b",
    ],
    14: [
        r"\bsd[gG]\s*14\b",
        r"\bgoal\s*14\b",
        r"\blife below water\b",
    ],
    15: [
        r"\bsd[gG]\s*15\b",
        r"\bgoal\s*15\b",
        r"\blife on land\b",
    ],
    16: [
        r"\bsd[gG]\s*16\b",
        r"\bgoal\s*16\b",
        r"\bpeace, justice and strong institutions\b",
    ],
    17: [
        r"\bsd[gG]\s*17\b",
        r"\bgoal\s*17\b",
        r"\bpartnerships for the goals\b",
    ],
}


# ============================================================
# LANGUAGE THAT INDICATES EXPLICIT COMPANY SUPPORT
#
# This is extremely important.
#
# A report mentioning "SDG 13" is NOT enough.
# We look for language suggesting that the company has
# identified, prioritised, aligned with or reported against it.
# ============================================================

EXPLICIT_PRIORITY_TERMS = [
    "priority sdg",
    "priority sdgs",
    "prioritised sdg",
    "prioritised sdgs",
    "prioritized sdg",
    "prioritized sdgs",
    "our sdgs",
    "our priority",
    "our priorities",
    "focus sdg",
    "focus sdgs",
    "focus areas",
    "key sdgs",
    "relevant sdgs",
    "identified sdgs",
    "selected sdgs",
    "strategic sdgs",
    "aligned with the sdgs",
    "aligned to the sdgs",
    "aligned with sdg",
    "aligned to sdg",
    "support the sdgs",
    "support sdg",
    "contribute to the sdgs",
    "contribute to sdg",
    "contribution to the sdgs",
    "contribution to sdg",
    "commitment to the sdgs",
    "commitment to sdg",
    "mapped to the sdgs",
    "mapped to sdg",
    "linked to the sdgs",
    "linked to sdg",
    "sdg alignment",
    "sdg contribution",
    "sustainable development goals",
]


# ============================================================
# TARGET TERMS
# ============================================================

TARGET_TERMS = [
    "target",
    "targets",
    "commitment",
    "commitments",
    "ambition",
    "ambitions",
    "goal",
    "goals",
    "by 2025",
    "by 2026",
    "by 2027",
    "by 2028",
    "by 2029",
    "by 2030",
    "by 2035",
    "by 2040",
    "by 2050",
    "net zero",
    "reduce",
    "reduction",
    "increase",
    "achieve",
    "achieving",
    "reach",
    "reaching",
    "maintain",
    "eliminate",
]


# ============================================================
# HTTP SESSION
# ============================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/150 Safari/537.36 "
        "SDG-Company-Data-Explorer/3.0"
    )
}


# ============================================================
# HELPERS
# ============================================================

def clean_text(text):
    """Clean excessive whitespace."""
    if not text:
        return ""

    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalise_company(company):
    """Basic company-name cleaning."""
    company = company.strip()
    company = re.sub(
        r"\b(limited|ltd|plc|inc|incorporated|corp|corporation)\b",
        "",
        company,
        flags=re.IGNORECASE
    )
    return clean_text(company)


def is_pdf_url(url):
    return ".pdf" in url.lower()


def get_domain(url):
    try:
        return urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return ""


def looks_like_company_domain(url, company):
    """
    Heuristic only.

    We don't assume that every search result is official.
    """
    domain = get_domain(url)

    if not domain:
        return False

    company_words = re.findall(
        r"[a-z0-9]+",
        normalise_company(company).lower()
    )

    if not company_words:
        return False

    return any(
        word in domain
        for word in company_words
        if len(word) > 3
    )


# ============================================================
# SEARCH
# ============================================================

@st.cache_data(ttl=3600, show_spinner=False)
def search_web(query, max_results=8):
    """
    Search DuckDuckGo.

    Cached for 1 hour so repeated searches are faster.
    """

    endpoints = [
        "https://html.duckduckgo.com/html/",
        "https://lite.duckduckgo.com/lite/",
    ]

    last_error = None

    for endpoint in endpoints:

        try:
            response = requests.get(
                endpoint,
                params={"q": query},
                headers=HEADERS,
                timeout=8
            )

            response.raise_for_status()

            soup = BeautifulSoup(
                response.text,
                "html.parser"
            )

            results = []

            # Standard DuckDuckGo results
            selectors = [
                ".result",
                ".result-link",
                ".result__body"
            ]

            found = []

            for selector in selectors:
                found = soup.select(selector)
                if found:
                    break

            for item in found:

                link = (
                    item.select_one(".result__a")
                    or item.select_one("a.result-link")
                    or item.select_one("a")
                )

                if not link:
                    continue

                url = link.get("href", "")

                title = clean_text(
                    link.get_text(" ", strip=True)
                )

                snippet_element = (
                    item.select_one(".result__snippet")
                    or item.select_one(".result-snippet")
                )

                snippet = (
                    clean_text(
                        snippet_element.get_text(
                            " ",
                            strip=True
                        )
                    )
                    if snippet_element
                    else ""
                )

                if url and title:

                    results.append({
                        "title": title,
                        "url": url,
                        "snippet": snippet
                    })

            if results:
                return results[:max_results]

        except Exception as e:
            last_error = e

    return []


# ============================================================
# FIND LATEST COMPANY REPORTS
# ============================================================

def find_latest_reports(company, max_results=8):

    current_year = datetime.now().year

    queries = [
        f'"{company}" sustainability report {current_year} PDF',
        f'"{company}" ESG report {current_year} PDF',
        f'"{company}" integrated report {current_year} PDF',
        f'"{company}" sustainability report {current_year - 1} PDF',
        f'"{company}" ESG report {current_year - 1} PDF',
        f'"{company}" SDG report PDF',
    ]

    all_results = []
    seen_urls = set()

    for query in queries:

        results = search_web(
            query,
            max_results=5
        )

        for result in results:

            url = result["url"]

            if not url:
                continue

            if url in seen_urls:
                continue

            seen_urls.add(url)

            title_lower = result["title"].lower()

            relevance = 0

            if "sustainability" in title_lower:
                relevance += 5

            if "esg" in title_lower:
                relevance += 5

            if "integrated report" in title_lower:
                relevance += 4

            if "annual report" in title_lower:
                relevance += 2

            if is_pdf_url(url):
                relevance += 5

            if looks_like_company_domain(url, company):
                relevance += 8

            year_match = re.search(
                r"\b(20\d{2})\b",
                result["title"]
            )

            year = (
                int(year_match.group(1))
                if year_match
                else 0
            )

            result["relevance"] = relevance
            result["year"] = year

            all_results.append(result)

    # Highest relevance first, then latest year
    all_results.sort(
        key=lambda x: (
            x["relevance"],
            x["year"]
        ),
        reverse=True
    )

    return all_results[:max_results]


# ============================================================
# DOWNLOAD PDF
# ============================================================

@st.cache_data(
    ttl=86400,
    show_spinner=False,
    max_entries=50
)
def download_pdf(url):

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=15
        )

        response.raise_for_status()

        content_type = response.headers.get(
            "Content-Type",
            ""
        ).lower()

        # Accept PDF URL even if server doesn't return
        # a perfect content-type.
        if (
            "pdf" not in content_type
            and not is_pdf_url(url)
        ):
            return None

        return response.content

    except Exception:
        return None


# ============================================================
# EXTRACT PDF TEXT
# ============================================================

def extract_pdf_pages(pdf_bytes):

    if not PDF_AVAILABLE:
        return []

    if not pdf_bytes:
        return []

    try:

        reader = PdfReader(
            io.BytesIO(pdf_bytes)
        )

        pages = []

        for page_number, page in enumerate(
            reader.pages,
            start=1
        ):

            try:
                text = page.extract_text() or ""
            except Exception:
                text = ""

            text = clean_text(text)

            if text:
                pages.append({
                    "page": page_number,
                    "text": text
                })

        return pages

    except Exception:
        return []


# ============================================================
# HTML FALLBACK
# ============================================================

@st.cache_data(
    ttl=86400,
    show_spinner=False,
    max_entries=50
)
def fetch_html(url):

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=10
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

        return [{
            "page": None,
            "text": clean_text(text)
        }]

    except Exception:
        return []


# ============================================================
# GET DOCUMENT PAGES
# ============================================================

def get_document_pages(url):

    if is_pdf_url(url):

        pdf_bytes = download_pdf(url)

        if pdf_bytes:
            return extract_pdf_pages(
                pdf_bytes
            )

    return fetch_html(url)


# ============================================================
# SDG DETECTION
# ============================================================

def detect_sdgs_in_text(text):

    detected = []

    text_lower = text.lower()

    for sdg_number, patterns in SDG_PATTERNS.items():

        for pattern in patterns:

            if re.search(
                pattern,
                text_lower,
                flags=re.IGNORECASE
            ):
                detected.append(sdg_number)
                break

    return sorted(set(detected))


# ============================================================
# SENTENCE SPLITTING
# ============================================================

def split_sentences(text):

    text = clean_text(text)

    # Basic sentence splitter suitable for report extraction.
    sentences = re.split(
        r"(?<=[.!?])\s+",
        text
    )

    return [
        sentence.strip()
        for sentence in sentences
        if len(sentence.strip()) > 20
    ]


# ============================================================
# EXPLICIT SDG PRIORITY CHECK
# ============================================================

def sentence_has_priority_language(sentence):

    sentence_lower = sentence.lower()

    return any(
        term in sentence_lower
        for term in EXPLICIT_PRIORITY_TERMS
    )


def get_sdg_evidence(
    pages,
    sdg_number
):

    evidence = []

    patterns = SDG_PATTERNS[
        sdg_number
    ]

    for page_data in pages:

        page_number = page_data["page"]
        text = page_data["text"]

        sentences = split_sentences(text)

        for sentence in sentences:

            sdg_match = any(
                re.search(
                    pattern,
                    sentence,
                    flags=re.IGNORECASE
                )
                for pattern in patterns
            )

            if not sdg_match:
                continue

            # Strong evidence:
            # SDG reference + priority/support language
            if sentence_has_priority_language(
                sentence
            ):

                evidence.append({
                    "page": page_number,
                    "text": sentence,
                    "confidence": "High"
                })

            else:

                # Keep weaker evidence separate.
                evidence.append({
                    "page": page_number,
                    "text": sentence,
                    "confidence": "Medium"
                })

    return evidence


# ============================================================
# TARGET EXTRACTION
# ============================================================

def looks_like_target(sentence):

    lower = sentence.lower()

    has_target_language = any(
        term in lower
        for term in TARGET_TERMS
    )

    # Quantitative target patterns
    has_percentage = bool(
        re.search(
            r"\b\d{1,3}(?:\.\d+)?\s?%",
            sentence
        )
    )

    has_year = bool(
        re.search(
            r"\b20[2-5]\d\b",
            sentence
        )
    )

    has_number = bool(
        re.search(
            r"\b\d+(?:\.\d+)?\b",
            sentence
        )
    )

    return (
        has_target_language
        and (
            has_percentage
            or has_year
            or has_number
        )
    )


def extract_targets_near_sdg(
    pages,
    sdg_number
):

    targets = []

    patterns = SDG_PATTERNS[
        sdg_number
    ]

    for page_data in pages:

        page_number = page_data["page"]
        text = page_data["text"]

        sentences = split_sentences(text)

        for i, sentence in enumerate(
            sentences
        ):

            sdg_match = any(
                re.search(
                    pattern,
                    sentence,
                    flags=re.IGNORECASE
                )
                for pattern in patterns
            )

            if not sdg_match:
                continue

            # Look at this sentence and the next
            # two sentences.
            nearby = sentences[
                i:min(i + 3, len(sentences))
            ]

            for candidate in nearby:

                if not looks_like_target(
                    candidate
                ):
                    continue

                targets.append({
                    "page": page_number,
                    "text": candidate
                })

    # Remove duplicates
    unique = []
    seen = set()

    for target in targets:

        key = target["text"].lower()

        if key in seen:
            continue

        seen.add(key)
        unique.append(target)

    return unique[:10]


# ============================================================
# TARGET YEAR
# ============================================================

def extract_target_year(text):

    years = re.findall(
        r"\b20(?:2[5-9]|3\d|4\d|50)\b",
        text
    )

    if not years:
        return ""

    # Prefer the latest target year mentioned.
    return max(
        years,
        key=int
    )


# ============================================================
# QUANTITATIVE TARGET
# ============================================================

def extract_quantitative_target(text):

    patterns = [

        # Percentage
        r"\b\d{1,3}(?:\.\d+)?\s?%",

        # Numbers with common units
        r"\b\d+(?:\.\d+)?\s?(?:tCO2e|tCO₂e|tonnes|tons|MW|GW|MWh|GWh|kWh|kg|litres|liters)\b",

        # Net zero year
        r"\bnet zero\b.*?\b20\d{2}\b",

        # Carbon neutral
        r"\bcarbon neutral\b.*?\b20\d{2}\b",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        if match:
            return clean_text(
                match.group(0)
            )

    return ""


# ============================================================
# BUILD SDG PROFILE
# ============================================================

def build_sdg_profile(
    company,
    report,
    pages
):

    profile = []

    for sdg_number in SDGS:

        evidence = get_sdg_evidence(
            pages,
            sdg_number
        )

        if not evidence:
            continue

        # We only regard the SDG as a company-supported
        # SDG when strong explicit language exists.
        high_confidence = [
            e for e in evidence
            if e["confidence"] == "High"
        ]

        if not high_confidence:
            continue

        targets = extract_targets_near_sdg(
            pages,
            sdg_number
        )

        target_text = ""

        if targets:
            target_text = targets[0]["text"]

        combined_target_text = " ".join(
            t["text"]
            for t in targets
        )

        target_year = (
            extract_target_year(
                combined_target_text
            )
            if combined_target_text
            else ""
        )

        quantitative_target = (
            extract_quantitative_target(
                combined_target_text
            )
            if combined_target_text
            else ""
        )

        best_evidence = high_confidence[0]

        profile.append({

            "Company": company,

            "SDG": f"SDG {sdg_number}",

            "SDG Name": SDGS[
                sdg_number
            ],

            "Company SDG Priority": "Explicitly identified",

            "Evidence Confidence": "High",

            "Target / Commitment": target_text,

            "Target Year": target_year,

            "Quantitative Target": quantitative_target,

            "Source": report["url"],

            "Report Name": report["title"],

            "Reporting Year": report.get(
                "year",
                ""
            ),

            "Page Reference": best_evidence[
                "page"
            ],

            "Evidence": best_evidence[
                "text"
            ],

            "Analyst Review": "Required",

            "Analyst Comment": "",
        })

    return profile


# ============================================================
# FIND BEST REPORT
# ============================================================

def select_best_report(
    company,
    reports
):

    if not reports:
        return None

    current_year = datetime.now().year

    scored = []

    for report in reports:

        score = report.get(
            "relevance",
            0
        )

        title = report[
            "title"
        ].lower()

        url = report[
            "url"
        ]

        year = report.get(
            "year",
            0
        )

        # Strong preference for official-looking source
        if looks_like_company_domain(
            url,
            company
        ):
            score += 20

        # Prefer PDFs
        if is_pdf_url(url):
            score += 10

        # Prefer sustainability/ESG reports
        if "sustainability" in title:
            score += 10

        if "esg" in title:
            score += 8

        if "integrated report" in title:
            score += 6

        # Prefer latest available year,
        # but don't require current year.
        if year:
            year_distance = max(
                0,
                current_year - year
            )

            score += max(
                0,
                15 - year_distance * 3
            )

        report_copy = dict(report)
        report_copy[
            "final_score"
        ] = score

        scored.append(
            report_copy
        )

    scored.sort(
        key=lambda x: (
            x["final_score"],
            x.get("year", 0)
        ),
        reverse=True
    )

    return scored[0]


# ============================================================
# MAIN COLLECTION FUNCTION
# ============================================================

@st.cache_data(
    ttl=3600,
    show_spinner=False
)
def collect_company_data(company):

    company = normalise_company(
        company
    )

    reports = find_latest_reports(
        company,
        max_results=8
    )

    if not reports:
        return {
            "reports": [],
            "selected_report": None,
            "profile": [],
            "error": "No reports found."
        }

    selected_report = select_best_report(
        company,
        reports
    )

    if not selected_report:
        return {
            "reports": reports,
            "selected_report": None,
            "profile": [],
            "error": "Could not select a report."
        }

    pages = get_document_pages(
        selected_report["url"]
    )

    if not pages:
        return {
            "reports": reports,
            "selected_report": selected_report,
            "profile": [],
            "error": (
                "The report was found but its contents "
                "could not be extracted."
            )
        }

    profile = build_sdg_profile(
        company,
        selected_report,
        pages
    )

    return {
        "reports": reports,
        "selected_report": selected_report,
        "profile": profile,
        "error": ""
    }


# ============================================================
# UI
# ============================================================

st.title(
    "🌍 SDG Company Data Explorer — Version 3"
)

st.caption(
    "Find the latest company sustainability reporting "
    "and extract only the SDGs the company explicitly identifies "
    "together with associated targets."
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

    run = st.button(
        "Find latest SDG data",
        type="primary",
        use_container_width=True
    )

    st.divider()

    st.subheader(
        "Optional report URL"
    )

    manual_url = st.text_input(
        "Paste official sustainability report URL",
        placeholder="https://company.com/report.pdf"
    )

    st.divider()

    st.markdown(
        """
### Methodology

The app does **not** score all 17 SDGs.

An SDG is returned only when the company appears to
explicitly identify, prioritise, align with or report against it.

The extracted target must then be reviewed by an analyst
before being used for investment, reporting or client purposes.
"""
    )


# ============================================================
# MAIN ACTION
# ============================================================

if run:

    if not company.strip():

        st.error(
            "Please enter a company name."
        )

        st.stop()

    if not PDF_AVAILABLE:

        st.warning(
            "PDF support is not installed. "
            "Install pypdf using: pip install pypdf"
        )

    with st.spinner(
        "Finding the latest sustainability report..."
    ):

        if manual_url.strip():

            selected_report = {
                "title": "Manually supplied report",
                "url": manual_url.strip(),
                "year": "",
                "relevance": 100,
            }

            pages = get_document_pages(
                manual_url.strip()
            )

            profile = build_sdg_profile(
                company,
                selected_report,
                pages
            )

            result = {
                "reports": [
                    selected_report
                ],
                "selected_report":
                    selected_report,
                "profile":
                    profile,
                "error": ""
            }

        else:

            result = collect_company_data(
                company
            )


    # ========================================================
    # ERROR
    # ========================================================

    if result.get("error"):

        st.warning(
            result["error"]
        )

        if result.get(
            "selected_report"
        ):

            report = result[
                "selected_report"
            ]

            st.markdown(
                f"**Report found:** "
                f"{report['title']}"
            )

            st.link_button(
                "Open report",
                report["url"]
            )

        st.stop()


    selected_report = result[
        "selected_report"
    ]

    profile = result[
        "profile"
    ]


    # ========================================================
    # REPORT FOUND
    # ========================================================

    st.success(
        "Latest relevant company report found."
    )

    st.subheader(
        "Source report"
    )

    report_col1, report_col2 = st.columns(
        [4, 1]
    )

    with report_col1:

        st.markdown(
            f"**{selected_report['title']}**"
        )

        st.caption(
            selected_report["url"]
        )

    with report_col2:

        st.link_button(
            "Open report",
            selected_report["url"]
        )


    # ========================================================
    # NO EXPLICIT SDGs
    # ========================================================

    if not profile:

        st.warning(
            "No SDGs were identified as explicitly supported "
            "or prioritised in the extracted report evidence."
        )

        st.info(
            "The app deliberately does not infer SDG support "
            "from general ESG topics or keyword mentions."
        )

        st.stop()


    # ========================================================
    # SUMMARY
    # ========================================================

    st.divider()

    st.subheader(
        f"Explicitly identified SDGs — {company}"
    )

    st.metric(
        "SDGs identified",
        len(profile)
    )


    # ========================================================
    # SDG CARDS
    # ========================================================

    for item in profile:

        with st.container(
            border=True
        ):

            left, right = st.columns(
                [1, 3]
            )

            with left:

                st.markdown(
                    f"### {item['SDG']}"
                )

                st.markdown(
                    f"**{item['SDG Name']}**"
                )

                st.success(
                    "Explicit company identification"
                )

            with right:

                st.markdown(
                    "**Target / Commitment**"
                )

                if item[
                    "Target / Commitment"
                ]:

                    st.write(
                        item[
                            "Target / Commitment"
                        ]
                    )

                else:

                    st.write(
                        "No specific target extracted."
                    )

                target_col1, target_col2 = st.columns(
                    2
                )

                with target_col1:

                    st.markdown(
                        "**Target year**"
                    )

                    st.write(
                        item[
                            "Target Year"
                        ]
                        or "Not identified"
                    )

                with target_col2:

                    st.markdown(
                        "**Quantitative target**"
                    )

                    st.write(
                        item[
                            "Quantitative Target"
                        ]
                        or "Not identified"
                    )

            st.markdown(
                "**Evidence from report**"
            )

            st.info(
                item["Evidence"]
            )

            st.caption(
                f"Page: {item['Page Reference']} | "
                f"Confidence: {item['Evidence Confidence']}"
            )

            st.link_button(
                "Open source report",
                item["Source"]
            )


    # ========================================================
    # DATA TABLE
    # ========================================================

    st.divider()

    st.subheader(
        "Export-ready SDG dataset"
    )

    try:

        import pandas as pd

        df = pd.DataFrame(
            profile
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        csv = df.to_csv(
            index=False
        ).encode(
            "utf-8"
        )

        st.download_button(
            "Download SDG data as CSV",
            csv,
            file_name=(
                f"{normalise_company(company)}"
                "_SDG_Data.csv"
            ),
            mime="text/csv"
        )

    except Exception as e:

        st.error(
            f"Could not create export table: {e}"
        )


    # ========================================================
    # REPORTS DISCOVERED
    # ========================================================

    with st.expander(
        "Other reports discovered"
    ):

        for report in result[
            "reports"
        ]:

            st.markdown(
                f"**{report['title']}**"
            )

            st.caption(
                f"Year: {report.get('year', 'Unknown')} | "
                f"Relevance: {report.get('relevance', 0)}"
            )

            st.link_button(
                "Open",
                report["url"]
            )


# ============================================================
# LANDING PAGE
# ============================================================

else:

    st.info(
        "Enter a company and click "
        "**Find latest SDG data**."
    )

    st.markdown(
        """
## How Version 3 works

### 1. Find the latest report

The app searches for:

- Sustainability Reports
- ESG Reports
- Integrated Reports
- SDG-related company reports

It prioritises recent reports and company-domain sources.

### 2. Extract the report

Where the source is a PDF, the app extracts the report text
page by page so that the source page can be retained.

### 3. Identify explicit SDGs

The app looks for language such as:

- Priority SDGs
- Our SDGs
- Focus SDGs
- Key SDGs
- Identified SDGs
- Aligned with the SDGs
- Contribution to the SDGs
- SDG alignment

### 4. Extract targets

The app then looks for targets associated with those SDGs,
including:

- Percentage targets
- Reduction targets
- Increase targets
- Net-zero commitments
- Target years
- Quantitative KPIs

### 5. Return only company-supported SDGs

If a report mentions SDG 13 in passing but does not indicate
that the company identifies or supports it, the SDG is **not
returned as a supported SDG**.

This is deliberately different from a keyword-based SDG score.

### 6. Analyst validation

Every extracted result includes:

**Company → SDG → Target → Target Year → Evidence → Page → Source**

The analyst can then validate the disclosure before it is
used in an ESG or investment workflow.
"""
    )

    st.divider()

    st.markdown(
      
### Required packages




import re
import requests
import streamlit as st
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urlparse
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
    17: "Partnerships for the Goals"
}


# ============================================================
# SDG IDENTIFICATION TERMS
#
# These are used to FIND possible SDG references.
# They do NOT automatically mean that a company supports
# the SDG.
# ============================================================

SDG_TERMS = {

    1: [
        "SDG 1",
        "SDG1",
        "No Poverty",
        "poverty",
        "financial inclusion"
    ],

    2: [
        "SDG 2",
        "SDG2",
        "Zero Hunger",
        "food security",
        "nutrition"
    ],

    3: [
        "SDG 3",
        "SDG3",
        "Good Health and Well-being",
        "health and wellbeing",
        "occupational health"
    ],

    4: [
        "SDG 4",
        "SDG4",
        "Quality Education",
        "education",
        "skills development"
    ],

    5: [
        "SDG 5",
        "SDG5",
        "Gender Equality",
        "gender equality",
        "women empowerment"
    ],

    6: [
        "SDG 6",
        "SDG6",
        "Clean Water and Sanitation",
        "water security",
        "water management"
    ],

    7: [
        "SDG 7",
        "SDG7",
        "Affordable and Clean Energy",
        "clean energy",
        "renewable energy"
    ],

    8: [
        "SDG 8",
        "SDG8",
        "Decent Work and Economic Growth",
        "decent work",
        "employment"
    ],

    9: [
        "SDG 9",
        "SDG9",
        "Industry, Innovation and Infrastructure",
        "innovation",
        "infrastructure"
    ],

    10: [
        "SDG 10",
        "SDG10",
        "Reduced Inequalities",
        "inequality",
        "economic inclusion"
    ],

    11: [
        "SDG 11",
        "SDG11",
        "Sustainable Cities and Communities",
        "sustainable cities",
        "affordable housing"
    ],

    12: [
        "SDG 12",
        "SDG12",
        "Responsible Consumption and Production",
        "circular economy",
        "responsible consumption"
    ],

    13: [
        "SDG 13",
        "SDG13",
        "Climate Action",
        "climate action",
        "net zero",
        "carbon emissions"
    ],

    14: [
        "SDG 14",
        "SDG14",
        "Life Below Water",
        "marine",
        "ocean"
    ],

    15: [
        "SDG 15",
        "SDG15",
        "Life on Land",
        "biodiversity",
        "nature"
    ],

    16: [
        "SDG 16",
        "SDG16",
        "Peace, Justice and Strong Institutions",
        "governance",
        "anti-corruption"
    ],

    17: [
        "SDG 17",
        "SDG17",
        "Partnerships for the Goals",
        "partnerships",
        "sustainable development partnerships"
    ]
}


# ============================================================
# REPORT TYPES
# ============================================================

REPORT_TYPES = [
    "Sustainability Report",
    "ESG Report",
    "Integrated Report",
    "Annual Report",
    "Climate Report",
    "Society Report",
    "Sustainability Data Report",
    "ESG Data Book",
    "Sustainable Development Report"
]


# ============================================================
# SEARCH FUNCTION
# ============================================================

def search_web(query, max_results=10):

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

                for item in soup.select(".result")[:max_results]:

                    link = item.select_one(".result__a")
                    snippet = item.select_one(
                        ".result__snippet"
                    )

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
        "Web search failed. " + str(last_error)
    )


# ============================================================
# FIND CURRENT COMPANY REPORTS
# ============================================================

def find_company_reports(company, max_results=12):

    current_year = datetime.now().year

    queries = [

        f'"{company}" sustainability report {current_year}',

        f'"{company}" ESG report {current_year}',

        f'"{company}" integrated report {current_year}',

        f'"{company}" annual report {current_year}',

        f'"{company}" sustainability SDG report',

        f'"{company}" sustainability targets ESG'

    ]

    all_results = []

    seen_urls = set()

    for query in queries:

        try:

            results = search_web(
                query,
                max_results=6
            )

            for result in results:

                url = result["url"]

                if url not in seen_urls:

                    seen_urls.add(url)

                    all_results.append(result)

        except Exception:
            continue

        if len(all_results) >= max_results:
            break

    return all_results[:max_results]


# ============================================================
# FETCH PAGE
# ============================================================

def fetch_page(url):

    try:

        response = requests.get(
            url,
            headers={
                "User-Agent":
                "Mozilla/5.0 SDG Company Scorecard/2.0"
            },
            timeout=30
        )

        response.raise_for_status()

        content_type = response.headers.get(
            "Content-Type",
            ""
        ).lower()

        # HTML page
        if "text/html" in content_type:

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

            return text[:250000]

        # PDF or other document
        return ""

    except Exception:

        return ""


# ============================================================
# DETECT REPORT YEAR
# ============================================================

def detect_report_year(text):

    if not text:
        return "Unknown"

    current_year = datetime.now().year

    years = re.findall(
        r"\b(20[1-2][0-9])\b",
        text
    )

    valid_years = [
        int(year)
        for year in years
        if int(year) <= current_year
    ]

    if not valid_years:
        return "Unknown"

    # Prefer the most recent year
    return str(max(valid_years))


# ============================================================
# IDENTIFY REPORT TYPE
# ============================================================

def identify_report_type(title, text):

    combined = (
        title + " " + text[:10000]
    ).lower()

    for report_type in REPORT_TYPES:

        if report_type.lower() in combined:

            return report_type

    return "Company disclosure"


# ============================================================
# EXTRACT EXPLICIT SDG REFERENCES
# ============================================================

def extract_explicit_sdgs(text):

    if not text:
        return {}

    results = {}

    # --------------------------------------------------------
    # First look for explicit "SDG X" references.
    # --------------------------------------------------------

    explicit_matches = re.findall(
        r"\bSDG\s*([1-9]|1[0-7])\b",
        text,
        flags=re.IGNORECASE
    )

    for number in explicit_matches:

        sdg = int(number)

        results.setdefault(
            sdg,
            {
                "confidence": "High",
                "evidence": []
            }
        )

    # --------------------------------------------------------
    # Look for official SDG names close to commitment language.
    # --------------------------------------------------------

    lower_text = text.lower()

    commitment_terms = [
        "prioritise",
        "prioritize",
        "priority",
        "focus",
        "aligned with",
        "support",
        "supports",
        "contribute",
        "contribution",
        "commitment",
        "committed to",
        "target",
        "targets",
        "our sdg",
        "our sustainable development goals",
        "material sdg"
    ]

    for sdg, terms in SDG_TERMS.items():

        for term in terms:

            start_position = 0

            while True:

                position = lower_text.find(
                    term.lower(),
                    start_position
                )

                if position == -1:
                    break

                start = max(
                    0,
                    position - 350
                )

                end = min(
                    len(text),
                    position + 500
                )

                passage = text[
                    start:end
                ].strip()

                passage_lower = passage.lower()

                has_commitment_language = any(
                    commitment in passage_lower
                    for commitment in commitment_terms
                )

                if has_commitment_language:

                    results.setdefault(
                        sdg,
                        {
                            "confidence": "Medium",
                            "evidence": []
                        }
                    )

                    if passage not in results[
                        sdg
                    ]["evidence"]:

                        results[
                            sdg
                        ]["evidence"].append(
                            passage
                        )

                start_position = (
                    position + len(term)
                )

    return results


# ============================================================
# EXTRACT TARGETS
# ============================================================

def extract_targets(text, sdg_number):

    if not text:
        return []

    terms = SDG_TERMS[
        sdg_number
    ]

    target_indicators = [
        "target",
        "targets",
        "commit",
        "committed",
        "aim",
        "aims",
        "goal",
        "by 2030",
        "by 2050",
        "by 2025",
        "by 2026",
        "by 2027",
        "by 2028",
        "by 2029",
        "by 2030",
        "reduce",
        "increase",
        "reach",
        "achieve",
        "achieve",
        "net zero"
    ]

    lower_text = text.lower()

    targets = []

    for term in terms:

        positions = [
            match.start()
            for match in re.finditer(
                re.escape(term.lower()),
                lower_text
            )
        ]

        for position in positions[:20]:

            start = max(
                0,
                position - 500
            )

            end = min(
                len(text),
                position + 900
            )

            passage = text[
                start:end
            ].strip()

            passage_lower = passage.lower()

            # Only keep passages that look like
            # actual target/commitment statements.
            if any(
                indicator in passage_lower
                for indicator in target_indicators
            ):

                # Clean excessive whitespace
                passage = re.sub(
                    r"\s+",
                    " ",
                    passage
                )

                if passage not in targets:

                    targets.append(
                        passage
                    )

    return targets[:8]


# ============================================================
# EXTRACT TARGET YEAR
# ============================================================

def extract_target_year(text):

    if not text:
        return "Not identified"

    years = re.findall(
        r"\b20[2-9][0-9]\b",
        text
    )

    if not years:
        return "Not identified"

    # Return years that are likely future/target years
    unique_years = sorted(
        set(years)
    )

    return ", ".join(
        unique_years[:5]
    )


# ============================================================
# EXTRACT QUANTITATIVE TARGET
# ============================================================

def extract_quantitative_target(text):

    if not text:
        return "Not identified"

    patterns = [

        # Percentages
        r"\b\d+(?:\.\d+)?\s*%",

        # Monetary values
        r"\b(?:R|£|\$|€)\s?\d+(?:[.,]\d+)?\s*(?:bn|billion|m|million)?",

        # Numbers followed by units
        r"\b\d+(?:[.,]\d+)?\s*(?:tonnes|tons|tCO2e|MW|GW|GWh|MWh|employees|people|jobs)\b"
    ]

    matches = []

    for pattern in patterns:

        found = re.findall(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        matches.extend(found)

    if not matches:
        return "Not identified"

    return ", ".join(
        list(dict.fromkeys(matches))[:10]
    )


# ============================================================
# BUILD COMPANY SDG PROFILE
# ============================================================

def build_sdg_profile(
    company,
    reports
):

    profile = {}

    for report in reports:

        text = report.get(
            "page_text",
            ""
        )

        if not text:
            continue

        explicit_sdgs = extract_explicit_sdgs(
            text
        )

        for sdg_number, data in explicit_sdgs.items():

            if sdg_number not in profile:

                profile[sdg_number] = {
                    "sdg": sdg_number,
                    "name": SDGS[
                        sdg_number
                    ],
                    "confidence":
                        data["confidence"],
                    "evidence": [],
                    "targets": [],
                    "target_year":
                        "Not identified",
                    "quantitative_target":
                        "Not identified",
                    "sources": []
                }

            # Evidence
            for evidence in data[
                "evidence"
            ]:

                if evidence not in profile[
                    sdg_number
                ]["evidence"]:

                    profile[
                        sdg_number
                    ]["evidence"].append(
                        evidence
                    )

            # Targets
            targets = extract_targets(
                text,
                sdg_number
            )

            for target in targets:

                if target not in profile[
                    sdg_number
                ]["targets"]:

                    profile[
                        sdg_number
                    ]["targets"].append(
                        target
                    )

            # Target year
            target_year = extract_target_year(
                " ".join(
                    profile[
                        sdg_number
                    ]["targets"]
                )
            )

            if target_year != "Not identified":

                profile[
                    sdg_number
                ]["target_year"] = target_year

            # Quantitative target
            quantitative_target = (
                extract_quantitative_target(
                    " ".join(
                        profile[
                            sdg_number
                        ]["targets"]
                    )
                )
            )

            if (
                quantitative_target
                != "Not identified"
            ):

                profile[
                    sdg_number
                ]["quantitative_target"] = (
                    quantitative_target
                )

            # Source
            source = {
                "title":
                    report["title"],

                "url":
                    report["url"],

                "year":
                    report[
                        "reporting_year"
                    ],

                "report_type":
                    report[
                        "report_type"
                    ]
            }

            if source not in profile[
                sdg_number
            ]["sources"]:

                profile[
                    sdg_number
                ]["sources"].append(
                    source
                )

    return profile


# ============================================================
# HEADER
# ============================================================

st.title(
    "🌍 SDG Company Scorecard"
)

st.caption(
    "Version 2 — identifies the SDGs a company "
    "explicitly prioritises and extracts its disclosed targets."
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header(
        "Company"
    )

    company = st.text_input(
        "Company name",
        "Nedbank"
    )

    max_reports = st.slider(
        "Reports / sources to collect",
        4,
        15,
        10
    )

    run = st.button(
        "Research company",
        type="primary"
    )

    st.divider()

    st.markdown(
        """
        ### Methodology

        The application:

        1. Searches for current company reports.
        2. Identifies explicit SDG references.
        3. Looks for company commitments.
        4. Extracts targets.
        5. Identifies target years.
        6. Shows the original source.

        An SDG is **not** treated as a company priority
        simply because an unrelated keyword appears.
        """
    )


# ============================================================
# RUN
# ============================================================

if run:

    if not company.strip():

        st.warning(
            "Please enter a company name."
        )

        st.stop()

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    with st.spinner(
        "Searching for the company's latest sustainability and ESG reports..."
    ):

        try:

            report_results = find_company_reports(
                company,
                max_reports
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

    if not report_results:

        st.warning(
            "No company reports were found."
        )

        st.stop()


    # --------------------------------------------------------
    # FETCH REPORTS
    # --------------------------------------------------------

    analysed_reports = []

    progress = st.progress(0)

    for i, result in enumerate(
        report_results
    ):

        text = fetch_page(
            result["url"]
        )

        if text:

            analysed_reports.append({

                **result,

                "page_text": text,

                "reporting_year":
                    detect_report_year(
                        text
                    ),

                "report_type":
                    identify_report_type(
                        result["title"],
                        text
                    )
            })

        progress.progress(
            (i + 1)
            / len(report_results)
        )

    progress.empty()


    # --------------------------------------------------------
    # BUILD SDG PROFILE
    # --------------------------------------------------------

    with st.spinner(
        "Identifying explicitly prioritised SDGs and extracting targets..."
    ):

        profile = build_sdg_profile(
            company,
            analysed_reports
        )


    # ========================================================
    # COMPANY SUMMARY
    # ========================================================

    st.subheader(
        f"{company} — SDG Profile"
    )

    st.write(
        "The profile below contains only SDGs for which "
        "the available company disclosures contain an "
        "explicit SDG reference or commitment-related "
        "evidence."
    )

    st.metric(
        "Explicitly identified SDGs",
        len(profile)
    )


    # ========================================================
    # NO SDGS FOUND
    # ========================================================

    if not profile:

        st.warning(
            "No explicit company SDG priorities could be "
            "identified from the sources collected."
        )

        st.info(
            "This does not mean the company has no SDG "
            "activities. It means the available webpages "
            "did not provide sufficiently explicit evidence."
        )

    else:

        # ====================================================
        # SDG TABLE
        # ====================================================

        st.divider()

        st.subheader(
            "Company-identified SDGs"
        )

        table_rows = []

        for sdg_number in sorted(
            profile.keys()
        ):

            item = profile[
                sdg_number
            ]

            table_rows.append({

                "SDG":
                    f"SDG {sdg_number}",

                "SDG Name":
                    item["name"],

                "Evidence confidence":
                    item["confidence"],

                "Targets identified":
                    len(
                        item["targets"]
                    ),

                "Target year":
                    item["target_year"],

                "Quantitative target":
                    item[
                        "quantitative_target"
                    ]
            })

        st.dataframe(
            table_rows,
            use_container_width=True,
            hide_index=True
        )


        # ====================================================
        # DETAILED SDG INFORMATION
        # ====================================================

        st.divider()

        st.subheader(
            "SDG Targets and Commitments"
        )

        for sdg_number in sorted(
            profile.keys()
        ):

            item = profile[
                sdg_number
            ]

            with st.expander(
                f"SDG {sdg_number} — {item['name']}",
                expanded=True
            ):

                st.markdown(
                    f"### SDG {sdg_number}: "
                    f"{item['name']}"
                )

                st.write(
                    f"**Evidence confidence:** "
                    f"{item['confidence']}"
                )

                # ------------------------------------------------
                # TARGETS
                # ------------------------------------------------

                st.markdown(
                    "#### 🎯 Targets / Commitments"
                )

                if item["targets"]:

                    for target in item[
                        "targets"
                    ]:

                        st.markdown(
                            f"- {target}"
                        )

                else:

                    st.info(
                        "No specific target was identified "
                        "from the available disclosure."
                    )


                # ------------------------------------------------
                # TARGET YEAR
                # ------------------------------------------------

                st.markdown(
                    "#### 📅 Target year"
                )

                st.write(
                    item["target_year"]
                )


                # ------------------------------------------------
                # QUANTITATIVE TARGET
                # ------------------------------------------------

                st.markdown(
                    "#### 📊 Quantitative target"
                )

                st.write(
                    item[
                        "quantitative_target"
                    ]
                )


                # ------------------------------------------------
                # COMPANY EVIDENCE
                # ------------------------------------------------

                st.markdown(
                    "#### 🔎 Company disclosure evidence"
                )

                if item["evidence"]:

                    for evidence in item[
                        "evidence"
                    ][:5]:

                        st.write(
                            evidence
                        )

                        st.divider()

                else:

                    st.info(
                        "No supporting passage was extracted."
                    )


                # ------------------------------------------------
                # SOURCES
                # ------------------------------------------------

                st.markdown(
                    "#### 📚 Sources"
                )

                for source in item[
                    "sources"
                ]:

                    st.markdown(
                        f"**{source['title']}**"
                    )

                    st.write(
                        f"Report type: "
                        f"{source['report_type']}"
                    )

                    st.write(
                        f"Reporting year: "
                        f"{source['year']}"
                    )

                    st.link_button(
                        "Open source",
                        source["url"]
                    )


    # ========================================================
    # REPORTS FOUND
    # ========================================================

    st.divider()

    st.subheader(
        "📚 Company Reports Found"
    )

    for report in analysed_reports:

        with st.expander(
            report["title"]
        ):

            st.write(
                f"**Report type:** "
                f"{report['report_type']}"
            )

            st.write(
                f"**Reporting year:** "
                f"{report['reporting_year']}"
            )

            if report["snippet"]:

                st.write(
                    report["snippet"]
                )

            st.link_button(
                "Open report / source",
                report["url"]
            )


    # ========================================================
    # DATA QUALITY WARNING
    # ========================================================

    st.divider()

    st.subheader(
        "⚠️ Data Quality & Analyst Review"
    )

    st.warning(
        """
        This application extracts information from publicly
        accessible webpages. It should not assume that an
        SDG is a company priority merely because the SDG's
        terminology appears in a document.

        Analysts should verify:

        • The SDG is explicitly identified by the company.
        • The target belongs to the company.
        • The target is current.
        • The target year is correct.
        • The metric and baseline are correctly interpreted.
        • The source is the company's official disclosure.
        • Any extracted target is not merely a general
          industry or UN target.
        """
    )


    # ========================================================
    # EXPORT-READY STRUCTURE
    # ========================================================

    st.divider()

    st.subheader(
        "📋 Structured Scorecard Fields"
    )

    st.write(
        """
        The information collected by this prototype can
        eventually be stored using the following structure:
        """
    )

    st.code(
        """
Company
Sector
SDG
SDG Name
Company SDG Priority
Evidence Confidence
Target / Commitment
Target Year
Baseline
Current Value
Target Value
Unit
Progress
Source
Report Name
Reporting Year
Page Reference
Analyst Review
Analyst Comment
        """,
        language="text"
    )


# ============================================================
# LANDING PAGE
# ============================================================

else:

    st.info(
        "Enter a company and click "
        "**Research company**."
    )

    st.markdown(
        """
## 🌍 What this version does

This version is designed around a different question:

> **Which SDGs does the company itself identify as priorities,
> and what targets has it disclosed against those SDGs?**

### 1. Finds current company disclosures

The application searches for:

- Sustainability Reports
- ESG Reports
- Integrated Reports
- Annual Reports
- Climate Reports
- Society Reports
- ESG data books
- Sustainability data reports

### 2. Identifies explicit SDGs

The application looks for explicit references such as:

**SDG 7**

or

**Affordable and Clean Energy**

combined with company commitment language.

### 3. Does not score all 17 SDGs

If a company explicitly identifies only certain SDGs,
only those SDGs are returned.

### 4. Extracts targets

For each identified SDG, the application attempts to
extract:

- Target
- Commitment
- Target year
- Quantitative target
- Supporting evidence
- Source

### 5. Keeps the source

Every extracted SDG and target should be traceable back
to the source document or webpage.

---

## Recommended final methodology

For your actual SDG company scorecard, I would eventually
structure the data as:

**Company**
↓
**Sector**
↓
**Company-identified SDGs**
↓
**SDG target**
↓
**KPI**
↓
**Baseline**
↓
**Current value**
↓
**Target value**
↓
**Target year**
↓
**Progress**
↓
**Analyst assessment**

This is preferable to assigning a score simply because
a sustainability report contains many references to a
particular SDG.
"""
    )



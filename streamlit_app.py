import re
import requests
import streamlit as st
from bs4 import BeautifulSoup
from urllib.parse import quote, urljoin

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="SDG Company Data Explorer",
    page_icon="🌍",
    layout="wide"
)

# ============================================================
# STYLING
# ============================================================

st.markdown("""
<style>
div.stButton > button[kind="primary"] {
    background-color: #0066CC;
    color: white;
    border: none;
    font-weight: 600;
}

div.stButton > button[kind="primary"]:hover {
    background-color: #0052A3;
    color: white;
}

.sdg-card {
    padding: 20px;
    border-radius: 10px;
    border: 1px solid #DDDDDD;
    margin-bottom: 20px;
}

.kpi-card {
    padding: 12px;
    border-radius: 8px;
    background-color: #F7F7F7;
    margin-bottom: 8px;
}

.evidence {
    padding: 10px;
    border-left: 4px solid #0066CC;
    background-color: #F7F7F7;
    margin-top: 8px;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# SDG FRAMEWORK
# INTERNAL ONLY
# ============================================================

SDG_FRAMEWORK = {

    1: {
        "name": "No Poverty",
        "targets": {
            "1.4": "Access to basic services and economic resources",
            "1.5": "Build resilience to economic, social and environmental shocks"
        },
        "kpis": [
            "Living wage",
            "Employees paid living wage",
            "Community investment",
            "Economic impact",
            "Financial inclusion",
            "Employees below living wage"
        ],
        "terms": [
            "living wage",
            "poverty",
            "financial inclusion",
            "community investment",
            "economic inclusion"
        ]
    },

    2: {
        "name": "Zero Hunger",
        "targets": {
            "2.1": "Access to safe and nutritious food",
            "2.4": "Sustainable food production"
        },
        "kpis": [
            "Food security",
            "Food waste",
            "Nutrition programmes",
            "Sustainable agriculture",
            "Agricultural investment"
        ],
        "terms": [
            "food security",
            "food waste",
            "nutrition",
            "agriculture",
            "hunger"
        ]
    },

    3: {
        "name": "Good Health and Well-being",
        "targets": {
            "3.4": "Promote mental health and well-being",
            "3.9": "Reduce illness from hazardous substances and pollution"
        },
        "kpis": [
            "Lost time injury frequency rate",
            "Total recordable injury frequency rate",
            "Fatalities",
            "Occupational injuries",
            "Occupational health",
            "Mental health",
            "Employee wellbeing",
            "Absenteeism"
        ],
        "terms": [
            "occupational health",
            "employee wellbeing",
            "mental health",
            "lost time injury",
            "recordable injury",
            "workplace safety",
            "fatalities"
        ]
    },

    4: {
        "name": "Quality Education",
        "targets": {
            "4.4": "Skills development",
            "4.5": "Equal access to education"
        },
        "kpis": [
            "Training hours per employee",
            "Training expenditure",
            "Employees trained",
            "Skills development",
            "Scholarships",
            "Bursaries",
            "Graduate programmes"
        ],
        "terms": [
            "training",
            "skills development",
            "education",
            "scholarship",
            "bursary",
            "graduate programme"
        ]
    },

    5: {
        "name": "Gender Equality",
        "targets": {
            "5.1": "End discrimination against women and girls",
            "5.5": "Women's participation and leadership"
        },
        "kpis": [
            "Female employees",
            "Female leadership",
            "Women on board",
            "Gender pay gap",
            "Women in management",
            "Parental leave"
        ],
        "terms": [
            "gender equality",
            "female leadership",
            "women in management",
            "gender pay gap",
            "women on board",
            "female employees"
        ]
    },

    6: {
        "name": "Clean Water and Sanitation",
        "targets": {
            "6.3": "Improve water quality",
            "6.4": "Improve water-use efficiency"
        },
        "kpis": [
            "Water consumption",
            "Water withdrawal",
            "Water discharge",
            "Water intensity",
            "Water recycled",
            "Wastewater"
        ],
        "terms": [
            "water consumption",
            "water withdrawal",
            "water intensity",
            "water recycling",
            "wastewater",
            "water efficiency"
        ]
    },

    7: {
        "name": "Affordable and Clean Energy",
        "targets": {
            "7.2": "Increase the share of renewable energy",
            "7.3": "Improve energy efficiency"
        },
        "kpis": [
            "Total energy consumption",
            "Energy intensity",
            "Renewable energy consumption",
            "Renewable electricity",
            "Renewable energy percentage",
            "Energy efficiency",
            "Electricity consumption"
        ],
        "terms": [
            "renewable energy",
            "renewable electricity",
            "solar energy",
            "wind energy",
            "energy consumption",
            "energy intensity",
            "energy efficiency"
        ]
    },

    8: {
        "name": "Decent Work and Economic Growth",
        "targets": {
            "8.5": "Decent work and equal pay",
            "8.8": "Protect labour rights and promote safe working environments"
        },
        "kpis": [
            "Number of employees",
            "Employee turnover",
            "Employee engagement",
            "Living wage",
            "Labour practices",
            "Employment created",
            "Economic contribution"
        ],
        "terms": [
            "decent work",
            "employment",
            "employee turnover",
            "labour rights",
            "labour practices",
            "employee engagement",
            "economic contribution"
        ]
    },

    9: {
        "name": "Industry, Innovation and Infrastructure",
        "targets": {
            "9.4": "Upgrade infrastructure for sustainability",
            "9.5": "Enhance research and innovation"
        },
        "kpis": [
            "Research and development",
            "R&D expenditure",
            "Innovation investment",
            "Infrastructure investment",
            "Technology investment",
            "Digitalisation"
        ],
        "terms": [
            "research and development",
            "innovation",
            "R&D",
            "infrastructure investment",
            "technology investment",
            "digitalisation"
        ]
    },

    10: {
        "name": "Reduced Inequalities",
        "targets": {
            "10.2": "Promote social and economic inclusion",
            "10.3": "Ensure equal opportunity"
        },
        "kpis": [
            "Economic inclusion",
            "Equal opportunity",
            "Employment equity",
            "B-BBEE",
            "Diversity",
            "Inclusion"
        ],
        "terms": [
            "inequality",
            "economic inclusion",
            "equal opportunity",
            "employment equity",
            "B-BBEE",
            "diversity and inclusion"
        ]
    },

    11: {
        "name": "Sustainable Cities and Communities",
        "targets": {
            "11.2": "Sustainable transport",
            "11.6": "Reduce environmental impact of cities"
        },
        "kpis": [
            "Sustainable transport",
            "Green buildings",
            "Affordable housing",
            "Community development",
            "Urban development",
            "Transport emissions"
        ],
        "terms": [
            "sustainable transport",
            "green buildings",
            "affordable housing",
            "community development",
            "urban development"
        ]
    },

    12: {
        "name": "Responsible Consumption and Production",
        "targets": {
            "12.2": "Sustainable management of resources",
            "12.5": "Reduce waste generation",
            "12.6": "Adopt sustainable business practices"
        },
        "kpis": [
            "Total waste generated",
            "Waste recycled",
            "Waste recycling rate",
            "Hazardous waste",
            "Non-hazardous waste",
            "Water consumption",
            "Resource efficiency",
            "Sustainable procurement",
            "Circular economy"
        ],
        "terms": [
            "waste generated",
            "waste recycled",
            "recycling",
            "hazardous waste",
            "circular economy",
            "resource efficiency",
            "sustainable procurement"
        ]
    },

    13: {
        "name": "Climate Action",
        "targets": {
            "13.1": "Strengthen resilience to climate-related hazards",
            "13.2": "Integrate climate measures into policies and strategies"
        },
        "kpis": [
            "Scope 1 emissions",
            "Scope 2 emissions",
            "Scope 3 emissions",
            "Total GHG emissions",
            "GHG emissions intensity",
            "Carbon emissions",
            "Emissions reduction",
            "Net-zero target",
            "Science-based target",
            "Climate risk"
        ],
        "terms": [
            "scope 1",
            "scope 2",
            "scope 3",
            "greenhouse gas emissions",
            "GHG emissions",
            "carbon emissions",
            "net zero",
            "science based target",
            "climate risk",
            "decarbonisation"
        ]
    },

    14: {
        "name": "Life Below Water",
        "targets": {
            "14.1": "Reduce marine pollution",
            "14.2": "Protect marine ecosystems"
        },
        "kpis": [
            "Marine pollution",
            "Ocean impacts",
            "Marine biodiversity",
            "Plastic pollution",
            "Fisheries",
            "Marine ecosystems"
        ],
        "terms": [
            "marine pollution",
            "ocean",
            "marine biodiversity",
            "plastic pollution",
            "fisheries",
            "marine ecosystem"
        ]
    },

    15: {
        "name": "Life on Land",
        "targets": {
            "15.1": "Protect terrestrial ecosystems",
            "15.2": "Sustainable forest management",
            "15.5": "Reduce biodiversity loss"
        },
        "kpis": [
            "Biodiversity impact",
            "Land use",
            "Deforestation",
            "Reforestation",
            "Protected areas",
            "Ecosystem restoration",
            "Biodiversity target"
        ],
        "terms": [
            "biodiversity",
            "deforestation",
            "reforestation",
            "land use",
            "ecosystem restoration",
            "protected areas"
        ]
    },

    16: {
        "name": "Peace, Justice and Strong Institutions",
        "targets": {
            "16.5": "Reduce corruption and bribery",
            "16.6": "Develop effective and accountable institutions"
        },
        "kpis": [
            "Anti-corruption",
            "Bribery incidents",
            "Whistleblowing",
            "Ethics training",
            "Board independence",
            "Governance",
            "Compliance incidents"
        ],
        "terms": [
            "anti-corruption",
            "anti bribery",
            "whistleblowing",
            "ethics",
            "corporate governance",
            "compliance",
            "board independence"
        ]
    },

    17: {
        "name": "Partnerships for the Goals",
        "targets": {
            "17.16": "Global partnerships",
            "17.17": "Public, private and civil society partnerships"
        },
        "kpis": [
            "Sustainability partnerships",
            "Community partnerships",
            "Public-private partnerships",
            "Stakeholder collaboration",
            "SDG partnerships"
        ],
        "terms": [
            "sustainability partnership",
            "strategic partnership",
            "stakeholder collaboration",
            "public private partnership",
            "SDG partnership"
        ]
    }
}

# ============================================================
# JSE COMPANY LIST
# ============================================================

JSE_COMPANIES = [
    "Absa Group",
    "AECI",
    "Afrimat",
    "African Rainbow Minerals",
    "Anglo American",
    "Anglo American Platinum",
    "AngloGold Ashanti",
    "Astral Foods",
    "Attacq",
    "AVI",
    "Balwin Properties",
    "BHP Group",
    "Bid Corporation",
    "Bidvest",
    "Capitec Bank",
    "Discovery",
    "Exxaro Resources",
    "FirstRand",
    "Fortress REIT",
    "Gold Fields",
    "Harmony Gold",
    "Impala Platinum",
    "Kumba Iron Ore",
    "Life Healthcare",
    "Momentum Metropolitan",
    "MTN Group",
    "Naspers",
    "Nedbank Group",
    "NEPI Rockcastle",
    "Old Mutual",
    "Pepkor",
    "Prosus",
    "Remgro",
    "Reunert",
    "Sanlam",
    "Sasol",
    "Shoprite Holdings",
    "Sibanye Stillwater",
    "Standard Bank Group",
    "Telkom",
    "Thungela Resources",
    "Tiger Brands",
    "Vodacom",
    "Woolworths Holdings"
]

# ============================================================
# WEB SEARCH
# ============================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/130 Safari/537.36"
    )
}


def search_web(company, num_results=8):

    query = f'"{company}" sustainability ESG annual report climate'

    url = (
        "https://html.duckduckgo.com/html/?q="
        + quote(query)
    )

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=15
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        results = []

        for result in soup.select(".result")[:num_results]:

            title_element = result.select_one(".result__a")
            snippet_element = result.select_one(".result__snippet")

            if not title_element:
                continue

            title = title_element.get_text(" ", strip=True)
            link = title_element.get("href", "")
            snippet = (
                snippet_element.get_text(" ", strip=True)
                if snippet_element
                else ""
            )

            results.append({
                "title": title,
                "url": link,
                "snippet": snippet
            })

        return results

    except Exception as e:

        st.error(f"Web search error: {e}")

        return []


# ============================================================
# PAGE TEXT EXTRACTION
# ============================================================

def get_page_text(url):

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=15
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        for tag in soup([
            "script",
            "style",
            "noscript",
            "header",
            "footer",
            "nav"
        ]):
            tag.decompose()

        text = soup.get_text(
            " ",
            strip=True
        )

        return text[:100000]

    except Exception:
        return ""


# ============================================================
# FIND RELEVANT EVIDENCE
# ============================================================

def find_evidence(text, terms):

    text_lower = text.lower()

    matches = []

    for term in terms:

        position = text_lower.find(
            term.lower()
        )

        if position == -1:
            continue

        start = max(
            0,
            position - 300
        )

        end = min(
            len(text),
            position + 500
        )

        evidence = text[start:end].strip()

        matches.append({
            "term": term,
            "evidence": evidence
        })

    return matches


# ============================================================
# KPI EXTRACTION
# ============================================================

def extract_kpi_values(text, kpi):

    results = []

    text_lower = text.lower()

    keyword = kpi.lower()

    positions = [
        m.start()
        for m in re.finditer(
            re.escape(keyword),
            text_lower
        )
    ]

    for position in positions[:5]:

        start = max(
            0,
            position - 150
        )

        end = min(
            len(text),
            position + 350
        )

        context = text[start:end]

        # Look for percentages
        percentages = re.findall(
            r"\b\d+(?:\.\d+)?\s?%",
            context
        )

        # Look for numbers with units
        quantities = re.findall(
            r"\b\d+(?:\.\d+)?\s?"
            r"(?:tCO2e|tCO₂e|tonnes|tons|MWh|GWh|TJ|"
            r"litres|million|billion|employees|hours)\b",
            context,
            flags=re.IGNORECASE
        )

        values = percentages + quantities

        results.append({
            "context": context,
            "values": list(dict.fromkeys(values))
        })

    return results


# ============================================================
# ANALYSE COMPANY
# ============================================================

def analyse_company(company, num_results):

    search_results = search_web(
        company,
        num_results
    )

    sdg_results = {}

    for result in search_results:

        page_text = (
            result["snippet"]
            + " "
            + get_page_text(result["url"])
        )

        if not page_text:
            continue

        for sdg_number, sdg in SDG_FRAMEWORK.items():

            evidence = find_evidence(
                page_text,
                sdg["terms"]
            )

            if not evidence:
                continue

            if sdg_number not in sdg_results:

                sdg_results[sdg_number] = {
                    "name": sdg["name"],
                    "targets": sdg["targets"],
                    "kpis": {},
                    "evidence": [],
                    "sources": []
                }

            for item in evidence[:3]:

                sdg_results[
                    sdg_number
                ]["evidence"].append({
                    "term": item["term"],
                    "text": item["evidence"],
                    "source": result["title"],
                    "url": result["url"]
                })

            source_exists = any(
                s["url"] == result["url"]
                for s in sdg_results[
                    sdg_number
                ]["sources"]
            )

            if not source_exists:

                sdg_results[
                    sdg_number
                ]["sources"].append({
                    "title": result["title"],
                    "url": result["url"]
                })

            # KPI matching
            for kpi in sdg["kpis"]:

                kpi_evidence = find_evidence(
                    page_text,
                    [kpi]
                )

                if kpi_evidence:

                    values = extract_kpi_values(
                        page_text,
                        kpi
                    )

                    if kpi not in sdg_results[
                        sdg_number
                    ]["kpis"]:

                        sdg_results[
                            sdg_number
                        ]["kpis"][kpi] = {
                            "values": [],
                            "sources": []
                        }

                    for value_data in values:

                        for value in value_data["values"]:

                            if value not in sdg_results[
                                sdg_number
                            ]["kpis"][kpi]["values"]:

                                sdg_results[
                                    sdg_number
                                ]["kpis"][kpi]["values"].append(
                                    value
                                )

                    if result["url"] not in [
                        s["url"]
                        for s in sdg_results[
                            sdg_number
                        ]["kpis"][kpi]["sources"]
                    ]:

                        sdg_results[
                            sdg_number
                        ]["kpis"][kpi]["sources"].append({
                            "title": result["title"],
                            "url": result["url"]
                        })

    return sdg_results


# ============================================================
# USER INTERFACE
# ============================================================

st.title("🌍 SDG Company Data Explorer")

st.write(
    "Search a JSE-listed company and identify the SDGs, "
    "KPIs, targets and supporting evidence found in public information."
)

st.divider()

# ------------------------------------------------------------
# COMPANY SELECTION
# ------------------------------------------------------------

st.subheader("Enter Company Name")

company = st.selectbox(
    "Company",
    JSE_COMPANIES,
    index=None,
    placeholder="Start typing a JSE company name..."
)

num_results = st.slider(
    "Web results to analyse",
    min_value=3,
    max_value=12,
    value=8
)

run = st.button(
    "Enter",
    type="primary",
    use_container_width=True
)

# ============================================================
# RUN ANALYSIS
# ============================================================

if run:

    if not company:

        st.warning(
            "Please select a company."
        )

    else:

        with st.spinner(
            f"Researching {company}..."
        ):

            results = analyse_company(
                company,
                num_results
            )

        st.session_state[
            "sdg_results"
        ] = results

        st.session_state[
            "company"
        ] = company


# ============================================================
# DISPLAY RESULTS
# ============================================================

if "sdg_results" in st.session_state:

    results = st.session_state[
        "sdg_results"
    ]

    company = st.session_state[
        "company"
    ]

    st.divider()

    st.header(
        f"SDG Analysis: {company}"
    )

    if not results:

        st.warning(
            "No SDG-related evidence was identified "
            "from the web sources analysed."
        )

    else:

        st.success(
            f"{len(results)} relevant SDG(s) identified."
        )

        # IMPORTANT:
        # Only SDGs with evidence are displayed.
        for sdg_number in sorted(results):

            sdg = results[
                sdg_number
            ]

            st.markdown(
                f"""
                <div class="sdg-card">
                <h2>SDG {sdg_number} — {sdg["name"]}</h2>
                </div>
                """,
                unsafe_allow_html=True
            )

            # ------------------------------------------------
            # TARGETS
            # ------------------------------------------------

            st.subheader(
                "Relevant Targets"
            )

            for target, description in sdg[
                "targets"
            ].items():

                st.write(
                    f"**{target}** — {description}"
                )

            # ------------------------------------------------
            # KPIs
            # ------------------------------------------------

            st.subheader(
                "Underlying KPIs"
            )

            if sdg["kpis"]:

                for kpi, data in sdg[
                    "kpis"
                ].items():

                    values = data[
                        "values"
                    ]

                    if values:

                        value_text = ", ".join(
                            values[:5]
                        )

                        st.markdown(
                            f"""
                            <div class="kpi-card">
                            <b>{kpi}</b><br>
                            Identified value(s): {value_text}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    else:

                        st.markdown(
                            f"""
                            <div class="kpi-card">
                            <b>{kpi}</b><br>
                            KPI identified — value not found.
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

            else:

                st.write(
                    "No specific KPI was identified."
                )

            # ------------------------------------------------
            # EVIDENCE
            # ------------------------------------------------

            st.subheader(
                "Supporting Evidence"
            )

            displayed_evidence = set()

            for evidence in sdg[
                "evidence"
            ][:6]:

                key = (
                    evidence["url"],
                    evidence["term"]
                )

                if key in displayed_evidence:
                    continue

                displayed_evidence.add(key)

                st.markdown(
                    f"""
                    <div class="evidence">
                    <b>Evidence related to:</b>
                    {evidence["term"]}<br><br>
                    {evidence["text"]}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                st.markdown(
                    f"[Source: {evidence['source']}]"
                    f"({evidence['url']})"
                )

            st.divider()

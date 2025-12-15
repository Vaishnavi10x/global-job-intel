import pandas as pd
import numpy as np
import re
import json
import os
from dotenv import load_dotenv

import typesense
import time
import io
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime, timedelta
from rapidfuzz import process, fuzz # Ensure you ran: pip install rapidfuzz

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

cached_df = None
load_dotenv()

# --- CONFIGURATION ---
TYPESENSE_CONFIG = {
    'nodes': [{
        'host': os.getenv('TYPESENSE_HOST'),
        'port': os.getenv('TYPESENSE_PORT'),
        'protocol': os.getenv('TYPESENSE_PROTOCOL')
    }],
    'api_key': os.getenv('TYPESENSE_API_KEY'),
    'connection_timeout_seconds': 300
}

# --- 1. CONFIGURATION ---


JUNK_SKILLS = [
    "gymnastic", "driving", "cleaning", "music", "unknown", "communication skills", 
    "good communication", "written communication", "verbal communication", 
    "team player", "interpersonal skills", "indian cinema", "sports", "swimming", 
    "soft skills", "fluent english", "ms office", "microsoft office", "communication",
    "leadership", "management", "problem solving", "analytical skills", "time management",
    "presentation skills", "negotiation", "teamwork", "adaptability",
    "maharashtra", "karnataka", "uttar pradesh", "tamil nadu", "telangana", "andhra pradesh",
    "west bengal", "gujarat", "rajasthan", "kerala", "haryana", "punjab", "madhya pradesh",
    "delhi", "new delhi", "mumbai", "bangalore", "bengaluru", "hyderabad", "chennai", "pune",
    "noida", "gurgaon", "gurugram", "kolkata", "ahmedabad", "india", "usa", "united states",
    "uk", "london", "dubai", "remote", "work from home", "wfh", "hybrid", "onsite", 
    "full time", "part time", "contract", "permanent", "temporary", "internship", "fresher"
]

CITY_COORDS = {
    'bengaluru': [12.9716, 77.5946], 'bangalore': [12.9716, 77.5946],
    'hyderabad': [17.3850, 78.4867], 'secunderabad': [17.4399, 78.4983],
    'chennai': [13.0827, 80.2707], 'mumbai': [19.0760, 72.8777],
    'pune': [18.5204, 73.8567], 'delhi': [28.7041, 77.1025], 'new delhi': [28.6139, 77.2090],
    'noida': [28.5355, 77.3910], 'gurgaon': [28.4595, 77.0266], 'gurugram': [28.4595, 77.0266],
    'kolkata': [22.5726, 88.3639], 'ahmedabad': [23.0225, 72.5714],
    'jaipur': [26.9124, 75.7873], 'chandigarh': [30.7333, 76.7794],
    'indore': [22.7196, 75.8577], 'kochi': [9.9312, 76.2673],
    'trivandrum': [8.5241, 76.9366], 'coimbatore': [11.0168, 76.9558], 'lucknow': [26.8467, 80.9462], 
    'nagpur': [21.1458, 79.0882], 'surat': [21.1702, 72.8311],
    'bhopal': [23.2599, 77.4126], 'patna': [25.5941, 85.1376],
    'kanpur': [26.4499, 80.3319], 'thane': [19.2183, 72.9781], 'navi mumbai': [19.0330, 73.0297],
    'london': [51.5074, -0.1278], 'new york': [40.7128, -74.0060],
    'san francisco': [37.7749, -122.4194], 'berlin': [52.5200, 13.4050],
    'singapore': [1.3521, 103.8198], 'dubai': [25.2048, 55.2708],
    'sydney': [-33.8688, 151.2093], 'tokyo': [35.6762, 139.6503],
    'paris': [48.8566, 2.3522], 'toronto': [43.6510, -79.3470],
    'amsterdam': [52.3676, 4.9041], 'madrid': [40.4168, -3.7038],
    'los angeles': [34.0522, -118.2437], 'chicago': [41.8781, -87.6298],
    'austin': [30.2672, -97.7431], 'seattle': [47.6062, -122.3321]
}

# --- 4. EXPANDED DICTIONARY (Fixed Missing Categories) ---
ROLE_MAPPINGS = {
    # --- 1. LEADERSHIP & STRATEGY ---
    "Engineering Management": ["engineering manager", "director of engineering", "vp of engineering", "head of engineering", "cto", "tech lead", "team lead", "development manager", "software manager", "application lead", "technical lead"],
    "Product Leadership": ["chief product officer", "head of product", "vp product", "director of product", "product lead", "group product manager"],
    "Executive / C-Suite": ["ceo", "cfo", "coo", "chief executive", "president", "founder", "co-founder", "vice president", "director of operations"],
    
    # --- 2. CORE TECH ---
    "Frontend Development": ["frontend", "front-end", "front end", "react", "angular", "vue", "ui developer", "web developer", "javascript developer", "js developer", "next.js"],
    "Backend Development": ["backend", "back-end", "back end", "node.js", "django", "flask", "laravel", "express", "ruby on rails", "php developer", "golang", "java developer", "spring boot", "java engineer", "python developer"],
    "Mobile Development": ["ios", "android", "mobile", "flutter", "react native", "swift", "kotlin", "app developer"],
    "Data Science": ["data scientist", "machine learning", "ai ", "artificial intelligence", "nlp", "computer vision", "deep learning", "predictive modeling", "generative ai", "llm", "applied scientist"],
    "Data Engineering": ["data engineer", "etl", "spark", "hadoop", "big data", "airflow", "kafka", "warehouse", "database engineer", "data architect", "database administrator", "dba"],
    "DevOps & Cloud": ["devops", "sre", "site reliability", "cloud engineer", "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ci/cd", "infrastructure", "platform engineer"],
    "Cybersecurity": ["cyber", "infosec", "penetration", "vulnerability", "network security", "security analyst", "security engineer", "ciso", "security operations", "information security"],
    "Software Architecture": ["solutions architect", "technical architect", "enterprise architect", "software architect", "cloud architect", "systems architect"],
    "QA & Testing": ["qa ", "quality assurance", "test engineer", "automation tester", "selenium", "manual testing", "sdet", "test automation", "software tester"],
    "UI/UX Design": ["ui/ux", "user interface", "user experience", "product design", "interaction design", "figma", "ux researcher", "senior designer", "ux designer", "ui designer", "visual designer"],
    "Network Engineering": ["network engineer", "network administrator", "system administrator", "network analyst", "noc technician"],

    # --- 3. GENERAL TECH CATCH-ALL ---
    "Software Development (General)": ["software engineer", "software development", "developer", "programmer", "sde", "full stack", "application developer", ".net", "c#", "c++", "software design", "engineer", "web engineer", "mulesoft", "salesforce developer"],
    "Data Analysis": ["data analyst", "business analyst", "analytics", "tableau", "power bi", "sql", "reporting", "bi developer", "operations analyst"],
    "Technical Support": ["technical support", "help desk", "service desk", "it support", "desktop support", "system support", "application support"],

    # --- 4. BUSINESS FUNCTIONS ---
    "Product Management": ["product manager", "product owner", "scrum product", "product strategy"],
    "Project Management": ["project manager", "program manager", "scrum master", "agile", "delivery manager", "pmo", "project coordinator"],
    "Sales": ["sales", "business development", "bde", "account executive", "inside sales", "closer", "revenue", "account manager", "sales representative", "client executive"],
    "Marketing": ["marketing", "seo", "content", "social media", "brand", "growth", "campaign", "digital marketing", "market research"],
    "HR & Recruiting": ["hr ", "human resources", "recruiter", "talent", "people ops", "payroll", "hrbp", "benefits", "staffing"],
    "Customer Success": ["customer success", "csm", "client success", "client relationship", "onboarding specialist", "account specialist"],
    "Customer Service": ["customer service", "call center", "support specialist", "client support", "customer care", "representative"],
    "Finance & Accounting": ["finance", "accountant", "audit", "tax", "banking", "controller", "bookkeeper", "financial analyst", "accounts payable", "treasury"],
    "Operations": ["operations manager", "admin", "clerk", "logistics", "supply chain", "warehouse", "inventory", "coordinator", "scheduler", "planner"],
    "Legal & Compliance": ["legal", "lawyer", "attorney", "compliance", "counsel", "paralegal", "contract manager"],
    
    # --- 5. CONTENT & CREATIVE ---
    "Content & Writing": ["content writer", "copywriter", "editor", "content strategist", "technical writer", "documentation", "journalist"],
    "Creative & Media": ["graphic designer", "art director", "creative director", "animator", "illustrator", "multimedia", "video editor", "photographer", "producer"],

    # --- 6. OTHER INDUSTRIES (To clean the "Other" pile) ---
    "Education": ["teacher", "professor", "tutor", "academic", "trainer", "instructor", "faculty", "education"],
    "Healthcare": ["nurse", "medical", "doctor", "pharmacy", "clinical", "physician", "therapist", "psychologist", "healthcare", "caregiver"],
    "Construction & Civil": ["site engineer", "civil engineer", "surveyor", "structural engineer", "construction manager", "site supervisor"],
    "Mechanical & Electrical": ["mechanical engineer", "electrical engineer", "technician", "electrician", "mechanic", "maintenance", "service engineer"],
    "Retail & Hospitality": ["store manager", "retail", "chef", "cook", "restaurant", "hotel", "housekeeping", "front desk", "receptionist", "barista"],
}


# --- HELPERS ---
def clean_salary_aggressive(x):
    if not isinstance(x, str): return 0
    x = x.lower().replace(',', '').replace('₹', '').replace('$', '').strip()
    if "not" in x or "disclosed" in x: return 0
    nums = re.findall(r'(\d+\.?\d*)', x)
    if not nums: return 0
    vals = [float(n) for n in nums]
    avg = sum(vals) / len(vals)
    if avg < 100: avg *= 100000 
    return int(avg)

def clean_experience_aggressive(x):
    if not isinstance(x, str): return 0
    nums = re.findall(r'(\d+\.?\d*)', str(x))
    if not nums: return 0
    return float(nums[0])

# --- TYPESENSE FETCHER ---
def fetch_from_typesense():
    if os.path.exists("live_cache.csv"):
        if (time.time() - os.path.getmtime("live_cache.csv")) < 86400:
            print("⚡ Loading from Local Cache...")
            return pd.read_csv("live_cache.csv", low_memory=False)

    print("📡 Connecting to Typesense Cloud...")
    try:
        client = typesense.Client(TYPESENSE_CONFIG)
        # Removed unused variables
        
        print("⏳ Streaming ALL Data (Export Mode)...")
        try: jsonl_data = client.collections['jobs'].documents.export()
        except: jsonl_data = client.collections['job_postings'].documents.export()
        
        if not jsonl_data:
            print("❌ Export returned empty data.")
            return None

        print("⚡ Parsing data into DataFrame...")
        df = pd.read_json(io.StringIO(jsonl_data), lines=True)
        df.to_csv("live_cache.csv", index=False)
        print(f"✅ Fetched Total {len(df)} Live Jobs.")
        return df

    except Exception as e:
        print(f"❌ Typesense Error: {e}")
        return None

def load_data_internal():
    global cached_df

    df = fetch_from_typesense()
    if df is None or df.empty:
        try: df = pd.read_csv("jobs.csv", low_memory=False)
        except: return

    df.columns = df.columns.str.strip().str.lower()
    
    rename_map = {
        "title": "raw_role", "job title": "raw_role", "job_title": "raw_role",
        "location": "raw_location", "ctc": "ctc", "salary": "ctc",
        "min_experience": "min_experience", "skills": "skills", "key_skills": "skills",
        "posted_at": "posted_at", "job_type": "job_type", "location_type": "location_type",
        "apply_link": "apply_url", "url": "apply_url",
        "company_name": "company_name", "description": "description",
        "latlon": "latlon"
    }
    df.rename(columns=rename_map, inplace=True)

    # --- FUZZY CLASSIFIER (OPTIMIZED) ---
    print("🧠 Classifying Roles (Fuzzy Logic)...")
    unique_titles = df['raw_role'].unique()
    title_map = {}

    for title in unique_titles:
        if not isinstance(title, str): 
            title_map[title] = "Other"
            continue
            
        t_lower = title.lower()
        matched_group = "Other"
        
        # 1. Exact Substring Match (Fast)
        for group, keywords in ROLE_MAPPINGS.items():
            if any(k in t_lower for k in keywords):
                matched_group = group
                break
        
        # 2. Fuzzy Match (If Exact Failed)
        if matched_group == "Other":
            # Check against all keywords using partial match
            best_score = 0
            for group, keywords in ROLE_MAPPINGS.items():
                match = process.extractOne(t_lower, keywords, scorer=fuzz.partial_ratio)
                if match and match[1] > 85: # Strict Threshold
                    if match[1] > best_score:
                        best_score = match[1]
                        matched_group = group

        title_map[title] = matched_group

    df["job_role"] = df["raw_role"].map(title_map)
    print("✅ Classification Complete.")

    # Location Parsing
    if "raw_location" in df.columns:
        def parse_location(loc):
            if not isinstance(loc, str): return "Unknown", "Global"
            parts = [p.strip() for p in loc.split(',')]
            
            raw_city = parts[0].title()
            CITY_FIX = {"Bangalore": "Bengaluru", "Gurgaon": "Gurugram", "Bombay": "Mumbai", "Us": "Remote", "India": "Remote"}
            city = CITY_FIX.get(raw_city, raw_city)

            country = parts[-1].title() if len(parts) > 1 else "Global"
            loc_lower = loc.lower()
            if "india" in loc_lower and "indiana" not in loc_lower: country = "India"
            elif any(c in loc_lower for c in ['bengaluru', 'mumbai', 'delhi', 'pune']): country = "India"
            elif "united states" in loc_lower or " usa" in loc_lower: country = "USA"
            
            if city == country: city = "Remote"
            return city, country

        df[['city', 'country']] = df['raw_location'].apply(lambda x: pd.Series(parse_location(x)))
    else:
        df["city"], df["country"] = "Unknown", "Global"

    # LatLon
    def parse_latlon_hybrid(row):
        val = row.get("latlon")
        lat, lon = None, None
        try:
            if isinstance(val, list) and len(val) == 2:
                lat, lon = float(val[0]), float(val[1])
            elif isinstance(val, str):
                clean = val.replace('[', '').replace(']', '').strip()
                if clean:
                    parts = clean.split(',')
                    if len(parts) == 2:
                        lat, lon = float(parts[0]), float(parts[1])
        except: pass

        if (lat is None or pd.isna(lat)) and isinstance(row.get("city"), str):
            city_key = row["city"].lower()
            if city_key in CITY_COORDS:
                lat, lon = CITY_COORDS[city_key]
        return lat, lon

    df[['lat', 'lon']] = df.apply(lambda x: pd.Series(parse_latlon_hybrid(x)), axis=1)

    # Metrics
    if "ctc" in df.columns: df["parsed_salary"] = df["ctc"].astype(str).apply(clean_salary_aggressive)
    else: df["parsed_salary"] = 0
    
    if "min_experience" in df.columns: df["min_experience"] = df["min_experience"].astype(str).apply(clean_experience_aggressive)
    else: df["min_experience"] = 0

    if "posted_at" in df.columns:
        df["post_date"] = pd.to_numeric(df["posted_at"], errors='coerce')
        df["post_date"] = pd.to_datetime(df["post_date"], unit='s', errors='coerce')
    else:
        df["post_date"] = pd.NaT

    # Skills Cleaning
    if "skills" in df.columns:
        def clean_skills(x):
            if isinstance(x, list): raw_list = [str(s).lower() for s in x]
            else: raw_list = [s.strip().lower() for s in str(x).replace("'", "").replace("[", "").replace("]", "").split(",") if s.strip()]
            
            final_list = []
            for s in raw_list:
                if any(junk == s for junk in JUNK_SKILLS): continue
                if len(s) < 2: continue
                final_list.append(s)
            return final_list
        df["skills"] = df["skills"].apply(clean_skills)

    cached_df = df
    print(f"Data Loaded: {len(df)} rows.")

@app.on_event("startup")
def startup_event():
    load_data_internal()

@app.get("/filter-options")
def get_filter_options():
    if cached_df is None: return {"countries": [], "roles": []}
    countries = sorted([str(x) for x in cached_df["country"].unique() if x and len(str(x)) > 1])
    roles = []
    if "job_role" in cached_df.columns:
        roles = sorted([str(r) for r in cached_df["job_role"].unique() if r and str(r) not in ['nan', 'Unknown']])
        if "Other" in roles:
            roles.remove("Other")
            roles.append("Other")
    return {"countries": countries, "roles": roles}

# ... (Endpoints apply_filters, kpis, companies, map-points, skills, salary, raw-jobs remain unchanged) ...
def apply_filters(df, countries, role, exp_max, keywords, days_ago):
    if df is None: return pd.DataFrame()
    d = df.copy()
    if countries and "Global" not in countries: d = d[d["country"].isin(countries)]
    if role and role != "All Roles": d = d[d["job_role"] == role]
    if exp_max is not None: d = d[d["min_experience"] <= exp_max]
    if keywords:
        k = keywords.lower()
        mask = d["raw_role"].astype(str).str.lower().str.contains(k, na=False)
        mask |= d["job_role"].astype(str).str.lower().str.contains(k, na=False)
        if "description" in d.columns:
             mask |= d["description"].astype(str).str.lower().str.contains(k, na=False)
        d = d[mask]
    if days_ago is not None and days_ago > 0:
        if "post_date" in d.columns:
            cutoff = pd.Timestamp.now() - pd.Timedelta(days=days_ago)
            d = d[d["post_date"] >= cutoff]
    return d

@app.get("/kpis")
def kpis(countries: Optional[List[str]] = Query(None), role: Optional[str] = None, exp_min: int = 20, keywords: Optional[str] = None, days_ago: Optional[int] = None):
    d = apply_filters(cached_df, countries, role, exp_min, keywords, days_ago)
    if d.empty: return {"total_jobs": 0, "avg_ctc": 0, "avg_experience": 0, "top_skill": "N/A"}
    valid_sal = d[d["parsed_salary"] > 0]
    avg_ctc = valid_sal["parsed_salary"].mean() if not valid_sal.empty else 0
    top_skill = "N/A"
    if "skills" in d.columns:
        s = d["skills"].explode().dropna()
        if not s.empty: top_skill = s.value_counts().idxmax()
    remote = len(d[d["location_type"].astype(str).str.lower().str.contains("remote", na=False)]) if "location_type" in d.columns else 0
    return {"total_jobs": len(d), "avg_ctc": avg_ctc, "avg_experience": d["min_experience"].mean(), "top_skill": top_skill, "remote_count": remote, "onsite_count": len(d)-remote}

@app.get("/companies")
def companies_endpoint(countries: Optional[List[str]] = Query(None), role: Optional[str] = None, exp_min: int = 20, keywords: Optional[str] = None, days_ago: Optional[int] = None):
    d = apply_filters(cached_df, countries, role, exp_min, keywords, days_ago)
    if d.empty or "company_name" not in d.columns: return []
    
    # 1. Standardize Case
    c = d["company_name"].astype(str).str.title().str.strip()
    
    # 2. THE FILTER: Remove Junk Values
    junk_companies = [
        "Nan", "None", "Null", "Unknown", "Confidential", 
        "Company Name", "Private", "Hidden", "Client Of"
    ]
    
    # Exclude rows where company name is in the junk list OR starts with "Client Of"
    c = c[~c.isin(junk_companies) & ~c.str.startswith("Client Of")]
    
    return [{"company": k, "count": int(v)} for k, v in c.value_counts().head(10).items()]

@app.get("/map-points")
def map_points(countries: Optional[List[str]] = Query(None), role: Optional[str] = None, exp_min: int = 20, keywords: Optional[str] = None, days_ago: Optional[int] = None):
    d = apply_filters(cached_df, countries, role, exp_min, keywords, days_ago)
    if d.empty: return []
    d_coords = d.dropna(subset=['lat', 'lon'])
    if d_coords.empty: return []
    city_counts = d_coords.groupby("city").agg(count=("city", "count"), lat=("lat", "mean"), lon=("lon", "mean")).reset_index()
    return city_counts.to_dict(orient="records")

@app.get("/skills")
def skills_endpoint(countries: Optional[List[str]] = Query(None), role: Optional[str] = None, exp_min: int = 20, keywords: Optional[str] = None, days_ago: Optional[int] = None):
    d = apply_filters(cached_df, countries, role, exp_min, keywords, days_ago)
    if d.empty: return []
    if "skills" in d.columns:
        s = d["skills"].explode()
        s = s[s.notna() & (s != "")]
        return [{"skill": k, "count": int(v)} for k, v in s.value_counts().head(15).items()]
    return []

@app.get("/salary_by_experience")
def salary_endpoint(countries: Optional[List[str]] = Query(None), role: Optional[str] = None, exp_min: int = 20, keywords: Optional[str] = None, days_ago: Optional[int] = None):
    d = apply_filters(cached_df, countries, role, exp_min, keywords, days_ago)
    d = d[(d["parsed_salary"] > 0) & (d["min_experience"] < 30)]
    if d.empty: return []
    top_cities = d["city"].value_counts().head(100).index.tolist()
    d = d[d["city"].isin(top_cities)]
    d["years"] = d["min_experience"].astype(int)
    agg = d.groupby(["city", "years"]).agg(avg_salary=("parsed_salary", "mean"), job_count=("parsed_salary", "count")).reset_index()
    return agg.to_dict(orient="records")

@app.get("/raw-jobs")
def raw_jobs(countries: Optional[List[str]] = Query(None), role: Optional[str] = None, exp_min: int = 20, keywords: Optional[str] = None, days_ago: Optional[int] = None, limit: int = 10):
    d = apply_filters(cached_df, countries, role, exp_min, keywords, days_ago)
    if d.empty: return []
    return d[["job_role", "city", "country", "min_experience", "parsed_salary", "location_type", "job_type", "apply_url", "job_id"]].head(limit).fillna("").to_dict(orient="records")
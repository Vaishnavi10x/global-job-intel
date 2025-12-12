import pandas as pd
import numpy as np
import re
import json
import os
import typesense
import time
import io
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime, timedelta
# NEW: Import RapidFuzz for Typo Tolerance
from rapidfuzz import process as fuzzy_process, fuzz

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

cached_df = None
ai_role_cache = {}

# --- CONFIG ---
TYPESENSE_CONFIG = {
    'nodes': [{'host': 'search.jobs.10xscale.ai', 'port': '443', 'protocol': 'https'}],
    'api_key': 'SVcCXku0gWOx3hVLCrDU9m4gaLPBuvnL',
    'connection_timeout_seconds': 300
}

JUNK_SKILLS = [
    "gymnastic", "driving", "cleaning", "music", "unknown", "communication skills", 
    "good communication", "written communication", "verbal communication", 
    "team player", "interpersonal skills", "indian cinema", "sports", "swimming", 
    "soft skills", "fluent english", "ms office"
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
    'amsterdam': [52.3676, 4.9041], 'madrid': [40.4168, -3.7038]
}

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
        
        print("⏳ Streaming ALL Data (Export Mode)...")
        try:
            jsonl_data = client.collections['jobs'].documents.export()
        except:
            jsonl_data = client.collections['job_postings'].documents.export()
        
        if not jsonl_data:
            print("❌ Export returned empty data.")
            return None

        print("⚡ Parsing data...")
        df = pd.read_json(io.StringIO(jsonl_data), lines=True)
        
        df.to_csv("live_cache.csv", index=False)
        print(f"✅ Fetched Total {len(df)} Live Jobs.")
        return df

    except Exception as e:
        print(f"❌ Typesense Error: {e}")
        return None

def load_data_internal():
    global cached_df, ai_role_cache
    
    if os.path.exists("gemini_role_map.json"):
        with open("gemini_role_map.json", "r") as f:
            ai_role_cache = json.load(f)
    else:
        ai_role_cache = {}

    df = fetch_from_typesense()
    if df is None or df.empty:
        try: df = pd.read_csv("jobs.csv", low_memory=False)
        except: return

    df.columns = df.columns.str.strip().str.lower()
    
    rename_map = {
        "title": "raw_role", "job title": "raw_role", 
        "location": "raw_location", "ctc": "ctc", "salary": "ctc",
        "min_experience": "min_experience", "skills": "skills", 
        "posted_at": "posted_at", "job_type": "job_type", "location_type": "location_type",
        "apply_link": "apply_url", "url": "apply_url",
        "company_name": "company_name", "description": "description",
        "latlon": "latlon"
    }
    df.rename(columns=rename_map, inplace=True)

    # --- COORDINATE PARSING ---
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
                    if len(parts) == 2: lat, lon = float(parts[0]), float(parts[1])
        except: pass

        if (lat is None or pd.isna(lat)) and isinstance(row.get("city"), str):
            city_key = row["city"].lower()
            if city_key in CITY_COORDS:
                lat, lon = CITY_COORDS[city_key]
        
        return lat, lon

    # --- ROLE STANDARDIZATION (AI + DICTIONARY + FUZZY) ---
    # Define Dictionary Outside to avoid re-creating it
    MANUAL_MAPPINGS = {
        "Software Development": ["software engineer", "developer", "programmer", "sde", "full stack", "backend", "frontend", ".net", "java", "coding", "web developer"],
        "Data Science": ["data scientist", "data analyst", "machine learning", "ai ", "artificial intelligence", "nlp", "computer vision"],
        "DevOps & Cloud": ["devops", "sre", "cloud", "aws", "azure", "docker", "kubernetes", "linux"],
        "Product Management": ["product manager", "product owner", "scrum product"],
        "Design": ["ui", "ux", "designer", "graphic", "creative", "artist"],
        "Sales": ["sales", "business development", "bde", "account manager", "inside sales"],
        "Marketing": ["marketing", "seo", "content", "social media", "brand", "digital marketing"],
        "HR": ["hr ", "human resources", "recruiter", "talent", "payroll"],
        "Customer Support": ["customer support", "customer service", "help desk", "support specialist"],
        "Finance": ["accountant", "finance", "audit", "tax", "banking"],
    }

    def standardize_role(title):
        if not isinstance(title, str): return "Other"
        t_clean = title.strip()
        t_lower = t_clean.lower()
        
        # 1. Check AI JSON (Fastest)
        if t_clean in ai_role_cache:
            mapped = ai_role_cache[t_clean]
            if mapped != "Other": return mapped

        # 2. Check Manual Dictionary (Exact Substring)
        for group, keywords in MANUAL_MAPPINGS.items():
            for k in keywords:
                if k in t_lower: return group

        # 3. Fuzzy Matching (Slower but catches "Softwear Enginer")
        # We check the title against all keywords in our dictionary
        best_score = 0
        best_group = None
        
        # Iterate groups
        for group, keywords in MANUAL_MAPPINGS.items():
            # Extract best match for this title against the list of keywords for this group
            match = fuzzy_process.extractOne(t_lower, keywords, scorer=fuzz.token_set_ratio)
            if match:
                score = match[1]
                if score > 85: # Strict threshold
                    if score > best_score:
                        best_score = score
                        best_group = group
        
        if best_group: return best_group

        return "Other"

    print("🧠 Standardizing Roles (This may take a moment)...")
    if "raw_role" in df.columns:
        df["job_role"] = df["raw_role"].apply(standardize_role)
    else:
        df["job_role"] = "Unknown"

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

    # Apply Lat/Lon
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
            if isinstance(x, list): raw_list = [str(s).lower().strip() for s in x]
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
        # Sort and exclude junk
        roles = sorted([str(r) for r in cached_df["job_role"].unique() if r and str(r) not in ['nan', 'Unknown', 'Other']])
    return {"countries": countries, "roles": roles}

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
    
    remote = 0
    onsite = 0
    if "location_type" in d.columns:
        remote = len(d[d["location_type"].astype(str).str.lower().str.contains("remote", na=False)])
        onsite = len(d) - remote

    return {
        "total_jobs": len(d), 
        "avg_ctc": d[d["parsed_salary"]>0]["parsed_salary"].mean() or 0, 
        "avg_experience": d["min_experience"].mean(), 
        "top_skill": "N/A",
        "remote_count": remote,
        "onsite_count": onsite
    }

@app.get("/companies")
def companies_endpoint(countries: Optional[List[str]] = Query(None), role: Optional[str] = None, exp_min: int = 20, keywords: Optional[str] = None, days_ago: Optional[int] = None):
    d = apply_filters(cached_df, countries, role, exp_min, keywords, days_ago)
    if d.empty or "company_name" not in d.columns: return []
    c = d["company_name"].astype(str).str.title()
    c = c[~c.isin(["Nan", "None", "Confidential"])]
    return [{"company": k, "count": int(v)} for k, v in c.value_counts().head(10).items()]

@app.get("/map-points")
def map_points(countries: Optional[List[str]] = Query(None), role: Optional[str] = None, exp_min: int = 20, keywords: Optional[str] = None, days_ago: Optional[int] = None):
    d = apply_filters(cached_df, countries, role, exp_min, keywords, days_ago)
    if d.empty: return []
    
    # 1. Drop rows without coordinates
    d_coords = d.dropna(subset=['lat', 'lon'])
    
    if d_coords.empty: return []

    # 2. Group by City
    city_counts = d_coords.groupby("city").agg(
        count=("city", "count"),
        lat=("lat", "mean"),
        lon=("lon", "mean")
    ).reset_index()

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
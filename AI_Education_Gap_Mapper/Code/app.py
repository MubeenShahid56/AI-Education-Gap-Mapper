import os
import json
import pickle
import re
import pandas as pd
import numpy as np
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# Paths to assets
BEST_MODEL_PATH = 'models/best_model.pkl'
VECTORIZER_PATH = 'models/vectorizer.pkl'
METRICS_PATH = 'models/metrics.json'
DOMAIN_SKILLS_PATH = 'models/domain_skills.json'
COURSES_PATH = 'courses.json'

# Global variables loaded on startup
model = None
vectorizer = None
metrics = None
domain_skills = None
preloaded_courses = None
all_unique_skills = set()

def load_assets():
    global model, vectorizer, metrics, domain_skills, preloaded_courses, all_unique_skills
    
    # Load Model and Vectorizer
    if os.path.exists(BEST_MODEL_PATH) and os.path.exists(VECTORIZER_PATH):
        with open(BEST_MODEL_PATH, 'rb') as f:
            model = pickle.load(f)
        with open(VECTORIZER_PATH, 'rb') as f:
            vectorizer = pickle.load(f)
        print("Model and vectorizer loaded successfully.")
    else:
        print("WARNING: Model and vectorizer files not found. Run training first.")
        
    # Load Metrics
    if os.path.exists(METRICS_PATH):
        with open(METRICS_PATH, 'r') as f:
            metrics = json.load(f)
    else:
        metrics = {"best_model": "None", "results": {}}
        
    # Load Domain Skills Database
    if os.path.exists(DOMAIN_SKILLS_PATH):
        with open(DOMAIN_SKILLS_PATH, 'r') as f:
            domain_skills = json.load(f)
            # Collect all unique skills in the database
            for domain, skills_list in domain_skills.items():
                for item in skills_list:
                    all_unique_skills.add(item['skill'])
        print(f"Domain skills database loaded. Total unique skills: {len(all_unique_skills)}")
    else:
        domain_skills = {}
        print("WARNING: Domain skills database not found.")
        
    # Load Preloaded Courses
    if os.path.exists(COURSES_PATH):
        with open(COURSES_PATH, 'r') as f:
            preloaded_courses = json.load(f)
    else:
        preloaded_courses = []
        print("WARNING: Preloaded courses not found.")

# Initial load
load_assets()

def extract_skills_from_text(text):
    """
    Extracts known skills from the given text using case-insensitive regex matching.
    """
    text_lower = text.lower()
    extracted = set()
    
    # Sort skills by length descending to match longer multi-word skills first (e.g. "machine learning" before "learning")
    sorted_skills = sorted(list(all_unique_skills), key=len, reverse=True)
    
    for skill in sorted_skills:
        skill_lower = skill.lower()
        # Handle word boundaries safely. 
        # For alphanumeric skills, use word boundaries. For skills with special chars (e.g., C++, .NET), match literally.
        if re.match(r'^[a-zA-Z0-9\s]+$', skill_lower):
            pattern = r'\b' + re.escape(skill_lower) + r'\b'
            if re.search(pattern, text_lower):
                extracted.add(skill)
        else:
            # Simple substring match for special terms like C++, C#, .NET
            if skill_lower in text_lower:
                extracted.add(skill)
                
    return list(extracted)


def _skill_matches_course(skill_name_lower, course_skills_lower):
    for cs in course_skills_lower:
        if cs == skill_name_lower:
            return True
        if skill_name_lower in cs or cs in skill_name_lower:
            return True
        skill_tokens = [token for token in re.split(r'\W+', skill_name_lower) if len(token) > 2]
        if skill_tokens and all(token in cs for token in skill_tokens):
            return True
    return False


def calculate_gap(predicted_domain, course_skills):
    """
    Compares course skills with top industry skills for the predicted domain using weighted coverage.
    """
    if not domain_skills or predicted_domain not in domain_skills:
        return {
            "alignment_score": 0.0,
            "matched_skills": [],
            "missing_skills": [],
            "recommendations": [],
            "total_evaluated": 0,
            "coverable_skills": []
        }

    top_industry_skills = domain_skills[predicted_domain]
    course_skills_lower = [s.lower() for s in course_skills]

    matched = []
    missing = []

    evaluation_pool = top_industry_skills[:20]
    total_weight = sum(item.get('percentage', 0) for item in evaluation_pool) or 1
    matched_weight = 0.0

    for idx, item in enumerate(evaluation_pool):
        skill_name = item.get('skill')
        skill_pct = item.get('percentage', 0)
        skill_name_lower = skill_name.lower() if isinstance(skill_name, str) else ''
        found = _skill_matches_course(skill_name_lower, course_skills_lower)

        skill_info = {
            "rank": idx + 1,
            "skill": skill_name,
            "percentage": skill_pct
        }
        if found:
            matched.append(skill_info)
            matched_weight += skill_pct
        else:
            missing.append(skill_info)

    alignment_score = (matched_weight / total_weight * 100) if total_weight > 0 else 0.0
    top_missing = missing[:5]
    recommendations = [
        {
            "skill": m['skill'],
            "priority": "High" if m['rank'] <= 5 else "Medium",
            "reason": f"Required in {m['percentage']}% of jobs in the {predicted_domain} category (ranked #{m['rank']} overall)."
        }
        for m in top_missing
    ]

    return {
        "alignment_score": round(alignment_score, 1),
        "matched_skills": matched,
        "missing_skills": missing,
        "coverable_skills": [m['skill'] for m in missing],
        "recommendations": recommendations,
        "total_evaluated": len(evaluation_pool)
    }


def best_matching_domain(course_skills):
    """Return the domain in `domain_skills` with highest weighted overlap for the given course skills."""
    if not domain_skills:
        return None

    course_skills_lower = [s.lower() for s in course_skills]
    best_domain = None
    best_score = -1.0

    for domain, skills_list in domain_skills.items():
        evaluation_pool = skills_list[:20]
        total_weight = sum(item.get('percentage', 0) for item in evaluation_pool) or 1
        matched_weight = 0.0
        for item in evaluation_pool:
            skill_name = item.get('skill', '')
            skill_pct = item.get('percentage', 0)
            if _skill_matches_course(skill_name.lower(), course_skills_lower):
                matched_weight += skill_pct

        score = matched_weight / total_weight
        if score > best_score:
            best_score = score
            best_domain = domain

    return best_domain

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/courses', methods=['GET'])
def get_courses():
    return jsonify(preloaded_courses)

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    # Return both raw metrics and a simplified overall accuracy for the selected model.
    response = {
        'best_model': metrics.get('best_model', 'Unknown'),
        'results': metrics.get('results', {}),
        'overall_accuracy': 0.0
    }

    best_model = response['best_model']
    best_stats = response['results'].get(best_model, {})
    if best_stats and isinstance(best_stats.get('accuracy'), (int, float)):
        response['overall_accuracy'] = round(best_stats['accuracy'] * 100, 2)
    return jsonify(response)

@app.route('/api/analyze', methods=['POST'])
def analyze_course():
    data = request.json
    if not data:
        return jsonify({"error": "No input data provided"}), 400
        
    title = data.get('title', 'Untitled Course')
    description = data.get('description', '')
    syllabus = data.get('syllabus', [])
    explicit_skills = data.get('skills', [])
    
    # Combine all text for model prediction and automatic skill extraction
    syllabus_text = " ".join(syllabus) if isinstance(syllabus, list) else str(syllabus)
    combined_text = f"{title} {description} {syllabus_text}"
    
    # 1. Automatically extract skills from the text using keyword matching
    extracted_skills = extract_skills_from_text(combined_text)
    
    # Merge explicit skills with automatically extracted skills
    all_course_skills = list(set(explicit_skills + extracted_skills))
    
    # 2. Predict the domain using the ML model
    # Convert course skills list to a space-separated string for TF-IDF input
    skills_input_str = " ".join([s.replace(',', ' ') for s in all_course_skills])
    
    predicted_domain = None
    prediction_probabilities = {}

    # If the course exactly matches a preloaded course, prefer skill-overlap mapping
    try:
        matched_pre = next((c for c in preloaded_courses if c.get('title') == title or c.get('id') == data.get('id')), None)
    except Exception:
        matched_pre = None

    if matched_pre:
        # Use explicit skills and syllabus to determine best domain
        combined_skills = list(set(matched_pre.get('skills', []) + extracted_skills))
        fb = best_matching_domain(combined_skills)
        if fb:
            predicted_domain = fb

    # Otherwise use ML model if available
    if not predicted_domain and model and vectorizer:
        try:
            # If the course has no skills, use combined text for classification
            features_str = skills_input_str if len(all_course_skills) > 0 else combined_text
            vec = vectorizer.transform([features_str])
            predicted_domain = model.predict(vec)[0]

            # Get probabilities if supported
            if hasattr(model, "predict_proba"):
                probs = model.predict_proba(vec)[0]
                classes = model.classes_
                prediction_probabilities = {classes[i]: round(probs[i] * 100, 1) for i in range(len(classes))}

                # If model is not confident, use the domain with best skill overlap instead
                max_prob = max(probs) if len(probs) > 0 else 0.0
                if max_prob < 0.45:
                    fb = best_matching_domain(all_course_skills)
                    if fb:
                        predicted_domain = fb
        except Exception as e:
            print(f"Error during model prediction: {e}")
    # If predicted domain isn't in our domain_skills DB, pick the best matching domain by overlap
    if not predicted_domain or predicted_domain not in domain_skills:
        fallback = best_matching_domain(all_course_skills)
        if fallback:
            predicted_domain = fallback

    # Display mapping: show broader categories in the UI without changing internal domain used for gap calculations
    DOMAIN_DISPLAY_MAP = {
        'Natural Language Processing': 'Artificial Intelligence',
        'Deep Learning': 'Artificial Intelligence'
    }
    display_domain = DOMAIN_DISPLAY_MAP.get(predicted_domain, predicted_domain)
            
    # 3. Calculate skill gap analysis
    gap_analysis = calculate_gap(predicted_domain, all_course_skills)

    # Build the response payload
    response = {
        "course_title": title,
        # `predicted_domain` for display may be a broader label while gap_analysis used the original domain key
        "predicted_domain": display_domain,
        "internal_domain": predicted_domain,
        "extracted_skills": all_course_skills,
        "gap_analysis": gap_analysis
    }

    # Include prediction probabilities if available
    try:
        if prediction_probabilities:
            response['prediction_probabilities'] = prediction_probabilities
    except NameError:
        pass

    return jsonify(response)

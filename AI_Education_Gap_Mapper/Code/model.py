import pandas as pd
import numpy as np
import pickle
import os
import re
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report

def categorize_job(title):
    title_lower = str(title).lower()
    
    if any(k in title_lower for k in ['deep learning', 'neural network', 'pytorch', 'tensorflow', 'keras']):
        return 'Deep Learning'
    elif any(k in title_lower for k in ['nlp', 'natural language', 'speech', 'text mining', 'translation', 'language model', 'llm', 'bert', 'gpt']):
        return 'Natural Language Processing'
    elif any(k in title_lower for k in ['vision', 'image', 'opencv', 'object detection', 'graphics', 'ocr']):
        return 'Computer Vision'
    elif any(k in title_lower for k in ['machine learning', 'ml ', 'ml-', 'mlops', 'reinforcement learning', 'predictive']):
        return 'Machine Learning'
    elif any(k in title_lower for k in ['data scientist', 'data science', 'statistician', 'statistics', 'quantitative analyst', 'quant']):
        return 'Data Science & Analytics'
    elif any(k in title_lower for k in ['software', 'developer', 'engineer', 'architect', 'devops', 'backend', 'frontend', 'full stack', 'cloud', 'systems']):
        return 'Software Engineering & Infrastructure'
    elif any(k in title_lower for k in ['data analyst', 'business analyst', 'bi analyst', 'analytics engineer', 'data specialist']):
        return 'Data Analytics'
    else:
        return 'Other CS/IT'

def train_and_evaluate():
    print("Loading filtered job skills data...")
    if not os.path.exists('ai_job_skills.csv'):
        raise FileNotFoundError("ai_job_skills.csv not found! Run the filtering script first.")
        
    df = pd.read_csv('ai_job_skills.csv')
    print(f"Loaded {len(df)} job listings.")
    
    # Categorize job listings
    df['domain'] = df['job_title'].apply(categorize_job)
    print("\nJob domain distribution:")
    print(df['domain'].value_counts())
    
    # Drop rows that are classified as 'Other CS/IT' or have missing skills
    df = df[df['domain'] != 'Other CS/IT']
    df = df.dropna(subset=['job_skills', 'domain'])
    
    print(f"\nFinal dataset size for training: {len(df)} listings.")
    
    # Clean the job skills strings to serve as text features
    # Skills are comma-separated. We replace commas with spaces to treat it as a bag of words/skills.
    df['skills_text'] = df['job_skills'].apply(lambda x: str(x).replace(',', ' '))
    
    X = df['skills_text']
    y = df['domain']
    
    # Split the dataset
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Vectorize text features using TF-IDF
    # We use sublinear TF scaling and limit vocabulary to top 5000 terms
    vectorizer = TfidfVectorizer(max_features=5000, stop_words='english', sublinear_tf=True)
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)
    
    print("\nTraining and evaluating models...")
    
    models = {
        'Naive Bayes': MultinomialNB(),
        'Decision Tree': DecisionTreeClassifier(max_depth=20, random_state=42),
        'Random Forest': RandomForestClassifier(n_estimators=100, max_depth=25, random_state=42, n_jobs=-1)
    }
    
    results = {}
    best_model_name = None
    best_f1 = -1
    best_model = None
    
    for name, model in models.items():
        print(f"\n--- Training {name} ---")
        model.fit(X_train_vec, y_train)
        y_pred = model.predict(X_test_vec)
        
        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision, recall, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='weighted', zero_division=0)
        
        results[name] = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1
        }
        
        print(f"Accuracy:  {accuracy:.4f}")
        print(f"Precision: {precision:.4f}")
        print(f"Recall:    {recall:.4f}")
        print(f"F1-Score:  {f1:.4f}")
        
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred, zero_division=0))
        
        if f1 > best_f1:
            best_f1 = f1
            best_model_name = name
            best_model = model
            
    print(f"\nBest model based on weighted F1-Score: {best_model_name} ({best_f1:.4f})")
    
    # Save the best model, vectorizer, and evaluation results
    print("Saving the best model and vectorizer...")
    os.makedirs('models', exist_ok=True)
    with open('models/best_model.pkl', 'wb') as f:
        pickle.dump(best_model, f)
    with open('models/vectorizer.pkl', 'wb') as f:
        pickle.dump(vectorizer, f)
        
    # Save the metrics to a JSON file for the dashboard
    import json
    metrics_summary = {
        'best_model': best_model_name,
        'results': results
    }
    with open('models/metrics.json', 'w') as f:
        json.dump(metrics_summary, f, indent=4)
        
    print("Model assets saved successfully.")
    
    # Identify top skills per domain to save as reference database
    print("\nExtracting top industry skills per domain...")
    domain_skills_db = {}
    for domain in df['domain'].unique():
        domain_df = df[df['domain'] == domain]
        # Split all skills and count frequencies
        all_skills = []
        for skills_str in domain_df['job_skills']:
            skills = [s.strip() for s in str(skills_str).split(',') if s.strip()]
            all_skills.extend(skills)
            
        skill_counts = pd.Series(all_skills).value_counts()
        total_jobs_in_domain = len(domain_df)
        
        # Keep top 50 skills with frequency and percentage
        top_skills = []
        for skill, count in skill_counts.head(50).items():
            top_skills.append({
                'skill': skill,
                'count': int(count),
                'percentage': round((count / total_jobs_in_domain) * 100, 2)
            })
            
        domain_skills_db[domain] = top_skills
        
    with open('models/domain_skills.json', 'w') as f:
        json.dump(domain_skills_db, f, indent=4)
    print("Domain skills database saved successfully.")

if __name__ == '__main__':
    train_and_evaluate()

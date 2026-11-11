# AI Education Gap Mapper

An advanced Educational Technology system that uses Machine Learning techniques (Naive Bayes, Decision Tree, and Random Forest) to analyze university course outlines, compare them against industry job requirements, and identify missing or weakly covered skills to improve curriculum alignment.

## 🚀 Key Features

- **Preloaded Syllabi Database:** Includes standard university courses (e.g., Intro to AI, Machine Learning, Deep Learning, NLP, Computer Vision, Data Engineering, Software Engineering) as benchmark syllabi.
- **Custom Syllabus Analyzer:** Allows users to input any custom course title, description, and weekly topics to analyze curriculum gaps in real time.
- **Machine Learning Domain Classifier:** Auto-classifies the course syllabus into one of the core computer science/AI domains using a trained **Random Forest Classifier** (achieving **90.64%** accuracy).
- **Curriculum Alignment Score:** Calculates a percentage-based score indicating how well a syllabus covers the top 20 skills demanded by employers in that domain.
- **Interactive Visual Dashboard:** Displays bar charts of industry demand vs. course coverage, alignment progress rings, and classification probability breakdowns.
- **Actionable Gap Recommendations:** Provides priority-ranked recommendations ("High" or "Medium") suggesting specific technologies, tools, or concepts to add to the syllabus.

---

## 🛠️ Project Architecture

```
.
├── ai_job_skills.csv          # Filtered AI/CS job requirements dataset (14,100 listings)
├── AI_Education_Gap_Mapper.ipynb # Jupyter Notebook for step-by-step model exploration
├── app.py                     # Flask backend API serving the analysis & predictions
├── courses.json               # Preloaded university courses database
├── model.py                   # Machine Learning model training & evaluation script
├── run.py                     # App execution launcher script (auto-manages venv)
├── README.md                  # Comprehensive documentation
├── models/                    # Pickled models, vectorizer, and domain skills data
│   ├── best_model.pkl
│   ├── vectorizer.pkl
│   ├── metrics.json
│   └── domain_skills.json
├── static/                    # Frontend styling & client-side logic
│   ├── css/
│   │   └── style.css          # Premium vanilla CSS stylesheet (dark mode)
│   └── js/
│       └── dashboard.js       # Client controller logic (Chart.js & animations)
└── templates/
    └── index.html             # Main dashboard UI
```

---

## 📈 Evaluation Metrics & Model Comparison

We compared three classification algorithms using standard metrics: **Accuracy, Precision, Recall, and F1-Score (Weighted)**.

| Algorithm | Accuracy | Precision | Recall | F1-Score | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Naive Bayes** | 89.18% | 87.75% | 89.18% | 87.85% | Evaluated |
| **Decision Tree** | 86.74% | 86.49% | 86.74% | 86.55% | Evaluated |
| **Random Forest** | **90.64%** | **89.92%** | **90.64%** | **89.78%** | **Selected** |

*Note: The Random Forest Classifier was chosen as the primary backend predictor due to its superior performance.*

---

## ⚙️ Quick Start

### 1. Prerequisites
Make sure you have **Python 3.8+** installed. The project runs in a localized virtual environment.

### 2. Launch the Web App
Simply run the launcher script:
```bash
python3 run.py
```
This script will automatically detect and execute inside the `.venv` virtual environment. 
- Open your browser and navigate to: **`http://localhost:5000`**

### 3. Run the Jupyter Notebook
To explore the training, evaluation, and visualizations interactively:
```bash
# Activate virtual environment
source .venv/bin/activate

# Launch Jupyter Notebook
jupyter notebook AI_Education_Gap_Mapper.ipynb
```

---

## ⚠️ Limitations & Future Work

1. **Syllabus Detail Dependency:** Accuracy depends on how detailed the course outline is. Short or vague descriptions might yield incomplete skill extractions.
2. **Temporal Shifts in Tech:** Industry demands change rapidly. The dataset must be updated regularly to capture new frameworks (e.g., LLMs, LangChain, vector databases).
3. **Soft Skills Gap:** The current system is optimized for technical skills (programming languages, libraries, algorithms) and does not map soft skills (teamwork, leadership) effectively.

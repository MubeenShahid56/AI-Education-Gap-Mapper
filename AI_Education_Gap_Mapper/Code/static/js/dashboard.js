// AI Education Gap Mapper - Frontend Dashboard JavaScript

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const preloadedSelect = document.getElementById('preloaded-select');
    const syllabusForm = document.getElementById('syllabus-form');
    const courseTitleInput = document.getElementById('course-title');
    const courseDescInput = document.getElementById('course-description');
    const syllabusWeeksInput = document.getElementById('syllabus-weeks');
    const analyzeBtn = document.getElementById('analyze-btn');
    const btnContent = analyzeBtn.querySelector('.btn-content');
    const loaderSpinner = analyzeBtn.querySelector('.loader-spinner');
    
    const welcomeState = document.getElementById('welcome-state');
    const analysisResults = document.getElementById('analysis-results');
    const resultsCard = document.getElementById('results-card');
    
    // Results DOM Elements
    const resTitle = document.getElementById('res-course-title');
    const resPredictedDomain = document.getElementById('res-predicted-domain');
    const resAlignmentPct = document.getElementById('res-alignment-pct');
    const scoreRing = document.getElementById('score-ring');
    const statCovered = document.getElementById('stat-covered-count');
    const statMissing = document.getElementById('stat-missing-count');
    const recommendationsList = document.getElementById('recommendations-list');
    const extractedSkillsCloud = document.getElementById('extracted-skills-cloud');
    
    // Tab Elements
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    // Global Chart instances to destroy before recreating
    let skillsChartInstance = null;
    let metricsChartInstance = null;
    
    // Progress Ring Circumference
    const ringRadius = 40;
    const ringCircumference = 2 * Math.PI * ringRadius;
    scoreRing.style.strokeDasharray = `${ringCircumference} ${ringCircumference}`;
    scoreRing.style.strokeDashoffset = ringCircumference;
    
    // Preloaded courses list
    let coursesData = [];

    // Initialize Page
    initDashboard();

    function initDashboard() {
        // Fetch Preloaded Courses
        fetch('/api/courses')
            .then(res => res.json())
            .then(data => {
                coursesData = data;
                populatePreloadedDropdown(data);
            })
            .catch(err => console.error("Error fetching preloaded courses:", err));

        // Fetch Model Metrics
        fetch('/api/metrics')
            .then(res => res.json())
            .then(data => {
                renderModelMetrics(data);
            })
            .catch(err => console.error("Error fetching model metrics:", err));

        // Event Listeners
        preloadedSelect.addEventListener('change', handlePreloadedChange);
        syllabusForm.addEventListener('submit', handleFormSubmit);
        setupTabs();
        setupNavigation();
    }

    // Populate dropdown with standard courses
    function populatePreloadedDropdown(courses) {
        courses.forEach(course => {
            const option = document.createElement('option');
            option.value = course.id;
            option.textContent = `${course.code}: ${course.title}`;
            preloadedSelect.appendChild(option);
        });
    }

    // Handle dropdown selection
    function handlePreloadedChange(e) {
        const selectedId = e.target.value;
        const selectedCourse = coursesData.find(c => c.id === selectedId);
        
        if (selectedCourse) {
            courseTitleInput.value = selectedCourse.title;
            courseDescInput.value = selectedCourse.description;
            
            // Set weekly topics with newline separation
            if (Array.isArray(selectedCourse.syllabus)) {
                syllabusWeeksInput.value = selectedCourse.syllabus.join('\n');
            } else {
                syllabusWeeksInput.value = selectedCourse.syllabus || '';
            }
            
                // Do NOT automatically submit form to avoid unexpected graph updates.
                // User must press the "Analyze Curriculum Gap" button to run analysis.
                // If you prefer auto-analysis, uncomment the code below.
                /*
                analyzeCurriculum({
                    title: selectedCourse.title,
                    description: selectedCourse.description,
                    syllabus: Array.isArray(selectedCourse.syllabus) ? selectedCourse.syllabus : selectedCourse.syllabus.split('\n'),
                    skills: selectedCourse.skills || []
                });
                */
        }
    }

    // Form submission handler
    function handleFormSubmit(e) {
        e.preventDefault();
        
        const title = courseTitleInput.value.trim();
        const description = courseDescInput.value.trim();
        const syllabusText = syllabusWeeksInput.value.trim();
        const syllabus = syllabusText.split('\n').map(line => line.trim()).filter(line => line.length > 0);
        
        if (!title || !description || syllabus.length === 0) return;
        
        analyzeCurriculum({
            title,
            description,
            syllabus,
            skills: [] // Custom user courses don't have preloaded explicit skills
        });
    }

    // Perform analysis API call
    function analyzeCurriculum(payload) {
        // Show loading state
        analyzeBtn.disabled = true;
        btnContent.classList.add('hidden');
        loaderSpinner.classList.remove('hidden');
        
        fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(result => {
            renderAnalysisResults(result);
            
            // Scroll to results on mobile / tablet
            if (window.innerWidth <= 1024) {
                resultsCard.scrollIntoView({ behavior: 'smooth' });
            }
        })
        .catch(err => {
            console.error("Analysis failed:", err);
            alert("An error occurred during curriculum analysis. Please try again.");
        })
        .finally(() => {
            // Reset button loading state
            analyzeBtn.disabled = false;
            btnContent.classList.remove('hidden');
            loaderSpinner.classList.add('hidden');
        });
    }

    // Render results on the UI
    function renderAnalysisResults(data) {
        // Hide welcome state, show results
        welcomeState.classList.add('hidden');
        analysisResults.classList.remove('hidden');
        
        // Populate header details
        resTitle.textContent = data.course_title;
        resPredictedDomain.textContent = data.predicted_domain;
        
        // Animate circular alignment score
        const score = data.gap_analysis.alignment_score;
        animateAlignmentScore(score);
        
        // Populate stats count
        const matchedCount = data.gap_analysis.matched_skills.length;
        const missingCount = data.gap_analysis.missing_skills.length;
        statCovered.textContent = matchedCount;
        statMissing.textContent = missingCount;
        
        // Update tab header counter for extracted skills
        const extractedTabBtn = document.querySelector('[data-tab="tab-extracted"]');
        extractedTabBtn.innerHTML = `<i class="fa-solid fa-microchip"></i> Covered Skills (${data.extracted_skills.length})`;
        
        // Render horizontal bar chart of skills
        renderSkillsChart(data.gap_analysis.matched_skills, data.gap_analysis.missing_skills, data.predicted_domain);
        
        // Render Actionable Gap Plan
        renderRecommendations(data.gap_analysis.recommendations);
        
        // Render Extracted Skills Cloud
        renderSkillsCloud(data.extracted_skills, data.gap_analysis.matched_skills);
    }

    // Circular progress animation
    function animateAlignmentScore(targetPercent) {
        let currentPercent = 0;
        const duration = 800; // ms
        const intervalTime = 10; // ms
        const step = targetPercent / (duration / intervalTime);
        
        const timer = setInterval(() => {
            currentPercent += step;
            if (currentPercent >= targetPercent) {
                currentPercent = targetPercent;
                clearInterval(timer);
            }
            
            // Set text label
            resAlignmentPct.textContent = Math.round(currentPercent);
            
            // Set circle progress offset
            const offset = ringCircumference - (currentPercent / 100) * ringCircumference;
            scoreRing.style.strokeDashoffset = offset;
        }, intervalTime);
    }

    // Render skills comparison chart using Chart.js
    function renderSkillsChart(matched, missing, domainName) {
        if (skillsChartInstance) {
            skillsChartInstance.destroy();
        }
        
        // Combine matched and missing into a single ordered list
        // Top skills sorted by relevance (percentage)
        const allSkills = [...matched, ...missing].sort((a, b) => b.percentage - a.percentage);
        
        const labels = allSkills.map(item => item.skill);
        const dataValues = allSkills.map(item => item.percentage);
        
        // Check coverage status to assign color
        const backgroundColors = allSkills.map(item => {
            const isMatched = matched.some(m => m.skill.toLowerCase() === item.skill.toLowerCase());
            return isMatched 
                ? 'rgba(16, 185, 129, 0.7)' // Emerald Green (Matched)
                : 'rgba(239, 68, 68, 0.45)'; // Crimson/Red (Missing)
        });
        
        const borderColors = allSkills.map(item => {
            const isMatched = matched.some(m => m.skill.toLowerCase() === item.skill.toLowerCase());
            return isMatched ? '#10b981' : '#ef4444';
        });

        const ctx = document.getElementById('skillsChart').getContext('2d');
        skillsChartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Employer Demand %',
                    data: dataValues,
                    backgroundColor: backgroundColors,
                    borderColor: borderColors,
                    borderWidth: 1.5,
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const skillName = context.label;
                                const isMatched = matched.some(m => m.skill.toLowerCase() === skillName.toLowerCase());
                                const status = isMatched ? "Covered" : "Missing";
                                return `Demand: ${context.raw}% | Status: ${status}`;
                            }
                        },
                        backgroundColor: '#111827',
                        titleFont: { family: 'Inter', size: 12 },
                        bodyFont: { family: 'Inter', size: 12 },
                        padding: 10,
                        borderColor: 'rgba(255,255,255,0.1)',
                        borderWidth: 1
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)'
                        },
                        ticks: {
                            color: '#9ca3af',
                            font: { family: 'Inter', size: 10 },
                            callback: value => `${value}%`
                        },
                        title: {
                            display: true,
                            text: 'Job Frequency Percentage',
                            color: '#9ca3af',
                            font: { family: 'Inter', size: 11 }
                        },
                        max: 100
                    },
                    y: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: '#f3f4f6',
                            font: { family: 'Outfit', size: 11, weight: '500' }
                        }
                    }
                }
            }
        });
    }

    // Render action plans (recommendations)
    function renderRecommendations(recs) {
        recommendationsList.innerHTML = '';
        
        if (recs.length === 0) {
            recommendationsList.innerHTML = `
                <div class="empty-recs">
                    <i class="fa-solid fa-circle-check text-success" style="font-size: 2rem; margin-bottom: 0.5rem;"></i>
                    <p><strong>Perfect alignment!</strong> No major curriculum gaps detected for this domain. The course covers all primary industry-requested skills.</p>
                </div>
            `;
            return;
        }
        
        recs.forEach(rec => {
            const item = document.createElement('div');
            const priorityClass = rec.priority === 'High' ? 'priority-high' : 'priority-medium';
            const badgeClass = rec.priority === 'High' ? 'rec-badge-high' : 'rec-badge-medium';
            
            item.className = `rec-item ${priorityClass}`;
            item.innerHTML = `
                <div class="rec-icon">
                    <i class="fa-solid ${rec.priority === 'High' ? 'fa-triangle-exclamation' : 'fa-circle-info'}"></i>
                </div>
                <div class="rec-content">
                    <h5>Add topic: <strong>${rec.skill}</strong></h5>
                    <p>${rec.reason}</p>
                </div>
                <div>
                    <span class="rec-badge ${badgeClass}">${rec.priority} Priority</span>
                </div>
            `;
            recommendationsList.appendChild(item);
        });
    }

    // Render extracted skills cloud
    function renderSkillsCloud(skills, matchedSkills) {
        extractedSkillsCloud.innerHTML = '';
        
        if (skills.length === 0) {
            extractedSkillsCloud.innerHTML = `<p class="label-muted">No specific technology skills detected. Add detailed week summaries or topics to improve extraction accuracy.</p>`;
            return;
        }
        
        // Sort skills alphabetically
        skills.sort().forEach(skill => {
            const pill = document.createElement('span');
            pill.className = 'skill-pill';
            
            // Check if this extracted skill is one of the top industry skills
            const isIndustryReq = matchedSkills.some(m => m.skill.toLowerCase() === skill.toLowerCase());
            
            if (isIndustryReq) {
                pill.innerHTML = `<i class="fa-solid fa-circle-check text-success"></i> ${skill}`;
                pill.style.borderColor = 'rgba(16, 185, 129, 0.3)';
                pill.style.background = 'rgba(16, 185, 129, 0.05)';
            } else {
                pill.innerHTML = `<i class="fa-solid fa-cube text-primary"></i> ${skill}`;
            }
            extractedSkillsCloud.appendChild(pill);
        });
    }

    // Render Model Evaluation Summary (only overall accuracy)
    function renderModelMetrics(data) {
        const summaryEl = document.getElementById('metrics-overall');
        if (!summaryEl) return;
        const overall = data && data.overall_accuracy ? data.overall_accuracy : null;
        summaryEl.textContent = overall !== null ? `Overall Accuracy: ${overall}%` : 'Overall Accuracy: --%';
    }

    // Set up interactive tabs inside results card
    function setupTabs() {
        tabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const targetTab = btn.getAttribute('data-tab');
                
                // Toggle active tab buttons
                tabBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                // Toggle active tab content
                tabContents.forEach(content => {
                    if (content.id === targetTab) {
                        content.classList.add('active');
                    } else {
                        content.classList.remove('active');
                    }
                });
            });
        });
    }

    // Set up smooth single-page navigation highlight
    function setupNavigation() {
        const navLinks = document.querySelectorAll('.nav-link');
        
        window.addEventListener('scroll', () => {
            let currentSec = 'analyzer';
            const scrollPos = window.scrollY + 150;
            
            document.querySelectorAll('section').forEach(sec => {
                const secTop = sec.offsetTop;
                const secHeight = sec.offsetHeight;
                
                if (scrollPos >= secTop && scrollPos < secTop + secHeight) {
                    currentSec = sec.getAttribute('id');
                }
            });
            
            navLinks.forEach(link => {
                link.classList.remove('active');
                if (link.getAttribute('href') === `#${currentSec}`) {
                    link.classList.add('active');
                }
            });
        });
    }
});

"""Add an expanded, repeatable synthetic dataset for a MentorMatch presentation."""

from app.scripts import seed_demo_data as base


base.FACULTY.extend([
    {"name": "Dr. Leena Kapoor", "email": "demo.leena.kapoor@example.edu", "department": "Computer Science"},
    {"name": "Dr. Arjun Bose", "email": "demo.arjun.bose@example.edu", "department": "Environmental Science"},
    {"name": "Dr. Farah Qureshi", "email": "demo.farah.qureshi@example.edu", "department": "Electrical Engineering"},
    {"name": "Dr. Rohan Desai", "email": "demo.rohan.desai@example.edu", "department": "Computer Science"},
])

base.STUDENTS.extend([
    {"name": "Ishaan Kulkarni", "email": "demo.ishaan.kulkarni@example.edu", "department": "Computer Science"},
    {"name": "Meera Thomas", "email": "demo.meera.thomas@example.edu", "department": "Environmental Science"},
    {"name": "Kabir Shah", "email": "demo.kabir.shah@example.edu", "department": "Electrical Engineering"},
    {"name": "Ananya Reddy", "email": "demo.ananya.reddy@example.edu", "department": "Computer Science"},
    {"name": "Vihaan Sethi", "email": "demo.vihaan.sethi@example.edu", "department": "Environmental Science"},
    {"name": "Sana Malik", "email": "demo.sana.malik@example.edu", "department": "Electrical Engineering"},
    {"name": "Aditya Menon", "email": "demo.aditya.menon@example.edu", "department": "Computer Science"},
    {"name": "Riya Chatterjee", "email": "demo.riya.chatterjee@example.edu", "department": "Environmental Science"},
    {"name": "Arnav Bhat", "email": "demo.arnav.bhat@example.edu", "department": "Electrical Engineering"},
    {"name": "Pooja Nambiar", "email": "demo.pooja.nambiar@example.edu", "department": "Computer Science"},
    {"name": "Rehan Siddiqui", "email": "demo.rehan.siddiqui@example.edu", "department": "Environmental Science"},
    {"name": "Tara Krishnan", "email": "demo.tara.krishnan@example.edu", "department": "Electrical Engineering"},
])

base.PROJECTS.extend([
    {
        "key": "regional-language-tools", "title": "Language Technology for Regional Languages",
        "faculty": "demo.leena.kapoor@example.edu", "department": "Computer Science",
        "description": "Evaluate multilingual language models and data collection approaches for regional languages with limited digital resources. The work includes careful text curation, baseline comparisons, and documenting coverage and bias limitations.",
        "skills": ["NLP", "Python", "language models", "data curation", "responsible AI"],
    },
    {
        "key": "campus-network-anomalies", "title": "Early Detection of Campus Network Anomalies",
        "faculty": "demo.leena.kapoor@example.edu", "department": "Computer Science",
        "description": "Analyze anonymized network-flow records to identify unusual traffic patterns and evaluate interpretable detection methods. Students will focus on reproducible experiments, privacy-aware handling, and practical false-positive analysis.",
        "skills": ["cybersecurity", "Python", "anomaly detection", "networks", "data analysis"],
    },
    {
        "key": "neighbourhood-heat", "title": "Mapping Neighbourhood Urban Heat Risk",
        "faculty": "demo.arjun.bose@example.edu", "department": "Environmental Science",
        "description": "Combine public weather observations, land-cover maps, and field measurements to understand neighbourhood-scale heat exposure. The team will assess canopy cover and prepare evidence for community cooling strategies.",
        "skills": ["GIS", "climate science", "field research", "statistics", "remote sensing"],
    },
    {
        "key": "wetland-soundscapes", "title": "Biodiversity Monitoring Through Wetland Soundscapes",
        "faculty": "demo.arjun.bose@example.edu", "department": "Environmental Science",
        "description": "Study seasonal changes in wetland recordings and test practical methods for identifying bird and amphibian activity. The project combines ecological interpretation with careful annotation and reproducible audio analysis.",
        "skills": ["ecology", "bioacoustics", "Python", "field methods", "data annotation"],
    },
    {
        "key": "battery-health", "title": "Battery Health Prediction for Campus Energy Storage",
        "faculty": "demo.farah.qureshi@example.edu", "department": "Electrical Engineering",
        "description": "Use laboratory cycling data to estimate battery state of health and identify operating conditions associated with faster degradation. Compare transparent regression models and validate predictions across cells and test runs.",
        "skills": ["electrical engineering", "Python", "battery systems", "signal processing", "machine learning"],
    },
    {
        "key": "campus-microgrid", "title": "Control Strategies for a Solar Campus Microgrid",
        "faculty": "demo.farah.qureshi@example.edu", "department": "Electrical Engineering",
        "description": "Model a campus microgrid with solar generation, storage, and variable demand. Compare scheduling policies for balancing reliability, cost, and renewable energy use under realistic operating constraints.",
        "skills": ["power systems", "optimization", "MATLAB", "renewable energy", "control systems"],
    },
    {
        "key": "transaction-graphs", "title": "Graph Methods for Detecting Transaction Fraud",
        "faculty": "demo.rohan.desai@example.edu", "department": "Computer Science",
        "description": "Explore how relationships among anonymized transactions can improve suspicious-activity detection. Compare graph features with standard baselines and evaluate precision, recall, and explainability on imbalanced data.",
        "skills": ["graph machine learning", "Python", "data mining", "statistics", "model evaluation"],
    },
    {
        "key": "accessible-indoor-navigation", "title": "Visual Cues for Accessible Indoor Navigation",
        "faculty": "demo.rohan.desai@example.edu", "department": "Computer Science",
        "description": "Prototype computer-vision methods that recognize useful indoor landmarks for accessible navigation. Focus on privacy-conscious image capture, robust performance across lighting conditions, and user-centred evaluation.",
        "skills": ["computer vision", "accessibility", "Python", "mobile systems", "user research"],
    },
])

base.INTERESTS.extend([
    {"key": "ishaan-regional-nlp", "student": "demo.ishaan.kulkarni@example.edu", "description": "I enjoy natural language processing and want to build language tools that work well for regional communities. I am especially interested in multilingual models, responsible data collection, and careful evaluation.", "skills": ["NLP", "Python", "language models", "responsible AI"]},
    {"key": "meera-wetlands", "student": "demo.meera.thomas@example.edu", "description": "I am interested in wetland ecology, biodiversity, and field-based monitoring. I would like to combine ecological observations with sound recordings and learn reproducible environmental research methods.", "skills": ["ecology", "field research", "bioacoustics", "statistics"]},
    {"key": "kabir-batteries", "student": "demo.kabir.shah@example.edu", "description": "My interests are power electronics, batteries, and reliable renewable energy. I would like to analyze engineering measurements and understand how storage can support a resilient grid.", "skills": ["electrical engineering", "battery systems", "Python", "signal processing"]},
    {"key": "ananya-security", "student": "demo.ananya.reddy@example.edu", "description": "I want to study practical cybersecurity and machine learning, especially methods that help analysts understand unusual network behaviour without excessive false alarms.", "skills": ["cybersecurity", "networks", "Python", "machine learning"]},
    {"key": "vihaan-climate", "student": "demo.vihaan.sethi@example.edu", "description": "I am interested in climate adaptation, urban heat, and how parks and tree cover affect public health. I want to develop stronger GIS and field research skills.", "skills": ["climate science", "GIS", "remote sensing", "field research"]},
    {"key": "sana-microgrid", "student": "demo.sana.malik@example.edu", "description": "I am curious about renewable power systems and how control decisions affect reliability and cost. I enjoy modelling solar, storage, and demand data.", "skills": ["power systems", "optimization", "MATLAB", "renewable energy"]},
    {"key": "aditya-graphs", "student": "demo.aditya.menon@example.edu", "description": "I am interested in data mining and graph algorithms. I would like to learn how relationships in large datasets reveal patterns through transparent, reproducible analysis.", "skills": ["Python", "graph algorithms", "data mining", "statistics"]},
    {"key": "riya-river-data", "student": "demo.riya.chatterjee@example.edu", "description": "I care about freshwater ecosystems and pollution monitoring. I am interested in analysing sensor and field data, communicating uncertainty, and connecting results to environmental decisions.", "skills": ["water quality", "environmental science", "statistics", "Python"]},
    {"key": "arnav-energy-storage", "student": "demo.arnav.bhat@example.edu", "description": "I want to work on battery management and predictive maintenance for energy systems. I have a foundation in circuits and programming and want to improve my modelling skills.", "skills": ["battery systems", "circuits", "Python", "machine learning"]},
    {"key": "pooja-accessibility", "student": "demo.pooja.nambiar@example.edu", "description": "I am interested in accessible technology and computer vision. I want to design assistive systems with user research, privacy protections, and robust real-world performance.", "skills": ["accessibility", "computer vision", "Python", "user research"]},
    {"key": "rehan-air-quality", "student": "demo.rehan.siddiqui@example.edu", "description": "I am interested in air pollution, urban environments, and public data. I want to combine sensors, maps, and weather observations to understand exposure across neighbourhoods.", "skills": ["air quality", "GIS", "sensor data", "environmental monitoring"]},
    {"key": "tara-freshwater", "student": "demo.tara.krishnan@example.edu", "description": "I would like to study freshwater pollution and practical laboratory methods for measuring microplastics. I am interested in careful sampling, microscopy, and statistics.", "skills": ["water quality", "microscopy", "environmental chemistry", "statistics"]},
])

base.APPLICATIONS.extend([
    {"student": "demo.ishaan.kulkarni@example.edu", "project": "regional-language-tools", "decision": base.ApplicationStatus.ACCEPTED, "message": "My NLP coursework and interest in regional language technology align with evaluating multilingual models and documenting their limitations."},
    {"student": "demo.ishaan.kulkarni@example.edu", "project": "transaction-graphs", "decision": None, "message": "I have used Python for graph algorithms and would like to explore relational features for detecting suspicious activity."},
    {"student": "demo.meera.thomas@example.edu", "project": "wetland-soundscapes", "decision": None, "message": "I have experience with ecology field assignments and would be excited to help annotate recordings and interpret biodiversity patterns."},
    {"student": "demo.meera.thomas@example.edu", "project": "water-quality", "decision": base.ApplicationStatus.PENDING, "message": "I would like to learn how river measurements and rainfall records support reliable environmental analysis."},
    {"student": "demo.kabir.shah@example.edu", "project": "battery-health", "decision": base.ApplicationStatus.ACCEPTED, "message": "My circuits and programming background would help me contribute to battery data analysis and model validation."},
    {"student": "demo.kabir.shah@example.edu", "project": "campus-microgrid", "decision": None, "message": "I would like to learn how storage and generation forecasts inform practical microgrid control decisions."},
    {"student": "demo.ananya.reddy@example.edu", "project": "campus-network-anomalies", "decision": None, "message": "I am interested in privacy-aware security research and can contribute Python skills to reproducible anomaly detection experiments."},
    {"student": "demo.ananya.reddy@example.edu", "project": "transaction-graphs", "decision": base.ApplicationStatus.PENDING, "message": "I would like to compare network-based detection methods and evaluate false positives in imbalanced data."},
    {"student": "demo.vihaan.sethi@example.edu", "project": "neighbourhood-heat", "decision": base.ApplicationStatus.ACCEPTED, "message": "My GIS coursework and interest in climate adaptation fit the neighbourhood mapping and field measurement work."},
    {"student": "demo.vihaan.sethi@example.edu", "project": "crop-disease", "decision": None, "message": "I am interested in how image analysis can support practical agricultural monitoring."},
    {"student": "demo.sana.malik@example.edu", "project": "campus-microgrid", "decision": None, "message": "My power systems coursework and modelling experience would help compare microgrid control policies."},
    {"student": "demo.sana.malik@example.edu", "project": "solar-forecasting", "decision": base.ApplicationStatus.PENDING, "message": "I am interested in combining weather and generation data to support renewable energy planning."},
    {"student": "demo.aditya.menon@example.edu", "project": "transaction-graphs", "decision": base.ApplicationStatus.ACCEPTED, "message": "I have worked with graph algorithms and would like to apply them to interpretable transaction-network analysis."},
    {"student": "demo.aditya.menon@example.edu", "project": "smart-traffic", "decision": None, "message": "I am interested in simulation and optimization and would like to help evaluate adaptive signal strategies."},
    {"student": "demo.riya.chatterjee@example.edu", "project": "water-quality", "decision": None, "message": "My environmental data interests align with analysing river measurements and communicating uncertainty."},
    {"student": "demo.riya.chatterjee@example.edu", "project": "wetland-soundscapes", "decision": base.ApplicationStatus.PENDING, "message": "I would like to contribute field observations and learn reproducible methods for biodiversity monitoring."},
    {"student": "demo.arnav.bhat@example.edu", "project": "battery-health", "decision": None, "message": "I can contribute programming and electronics coursework to analysing battery cycling data."},
    {"student": "demo.arnav.bhat@example.edu", "project": "solar-forecasting", "decision": base.ApplicationStatus.REJECTED, "message": "I am interested in renewable power and would value experience with forecasting and engineering measurements."},
    {"student": "demo.pooja.nambiar@example.edu", "project": "accessible-indoor-navigation", "decision": base.ApplicationStatus.ACCEPTED, "message": "My accessibility coursework and computer vision experience fit the project’s focus on robust, user-centred navigation."},
    {"student": "demo.pooja.nambiar@example.edu", "project": "medical-imaging", "decision": None, "message": "I would like to learn how interpretable computer vision methods are evaluated in sensitive applications."},
    {"student": "demo.rehan.siddiqui@example.edu", "project": "water-quality", "decision": None, "message": "I am interested in combining environmental sensor and weather data to understand local exposure patterns."},
    {"student": "demo.rehan.siddiqui@example.edu", "project": "neighbourhood-heat", "decision": base.ApplicationStatus.PENDING, "message": "I can contribute GIS and environmental monitoring skills to mapping heat risk."},
    {"student": "demo.tara.krishnan@example.edu", "project": "crop-disease", "decision": base.ApplicationStatus.ACCEPTED, "message": "My laboratory coursework and interest in environmental science fit the project’s field research and evaluation work."},
    {"student": "demo.tara.krishnan@example.edu", "project": "water-quality", "decision": None, "message": "I would like to learn how field measurements and sensor records support water-quality analysis."},
])


if __name__ == "__main__":
    counts = base.seed()
    print("Expanded demo seed completed:", counts)

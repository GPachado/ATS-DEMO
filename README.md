# ATS System Demo

## Introduction
This repository contains a basic implementation of an ATS (Applicant Tracking System) designed to filter and rank candidates based on skills, experience, and a semantic match with job descriptions. The application uses an SQLite database and a sentence embedding model to enhance candidate-job matching accuracy.

## Files in the Repository
- **build_db.py**: Initializes the SQLite database and manages embeddings with the embedding manager.
- **populate_db.py**: Populates the database with preloaded candidate data.
- **ats_system.py**: Contains core functionality for managing the ATS, including filtering, ranking, and generating match explanations.
- **app.py**: Sets up a Flask API endpoint for the ATS system.
- **main.py**: Demonstrates usage of the ATS system with a mock example without a frontend.

---

## File Overview

### `ats_system.py`
This script defines the primary logic and classes for the ATS, including:

- **Environment Setup**: Sets `CURL_CA_BUNDLE` to an empty string.
- **Data Models**: Defines data classes for `Experience`, `Education`, `Candidate`, and `Job`.
- **Skill Enrichment**: Adds related skills for enhanced candidate matching.
- **ATS System**: Provides candidate filtering, skill matching, and ranking based on skills and semantic similarity with job descriptions.

**Classes and Methods**:
- **Experience, Education, Candidate, Job**: Data models for storing and formatting candidate/job information.
- **SkillEnricher**: Enriches the skill set of each candidate by adding related technologies.
- **ATSSystem**: The main system for filtering, scoring, and ranking candidates.
    - `filter_candidates(job: Job)`: Filters candidates based on required skills.
    - `_calculate_skill_match_score()`: Calculates how well candidate skills match the job.
    - `_calculate_semantic_similarity()`: Computes semantic similarity between job descriptions and candidate profiles using embeddings.
    - `get_match_explanations()`: Provides explanations for candidate-job matches.
    - `rank_candidates()`: Ranks candidates based on both skill match score and semantic similarity.

### `build_db.py`
Creates and configures the SQLite database used in the ATS system, as well as the embedding manager for storing candidate embeddings.

### `populate_db.py`
Loads candidate data into the database. This file should be run after `build_db.py` to ensure the database structure is ready to receive data.

### `app.py`
Defines a Flask application with an endpoint to interact with the ATS system. This allows external systems or users to interact with the ATS functionalities via HTTP requests.

### `main.py`
Runs an example of how the ATS system works, providing a CLI-based demo without the need for a frontend interface.

---

## Usage

1. **Build the Database**:
   python build_db.py

2. **Populate the Database:**
    python populate_db.py

3. **Run the ATS System:**
To run the Flask application:
    python app.py

To demonstrate functionality with the command-line example:
python main.py

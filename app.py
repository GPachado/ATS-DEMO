from flask import Flask, request, jsonify
import sqlite3
import json
import time
import logging
from datetime import datetime
from ats_system import ATSSystem, parse_job_json

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

def store_job_matches(job_data, execution_time, ranked_candidates):
    conn = sqlite3.connect('ats.db')
    c = conn.cursor()
    
    # Generate a unique job ID
    job_id = f"job_{int(time.time())}"
    
    # Store matches for top 100 candidates
    for rank, result in enumerate(ranked_candidates[:100], 1):
        candidate = result['candidate']
        
        c.execute('''
            INSERT INTO job_matches (
                job_id,
                execution_time,
                job_title,
                job_description,
                budget_min,
                budget_max,
                budget_currency,
                required_skills,
                candidate_name,
                candidate_email,
                total_score,
                skill_match_score,
                semantic_score,
                skill_matches,
                experience_relevance
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            job_id,
            execution_time,
            job_data['job_title'],
            job_data['job_description'],
            job_data['budget']['min'],
            job_data['budget']['max'],
            job_data['budget']['currency'],
            json.dumps(job_data['required_skills']),
            candidate.full_name,
            candidate.email,
            result['score'],
            result['skill_match_score'],
            result['semantic_score'],
            json.dumps(result['explanations']['skill_matches']),
            json.dumps(result['explanations']['experience_relevance'])
        ))
    
    conn.commit()
    conn.close()
    
    return job_id

@app.route('/api/match-candidates', methods=['POST'])
def match_candidates():
    try:
        # Get job JSON from request
        job_json = request.json
        if not job_json:
            return jsonify({'error': 'No job data provided'}), 400
        
        # Parse and validate job data
        try:
            job = parse_job_json(job_json)
        except ValueError as e:
            return jsonify({'error': f'Invalid job data: {str(e)}'}), 400
        
        # Initialize ATS system
        ats = ATSSystem()
        
        # Time the matching process
        start_time = time.time()
        ranked_candidates = ats.rank_candidates(job)
        execution_time = time.time() - start_time
        
        # Store results in database
        job_id = store_job_matches(job_json, execution_time, ranked_candidates)
        
        # Prepare response
        response = {
            'job_id': job_id,
            'execution_time': execution_time,
            'top_candidates': []
        }
        
        # Add top 10 candidates to response for immediate feedback
        for result in ranked_candidates[:10]:
            candidate = result['candidate']
            response['top_candidates'].append({
                'full_name': candidate.full_name,
                'email': candidate.email,
                'score': round(result['score'], 2),
                'skill_match_score': round(result['skill_match_score'], 2),
                'semantic_score': round(result['semantic_score'], 2),
                'explanations': {
                    'skill_matches': result['explanations']['skill_matches'],
                    'experience_relevance': result['explanations']['experience_relevance']
                }
            })
        
        return jsonify(response)
    
    except Exception as e:
        logging.error(f"Error processing request: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True)
import requests

def test_ats_matching():
    # API endpoint
    url = "http://localhost:5000/api/match-candidates"
    
    job_data = {
    "job_title": "Software Engineer",
    "job_description": "Responsible for developing and maintaining software applications.",
    "budget": {
        "min": 70000,
        "max": 90000,
        "currency": "USD"
    },
    "required_skills": ["JavaScript", "Python", "Java"]
    }

    try:
        # Send POST request
        print("Sending request to ATS system...")
        response = requests.post(
            url,
            json=job_data,
            headers={'Content-Type': 'application/json'}
        )
        
        # Check if request was successful
        response.raise_for_status()
        
        # Get response data
        result = response.json()
        
        # Print job ID and execution time
        print("\nJob Match Results:")
        print(f"Job ID: {result['job_id']}")
        print(f"Execution Time: {result['execution_time']:.2f} seconds")
        
        # Print top candidates
        print("\nTop 5 Candidates:")
        print("-" * 50)
        
        for i, candidate in enumerate(result['top_candidates'], 1):
            print(f"\n{i}. {candidate['full_name']}")
            print(f"   Email: {candidate['email']}")
            print(f"   Total Score: {candidate['score']}")
            print(f"   Skill Match: {candidate['skill_match_score']}")
            print(f"   Semantic Match: {candidate['semantic_score']}")
            
            print("\n   Matching Skills:")
            for skill in candidate['explanations']['skill_matches']:
                print(f"   - {skill}")
            
            print("\n   Experience Relevance:")
            for exp in candidate['explanations']['experience_relevance']:
                print(f"   - {exp}")
            
            print("-" * 50)
        
        # # Now get detailed matches using the job_id
        # detailed_url = f"http://localhost:5000/api/job-matches/{result['job_id']}"
        # detailed_response = requests.get(detailed_url)
        # detailed_response.raise_for_status()
        
        # Save detailed results to a file
        # with open(f"job_matches_{result['job_id']}.json", 'w') as f:
        #     json.dump(detailed_response.json(), f, indent=2)
        
        # print(f"\nDetailed results saved to job_matches_{result['job_id']}.json")
        
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        if hasattr(e.response, 'text'):
            print(f"Server response: {e.response.text}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    # Run the test
    test_ats_matching()
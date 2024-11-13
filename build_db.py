from flask import Flask, request, jsonify
import sqlite3
import json
from datetime import datetime
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict, Any


app = Flask(__name__)

class EmbeddingManager:
    def __init__(self):
        print("loading pretrained model")
        self.model = SentenceTransformer('models') # sentence-transformers/all-MiniLM-L6-v2 Already downloaded
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(path="./chroma_db", settings=Settings(anonymized_telemetry=False))
        
        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name="candidates",
            embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name='models'  # Use the same model as before
            ),
            metadata={"hnsw:space": "cosine"}
        )
    
    def generate_candidate_embedding(self, data: Dict[Any, Any]) -> np.ndarray:
        """Generate embedding for candidate profile"""
        # Format experience text
        experience_texts = []
        for exp in data.get('experiences', []):
            exp_text = f"Worked as {exp['role']} at {exp['company']} for {exp['duration_years']} years"
            experience_texts.append(exp_text)
        
        # Format education text
        education_texts = []
        for edu in data.get('education', []):
            edu_text = f"Studied {edu['degree']} at {edu['institution']} graduating in {edu['year_of_graduation']}"
            education_texts.append(edu_text)
        
        # Combine all text
        profile_text = " ".join([
            " ".join(experience_texts),
            " ".join(education_texts),
            " ".join(data.get('skills', []))
        ])
        
        # Generate embedding
        embedding = self.model.encode(profile_text)
        return embedding.astype(np.float32)
    
    def add_candidate(self, candidate_id: str, data: Dict[Any, Any], embedding: np.ndarray):
        """Add candidate to ChromaDB"""
        # Format profile text (same as in generate_candidate_embedding)
        experience_texts = []
        for exp in data.get('experiences', []):
            exp_text = f"Worked as {exp['role']} at {exp['company']} for {exp['duration_years']} years"
            experience_texts.append(exp_text)
        
        education_texts = []
        for edu in data.get('education', []):
            edu_text = f"Studied {edu['degree']} at {edu['institution']} graduating in {edu['year_of_graduation']}"
            education_texts.append(edu_text)
        
        profile_text = " ".join([
            " ".join(experience_texts),
            " ".join(education_texts),
            " ".join(data.get('skills', []))
        ])
        
        # Add to collection
        self.collection.add(
            ids=[str(candidate_id)],
            embeddings=[embedding.tolist()],
            documents=[profile_text],
            metadatas=[{
                "candidate_id": str(candidate_id)
            }]
        )
    
    def search_candidates(self, 
                         job_embedding: np.ndarray, 
                         candidate_ids: List[str], 
                         k: int = 10) -> List[Dict[str, Any]]:
        """
        Search for similar candidates among preselected ones
        
        Args:
            job_embedding: The job embedding vector
            candidate_ids: List of preselected candidate IDs to search among
            k: Number of results to return
        """
        # Convert candidate_ids to strings if they aren't already
        candidate_ids = [str(id) for id in candidate_ids]
        
        # Query with ID filter
        results = self.collection.query(
            query_embeddings=[job_embedding.tolist()],
            n_results=k,
            where={"candidate_id": {"$in": candidate_ids}}
        )
        
        # Process results
        similarities = []
        for idx, id in enumerate(results['ids'][0]):
            similarities.append({
                'candidate_id': id,
                'similarity': results['distances'][0][idx], 
                'metadata': results['metadatas'][0][idx]
            })
        
        return similarities

def init_db():
    conn = sqlite3.connect('ats.db')
    c = conn.cursor()
    
    # Create tables if they don't already exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            birthdate DATE,
            age INTEGER,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            address TEXT,
            skills TEXT,
            max_education_level TEXT,
            experiences JSON,  -- Add JSON column for experiences
            education JSON,    -- Add JSON column for education
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS experiences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER NOT NULL,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE,
            duration_years REAL,
            FOREIGN KEY (candidate_id) REFERENCES candidates (id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS education (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER NOT NULL,
            institution TEXT NOT NULL,
            degree TEXT NOT NULL,
            year_of_graduation INTEGER NOT NULL,
            FOREIGN KEY (candidate_id) REFERENCES candidates (id)
        )
    ''')

    # Chroma index mapping
    c.execute('''
        CREATE TABLE IF NOT EXISTS candidate_embeddings (
            candidate_id INTEGER PRIMARY KEY,
            chroma_index INTEGER NOT NULL,
            embedding_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (candidate_id) REFERENCES candidates (id)
        )
    ''')

        
    # Result job matches table - Metrics also
    c.execute('''
        CREATE TABLE IF NOT EXISTS job_matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            execution_time FLOAT,
            
            -- Job details
            job_title TEXT NOT NULL,
            job_description TEXT,
            budget_min FLOAT,
            budget_max FLOAT,
            budget_currency TEXT,
            required_skills TEXT,
            
            -- Candidate details
            candidate_name TEXT NOT NULL,
            candidate_email TEXT NOT NULL,
            
            -- Match scores
            total_score FLOAT NOT NULL,
            skill_match_score FLOAT NOT NULL,
            semantic_score FLOAT NOT NULL,
            
            -- Match explanations
            skill_matches TEXT,
            experience_relevance TEXT,
            
            FOREIGN KEY (candidate_email) REFERENCES candidate_email
        )
    ''')
    

    conn.commit()
    conn.close()




def enrich_candidate_profile(data):
    # Enrich skills
    skill_inferences = {
        "Python": ["Flask", "Fastapi", "Pandas", "Numpy"],
        "Pytorch": ["Tensorflow", "Python", "Pandas"],
        "Javascript": ["Nodejs", "React", "Vue", "Angular", "Typescript", "Express"],
        "Java": ["Spring", "Hibernate", "Junit", "Maven", "Gradle"],
    }

    enriched_skills = set(data.get('skills', []))
    for skill in data.get('skills', []):
        if skill in skill_inferences:
            enriched_skills.update(skill_inferences[skill])  # Use update to add elements from the list
    data['skills'] = list(enriched_skills)

    # Calculate experience duration
    for exp in data.get('experiences', []):
        start_date = datetime.strptime(exp['start_date'], "%Y-%m-%d")
        end_date = datetime.strptime(exp['end_date'], "%Y-%m-%d") if exp.get('end_date') else datetime.now()
        exp['duration_years'] = round((end_date - start_date).days / 365, 1)

    # Determine max education level
    education_levels = ["High School", "Bachelor", "Master", "PhD"]
    max_level = "High School"
    for edu in data.get('education', []):
        if edu['degree'] in education_levels and education_levels.index(edu['degree']) > education_levels.index(max_level):
            max_level = edu['degree']
    data['max_education_level'] = max_level
    return data

@app.route('/api/candidates', methods=['POST'])
def add_candidate():
    try:
        embedding_manager = EmbeddingManager()
        data = request.json
        data = enrich_candidate_profile(data)
        
        conn = sqlite3.connect('ats.db')
        c = conn.cursor()
        
        # Insert candidate information including experiences and education as JSON
        c.execute('''
            INSERT INTO candidates (
                first_name, last_name, birthdate, age, email, 
                phone, address, skills, max_education_level, 
                experiences, education
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['first_name'],
            data['last_name'],
            data['birthdate'],
            data['age'],
            data['email'],
            data['phone'],
            data['address'],
            json.dumps(data['skills']),
            data['max_education_level'],
            json.dumps(data.get('experiences', [])),  # Convert experiences list to JSON
            json.dumps(data.get('education', []))     # Convert education list to JSON
        ))
        
        candidate_id = c.lastrowid
        
        # Generate and store embedding
        embedding = embedding_manager.generate_candidate_embedding(data)
        
        # Add embedding 
        embedding_manager.add_candidate(candidate_id, data, embedding)
        
        # Store mapping in SQLite
        c.execute('''
            INSERT INTO candidate_embeddings (candidate_id, chroma_index)
            VALUES (?, ?)
        ''', (candidate_id, candidate_id))

        try:
            # Insert enriched experiences into the experiences table
            for exp in data.get('experiences', []):
                c.execute('''
                    INSERT INTO experiences (
                        candidate_id, company, role, start_date, end_date, duration_years
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    candidate_id,
                    exp['company'],
                    exp['role'],
                    exp['start_date'],
                    exp.get('end_date'),
                    exp['duration_years']
                ))
                
            
            # Insert education into the education table
            for edu in data.get('education', []):
                c.execute('''
                    INSERT INTO education (
                        candidate_id, institution, degree, year_of_graduation
                    ) VALUES (?, ?, ?, ?)
                ''', (
                    candidate_id,
                    edu['institution'],
                    edu['degree'],
                    edu['year_of_graduation']
                ))
            
            
            conn.commit()
            
            return jsonify({'status': 'success', 'id': candidate_id}), 201
        
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    except sqlite3.IntegrityError:
        return jsonify({'status': 'error', 'message': 'Email already exists'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

if __name__ == '__main__':
    init_db()
    app.run(debug=True)





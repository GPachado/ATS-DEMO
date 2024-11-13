'''This following code will set the CURL_CA_BUNDLE environment variable to an empty string in the Python os module'''

import os
os.environ['CURL_CA_BUNDLE'] = ''

import sqlite3
import json
from typing import List, Dict, Any
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer
import numpy as np
import logging
import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
from build_db import EmbeddingManager

# Configure the logging system
logging.basicConfig(
    level=logging.INFO,                
    format='%(asctime)s - %(levelname)s - %(message)s',  
    handlers=[
        logging.FileHandler("app.log"),     
        logging.StreamHandler()             
    ]
)

# Data Models
@dataclass
class Experience:
    company: str
    role: str
    start_date: str
    end_date: str
    duration_years: float
    
    def to_text(self) -> str:
        return f"{self.role} at {self.company}"

@dataclass
class Education:
    institution: str
    degree: str
    year_of_graduation: int
    
    def to_text(self) -> str:
        return f"{self.degree} from {self.institution}"

@dataclass
class Candidate:
    first_name: str
    last_name: str
    email: str
    skills: List[str]
    experiences: List[Experience]
    education: List[Education]
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    

@dataclass
class Job:
    title: str
    description: str
    required_skills: List[str]
    
    def to_job_text(self) -> str:
        """Convert job to a single text for embedding"""
        return f"{self.title}. {self.description}. Required skills: {', '.join(self.required_skills)}"

class SkillEnricher:
    """Enriches skills with related technologies and frameworks"""
    def __init__(self):
        # This is a simplified version. A tree of skills or graph could be a better option
        self.skill_relations = {
            "Python": ["Flask", "Fastapi", "Pandas", "Numpy"],
            "Pytorch": ["Tensorflow", "Python", "Pandas"],
            "Javascript": ["Nodejs", "React", "Vue", "Angular", "Typescript", "Express"],
            "Java": ["Spring", "Hibernate", "Junit", "Maven", "Gradle"],
        }

    def enrich_skills(self, skills: List[str]) -> List[str]:
        """Expand skills list with related technologies"""
        enriched_skills = set(skills)
        for skill in skills:
            skill_lower = skill.lower()
            if skill_lower in self.skill_relations:
                enriched_skills.update(self.skill_relations[skill_lower])
        return list(enriched_skills)

class ATSSystem:
    def __init__(self):
        self.embedding_manager = EmbeddingManager()
        self.model = self.embedding_manager.model
        self.skill_enricher = SkillEnricher()
        
        
    def filter_candidates(self, job: Job):
        required_skills = job.required_skills
        
        # Conectarse a la base de datos SQLite
        conn = sqlite3.connect('ats.db')
        c = conn.cursor()

        # Crear una consulta SQL dinámica que use la cláusula LIKE para filtrar por habilidades
        like_conditions = ' OR '.join([f"skills LIKE '%\"{skill}\"%'" for skill in required_skills])
        query = f"""
                    SELECT c.*, ce.chroma_index 
                    FROM candidates c
                    JOIN candidate_embeddings ce ON c.id = ce.candidate_id
                    WHERE {like_conditions}
                """
        
        # Ejecutar la consulta SQL filtrando por habilidades
        c.execute(query)
        filtered_candidates = c.fetchall()
        column_names = [description[0] for description in c.description]
        conn.close()

        return filtered_candidates, column_names

    def _calculate_skill_match_score(self, job_skills: List[str], candidate_skills: List[str]) -> float:
        """Calculate skill match score based on required skills"""
        candidate_skills_set = set(s.lower() for s in candidate_skills)
        
        # Enrich both sets
        job_skills_enriched = set(self.skill_enricher.enrich_skills(job_skills))
        job_skills_enriched = set(s.lower() for s in job_skills_enriched)
        
        matched_skills = candidate_skills_set.intersection(job_skills_enriched)
        return len(matched_skills) / len(job_skills_enriched)

    
    def _calculate_semantic_similarity(self, job_embedding: np.ndarray, candidate_indices: List[int]) -> List[float]:
        """
        Calculate semantic similarity using pre-computed embeddings,
        considering only preselected candidates.
        """
        similarities = self.embedding_manager.search_candidates(
            job_embedding=job_embedding,
            candidate_ids=candidate_indices,
            k = 100 #len(candidate_indices)
            )
        logging.info(f"similarities: {similarities}")
        return similarities
    


    def get_match_explanations(self, job: Job, candidate: Candidate) -> Dict[str, Any]:
        """Generate explanations for why a candidate matches a job"""
        explanations = {
            "skill_matches": [],
            "experience_relevance": [],
            "education_relevance": []
        }
        
        # Skill matches
        candidate_skills_enriched = set(self.skill_enricher.enrich_skills(candidate.skills))
        job_skills_enriched = set(self.skill_enricher.enrich_skills(job.required_skills))
        matched_skills = candidate_skills_enriched.intersection(job_skills_enriched)
        
        explanations["skill_matches"] = list(matched_skills)
        
        # Experience relevance
        for exp in candidate.experiences:
            if any(skill.lower() in exp.role.lower() for skill in job_skills_enriched):
                explanations["experience_relevance"].append(
                    f"Relevant experience: {exp.role} at {exp.company}"
                )
        
        return explanations

    def rank_candidates(self, job: Job, 
                       min_skill_match: float = 0.1) -> List[Dict[str, Any]]:
        """Rank candidates for a job using a hybrid approach"""
        # Initial filter - Gross Filter
        candidates, column_names = self.filter_candidates(job)
        
        ranked_candidates = []
        candidate_chroma_indices = []
        
        for row in candidates:
            # Initial skill-based filtering
            logging.info("Initial skill-based filtering")
            candidate_dict = dict(zip(column_names, row))
            chroma_index = candidate_dict.pop('chroma_index') 
            candidate_chroma_indices.append(chroma_index)

            candidate_dict['skills'] = json.loads(candidate_dict['skills'])
            candidate = parse_candidate_json(candidate_dict)

            skill_match_score = self._calculate_skill_match_score(
                job.required_skills, candidate.skills
            )

            logging.info(skill_match_score)
            
            if skill_match_score >= min_skill_match:
                ranked_candidates.append({
                    "candidate": candidate,
                    "skill_match_score": skill_match_score,
                    "chroma_index": chroma_index
                })
        logging.info(ranked_candidates)

        if ranked_candidates:
            # Calculate semantic similarities for all candidates at once
            job_embedding = self.model.encode(job.to_job_text()).astype(np.float32)
            semantic_scores = self._calculate_semantic_similarity(job_embedding, [c["chroma_index"] for c in ranked_candidates])
            logging.info(f"Semantic Scores: {semantic_scores}")
            # Add scores and explanations
            for candidate_dict in ranked_candidates:
                chroma_index = candidate_dict['chroma_index']
                candidate_dict["explanations"] = self.get_match_explanations(job, candidate_dict["candidate"])

                for score in semantic_scores:
                    if int(score['candidate_id']) == chroma_index:
                        candidate_dict['semantic_score'] = score['similarity']
                        candidate_dict["score"] = (candidate_dict["skill_match_score"] * 0.4 + score['similarity'] * 0.6)
                        break

            # Print the updated ranked_candidates
            for candidate_dict in ranked_candidates:
                print("CANDIDATE")
                print(candidate_dict)
            # for candidate_dict, semantic_score in zip(ranked_candidates, semantic_scores):
            #     candidate_dict["semantic_score"] = float(semantic_score)
            #     candidate_dict["score"] = (candidate_dict["skill_match_score"] * 0.6 + semantic_score * 0.4)
            #     candidate_dict["explanations"] = self.get_match_explanations(job, candidate_dict["candidate"])
            #     logging.info(f"Processed candidate: {candidate_dict['candidate'].full_name} with score: {candidate_dict['score']}")
        
        # Sort by combined score
        ranked_candidates.sort(key=lambda x: x["score"], reverse=True)
        return ranked_candidates

# Usage example
def parse_candidate_json(candidate) -> Candidate:
    experiences_data = json.loads(candidate["experiences"])
    education_data = json.loads(candidate["education"])

    # Experience instances
    experiences = [Experience(**exp) for exp in experiences_data]
    
    education = [Education(**edu) for edu in education_data]
    return Candidate(
        first_name=candidate["first_name"],
        last_name=candidate["last_name"],
        email=candidate["email"],
        skills=candidate["skills"],
        experiences=experiences,
        education=education
    )

def parse_job_json(job_json: Dict) -> Job:
    return Job(
        title=job_json["job_title"],
        description=job_json["job_description"],
        required_skills=job_json["required_skills"]
    )

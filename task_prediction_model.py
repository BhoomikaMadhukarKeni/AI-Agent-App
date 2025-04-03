import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
import streamlit as st
import pickle
import os

class TaskAssignmentModel:
    """
    Machine learning model for automated task assignment predictions
    """
    def __init__(self):
        self.model = None
        self.skill_vectorizer = TfidfVectorizer(analyzer='word', stop_words='english')
        self.label_encoder = LabelEncoder()
        self.trained = False
        self.features = None
        self.model_path = "task_assignment_model.pkl"
        self.vectorizer_path = "skill_vectorizer.pkl"
        
    def preprocess_data(self, employees_df: pd.DataFrame, tasks_df: pd.DataFrame) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        Preprocess employee and task data for model training
        """
        # Create training dataset from successful task assignments
        training_data = []
        
        if tasks_df is None or len(tasks_df) == 0 or 'Assigned_To' not in tasks_df.columns:
            return None, None
            
        # Filter tasks that have been assigned and completed
        completed_tasks = tasks_df[
            (tasks_df['Assigned_To'].notnull()) & 
            (tasks_df['Status'] == 'Completed')
        ]
        
        if len(completed_tasks) == 0:
            return None, None
            
        # For each completed task, create a training sample
        for _, task in completed_tasks.iterrows():
            if task['Assigned_To'] in employees_df['ID'].values:
                # Find the employee who completed the task
                employee = employees_df[employees_df['ID'] == task['Assigned_To']].iloc[0]
                
                # Create features
                features = {
                    'skill_match_score': self._calculate_skill_match(employee['Skills'], task['Required_Skills']),
                    'employee_experience': self._encode_experience(employee['Experience']),
                    'task_priority': self._encode_priority(task['Priority']),
                    'current_workload': employee['TaskCount'],
                    'completed_tasks': employee['CompletedTasks']
                }
                
                # Add employee ID as the target
                features['assigned_to'] = employee['ID']
                
                training_data.append(features)
                
        if not training_data:
            return None, None
            
        # Convert to DataFrame
        training_df = pd.DataFrame(training_data)
        
        # Separate features and target
        X = training_df.drop('assigned_to', axis=1)
        y = training_df['assigned_to']
        
        # Save feature columns
        self.features = X.columns.tolist()
        
        return X, y
    
    def _calculate_skill_match(self, employee_skills: List[str], task_skills: List[str]) -> float:
        """
        Calculate skill match score between employee and task
        """
        if not employee_skills or not task_skills:
            return 0.0
            
        # Count matching skills
        matching_skills = set(employee_skills).intersection(set(task_skills))
        
        # Calculate match percentage
        if len(task_skills) == 0:
            return 0.0
            
        return len(matching_skills) / len(task_skills)
    
    def _encode_experience(self, experience: str) -> int:
        """
        Encode experience level to numerical value
        """
        experience_map = {
            'Junior': 1,
            'Mid-Level': 2,
            'Senior': 3,
            'Expert': 4
        }
        return experience_map.get(experience, 0)
    
    def _encode_priority(self, priority: str) -> int:
        """
        Encode task priority to numerical value
        """
        priority_map = {
            'Low': 1,
            'Medium': 2,
            'High': 3
        }
        return priority_map.get(priority, 0)
        
    def train_model(self, employees_df: pd.DataFrame, tasks_df: pd.DataFrame) -> bool:
        """
        Train the task assignment prediction model
        """
        # Preprocess data
        X, y = self.preprocess_data(employees_df, tasks_df)
        
        if X is None or len(X) < 5:  # Need at least a few samples to train
            return False
            
        # Create and train a Random Forest classifier
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        
        # Train the model
        self.model.fit(X, y)
        self.trained = True
        
        # Save the model
        self.save_model()
        
        return True
        
    def predict(self, task: Dict, employees_df: pd.DataFrame) -> pd.DataFrame:
        """
        Predict the best employee matches for a task
        """
        if not self.trained and not self.load_model():
            # If model not trained and can't be loaded, return None
            return None
            
        # Prepare prediction data for all employees
        prediction_data = []
        
        for _, employee in employees_df.iterrows():
            features = {
                'skill_match_score': self._calculate_skill_match(employee['Skills'], task['Required_Skills']),
                'employee_experience': self._encode_experience(employee['Experience']),
                'task_priority': self._encode_priority(task['Priority']),
                'current_workload': employee['TaskCount'],
                'completed_tasks': employee['CompletedTasks']
            }
            
            prediction_data.append(features)
            
        # Convert to DataFrame
        pred_df = pd.DataFrame(prediction_data, index=employees_df.index)
        
        # Ensure all required features are present
        for feature in self.features:
            if feature not in pred_df.columns:
                pred_df[feature] = 0
                
        # Reorder columns to match training data
        pred_df = pred_df[self.features]
        
        # Get prediction probabilities
        if len(pred_df) > 0:
            probas = self.model.predict_proba(pred_df)
            
            # Get employee IDs from the model's classes
            employee_ids = self.model.classes_
            
            # Create a probability DataFrame
            proba_df = pd.DataFrame(probas, columns=employee_ids)
            
            # Assign probabilities to each employee
            employees_df = employees_df.copy()
            employees_df['PredictionScore'] = 0.0
            
            for emp_id in employee_ids:
                if emp_id in employees_df['ID'].values:
                    mask = employees_df['ID'] == emp_id
                    idx = employees_df.index[mask].tolist()
                    if idx:
                        # Find the probability for this employee ID
                        col_idx = list(employee_ids).index(emp_id)
                        if col_idx < probas.shape[1]:
                            employees_df.loc[mask, 'PredictionScore'] = probas[:, col_idx].max()
            
            # Sort by prediction score
            return employees_df.sort_values('PredictionScore', ascending=False)
        
        return employees_df
    
    def save_model(self) -> bool:
        """
        Save the trained model to disk
        """
        if not self.trained or self.model is None:
            return False
            
        try:
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)
                
            return True
        except Exception as e:
            st.error(f"Error saving model: {e}")
            return False
    
    def load_model(self) -> bool:
        """
        Load a trained model from disk
        """
        if not os.path.exists(self.model_path):
            return False
            
        try:
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
                
            self.trained = True
            self.features = ['skill_match_score', 'employee_experience', 
                           'task_priority', 'current_workload', 'completed_tasks']
            return True
        except Exception as e:
            st.error(f"Error loading model: {e}")
            return False

# Create a simpler model that can work with minimal data using TF-IDF and cosine similarity
class SkillSimilarityModel:
    """
    A simpler model that uses TF-IDF vectorization and cosine similarity 
    to match tasks to employees based on skills
    """
    def __init__(self):
        self.vectorizer = TfidfVectorizer(analyzer='word', stop_words='english')
        self.employee_skill_matrix = None
        self.employee_ids = None
        
    def fit(self, employees_df: pd.DataFrame) -> None:
        """
        Process employee skills data to create a skill matrix
        """
        if employees_df is None or len(employees_df) == 0:
            return
            
        # Prepare skill documents (one per employee)
        skill_docs = []
        employee_ids = []
        
        for _, employee in employees_df.iterrows():
            # Join all skills into a single document
            skill_text = " ".join(employee['Skills'])
            skill_docs.append(skill_text)
            employee_ids.append(employee['ID'])
            
        # Fit and transform the vectorizer
        self.employee_skill_matrix = self.vectorizer.fit_transform(skill_docs)
        self.employee_ids = employee_ids
        
    def predict(self, task: Dict, employees_df: pd.DataFrame) -> pd.DataFrame:
        """
        Find best matching employees for a task based on skill similarity
        """
        if self.employee_skill_matrix is None or self.employee_ids is None:
            self.fit(employees_df)
            
        if self.employee_skill_matrix is None:
            return employees_df
            
        # Vectorize the task skills
        task_skills = " ".join(task['Required_Skills'])
        task_vector = self.vectorizer.transform([task_skills])
        
        # Calculate cosine similarity with all employees
        similarities = cosine_similarity(task_vector, self.employee_skill_matrix)[0]
        
        # Associate similarities with employee IDs
        similarity_dict = dict(zip(self.employee_ids, similarities))
        
        # Add similarity scores to employee DataFrame
        employees_df = employees_df.copy()
        employees_df['SimilarityScore'] = employees_df['ID'].map(similarity_dict)
        
        # Sort by similarity (highest first)
        return employees_df.sort_values('SimilarityScore', ascending=False)
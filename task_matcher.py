import pandas as pd
from typing import List, Dict, Any, Optional
import streamlit as st
from task_prediction_model import TaskAssignmentModel, SkillSimilarityModel

class TaskMatcher:
    """
    Handles matching tasks to employees based on skills and availability
    """
    def __init__(self, employee_df: Optional[pd.DataFrame] = None):
        self.employee_df = employee_df
        self.ml_model = TaskAssignmentModel()
        self.similarity_model = SkillSimilarityModel()
        self.use_ml_model = False
        self.tasks_df = None
    
    def set_employee_data(self, employee_df: pd.DataFrame) -> None:
        """
        Set or update the employee data
        """
        self.employee_df = employee_df
        
        # Fit the similarity model with the updated employee data
        self.similarity_model.fit(employee_df)
        
    def set_tasks_data(self, tasks_df: pd.DataFrame) -> None:
        """
        Set task data for model training
        """
        self.tasks_df = tasks_df
        
    def train_prediction_model(self) -> bool:
        """
        Train the ML prediction model with current employee and task data
        """
        if self.employee_df is None or self.tasks_df is None:
            return False
            
        success = self.ml_model.train_model(self.employee_df, self.tasks_df)
        if success:
            self.use_ml_model = True
            st.success("AI task assignment model trained successfully!")
        return success
    
    def find_matching_employees(self, required_skills: List[str], experience_level: Optional[str] = None) -> pd.DataFrame:
        """
        Find employees that match the required skills and optionally experience level
        """
        if self.employee_df is None or len(self.employee_df) == 0:
            return pd.DataFrame()
        
        matching_employees = []
        
        for idx, employee in self.employee_df.iterrows():
            employee_skills = employee['Skills']
            skill_match_count = sum(1 for skill in required_skills if skill in employee_skills)
            
            # Calculate match percentage
            match_percentage = (skill_match_count / len(required_skills)) * 100 if required_skills else 0
            
            # Experience level filter
            exp_match = True
            if experience_level and experience_level != "Any":
                exp_match = employee['Experience'] == experience_level
            
            # Add employee to matches if they have at least one matching skill and match experience if specified
            if skill_match_count > 0 and exp_match:
                matching_employees.append({
                    'ID': employee['ID'],
                    'Name': employee['Name'],
                    'Role': employee['Role'],
                    'Position': employee['Position'],
                    'Experience': employee['Experience'],
                    'Skills': employee['Skills'],
                    'Status': employee['Status'],
                    'TaskCount': employee['TaskCount'],
                    'MatchPercentage': match_percentage
                })
        
        # Convert to DataFrame and sort by match percentage
        if matching_employees:
            result_df = pd.DataFrame(matching_employees)
            return result_df.sort_values(by='MatchPercentage', ascending=False)
        
        return pd.DataFrame()
    
    def find_employees_by_skill(self, skill: str) -> pd.DataFrame:
        """
        Find employees who have a specific skill
        """
        if self.employee_df is None or len(self.employee_df) == 0:
            return pd.DataFrame()
        
        filtered_employees = []
        
        for idx, employee in self.employee_df.iterrows():
            if skill in employee['Skills']:
                filtered_employees.append({
                    'ID': employee['ID'],
                    'Name': employee['Name'],
                    'Role': employee['Role'],
                    'Position': employee['Position'],
                    'Experience': employee['Experience'],
                    'Skills': employee['Skills'],
                    'Status': employee['Status'],
                    'TaskCount': employee['TaskCount']
                })
        
        if filtered_employees:
            return pd.DataFrame(filtered_employees)
        
        return pd.DataFrame()
    
    def recommend_best_match(self, required_skills: List[str], experience_preference: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Recommend the best employee match for a task based on skills, experience, and current workload
        Uses AI models when available
        """
        # Create a mock task for prediction
        task = {
            'Required_Skills': required_skills,
            'Priority': 'Medium',  # Default priority if not specified
            'Status': 'Not Started'
        }
        
        # Try to use AI models if available
        employees_with_scores = None
        
        # First try the ML model if it's trained
        if self.use_ml_model and self.ml_model.trained:
            # Use the machine learning model for prediction
            employees_with_scores = self.ml_model.predict(task, self.employee_df)
            
            if employees_with_scores is not None and len(employees_with_scores) > 0:
                # Apply experience filter if specified
                if experience_preference and experience_preference != "Any":
                    employees_with_scores = employees_with_scores[
                        employees_with_scores['Experience'] == experience_preference
                    ]
                
                if len(employees_with_scores) > 0:
                    # Get the best match
                    best_match = employees_with_scores.iloc[0].to_dict()
                    best_match['MatchPercentage'] = float(best_match.get('PredictionScore', 0) * 100)
                    best_match['AI_Powered'] = True
                    return best_match
        
        # If ML model fails or not enough data, try the similarity model
        employees_with_scores = self.similarity_model.predict(task, self.employee_df)
        if employees_with_scores is not None and len(employees_with_scores) > 0:
            # Apply experience filter if specified
            if experience_preference and experience_preference != "Any":
                employees_with_scores = employees_with_scores[
                    employees_with_scores['Experience'] == experience_preference
                ]
            
            if len(employees_with_scores) > 0:
                # Get the best match considering similarity and workload
                employees_with_scores['WorkloadFactor'] = 1.0
                for idx, emp in employees_with_scores.iterrows():
                    if emp['Status'] == 'Partially Assigned':
                        employees_with_scores.at[idx, 'WorkloadFactor'] = 0.8
                    elif emp['Status'] == 'Fully Assigned':
                        employees_with_scores.at[idx, 'WorkloadFactor'] = 0.5
                
                # Adjust score by workload factor
                employees_with_scores['FinalScore'] = employees_with_scores['SimilarityScore'] * employees_with_scores['WorkloadFactor']
                
                # Get best match
                best_match = employees_with_scores.sort_values(by='FinalScore', ascending=False).iloc[0].to_dict()
                best_match['MatchPercentage'] = float(best_match.get('SimilarityScore', 0) * 100)
                best_match['AI_Powered'] = True
                return best_match
        
        # Fall back to the original algorithm if AI methods fail
        matching_employees = self.find_matching_employees(required_skills, experience_preference)
        
        if len(matching_employees) == 0:
            return None
        
        # Consider both match percentage and current workload
        matching_employees['WorkloadFactor'] = 1.0
        for idx, emp in matching_employees.iterrows():
            if emp['Status'] == 'Partially Assigned':
                matching_employees.at[idx, 'WorkloadFactor'] = 0.8
            elif emp['Status'] == 'Fully Assigned':
                matching_employees.at[idx, 'WorkloadFactor'] = 0.5
        
        # Adjust match score by workload factor
        matching_employees['FinalScore'] = matching_employees['MatchPercentage'] * matching_employees['WorkloadFactor']
        
        # Get best match
        best_match = matching_employees.sort_values(by='FinalScore', ascending=False).iloc[0].to_dict()
        best_match['AI_Powered'] = False
        
        return best_match
        
    def find_ai_matches(self, task: Dict[str, Any]) -> pd.DataFrame:
        """
        Use AI models to find the best matches for a task
        """
        # Try the ML model first if trained
        if self.use_ml_model and self.ml_model.trained:
            matches = self.ml_model.predict(task, self.employee_df)
            if matches is not None and len(matches) > 0:
                # Add AI flag
                matches['AI_Method'] = 'Machine Learning'
                matches['MatchPercentage'] = matches['PredictionScore'] * 100
                return matches
        
        # Fall back to similarity model
        matches = self.similarity_model.predict(task, self.employee_df)
        if matches is not None and len(matches) > 0:
            # Add AI flag
            matches['AI_Method'] = 'Skill Similarity'
            matches['MatchPercentage'] = matches['SimilarityScore'] * 100
            return matches
            
        # If all else fails, use the basic matching algorithm
        if 'Required_Skills' in task:
            return self.find_matching_employees(task['Required_Skills'])
            
        return pd.DataFrame()

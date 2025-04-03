import pandas as pd
from typing import List, Dict, Any, Optional

class TaskMatcher:
    """
    Handles matching tasks to employees based on skills and availability
    """
    def __init__(self, employee_df: Optional[pd.DataFrame] = None):
        self.employee_df = employee_df
    
    def set_employee_data(self, employee_df: pd.DataFrame) -> None:
        """
        Set or update the employee data
        """
        self.employee_df = employee_df
    
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
        """
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
        
        return best_match

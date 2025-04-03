import pandas as pd
import streamlit as st
from typing import List, Dict, Any, Optional

class EmployeeManagement:
    """
    Manages employee preferences and settings
    """
    def __init__(self, employee_df: Optional[pd.DataFrame] = None):
        self.employee_df = employee_df
        
        # Initialize employee preferences
        if 'employee_preferences' not in st.session_state:
            st.session_state.employee_preferences = {}
    
    def set_employee_data(self, employee_df: pd.DataFrame) -> None:
        """
        Set or update the employee data
        """
        self.employee_df = employee_df
    
    def get_employee_by_id(self, employee_id: int) -> Optional[Dict[str, Any]]:
        """
        Get employee information by ID
        """
        if self.employee_df is None:
            return None
        
        employee = self.employee_df[self.employee_df['ID'] == employee_id]
        
        if len(employee) == 0:
            return None
        
        return employee.iloc[0].to_dict()
    
    def set_employee_preference(self, employee_id: int, preference_type: str, preference_value: Any) -> bool:
        """
        Set a preference for an employee
        """
        if employee_id not in st.session_state.employee_preferences:
            st.session_state.employee_preferences[employee_id] = {}
        
        st.session_state.employee_preferences[employee_id][preference_type] = preference_value
        return True
    
    def get_employee_preference(self, employee_id: int, preference_type: str) -> Any:
        """
        Get a preference for an employee
        """
        if (employee_id not in st.session_state.employee_preferences or 
            preference_type not in st.session_state.employee_preferences[employee_id]):
            return None
        
        return st.session_state.employee_preferences[employee_id][preference_type]
    
    def get_employee_preferences(self, employee_id: int) -> Dict[str, Any]:
        """
        Get all preferences for an employee
        """
        if employee_id not in st.session_state.employee_preferences:
            return {}
        
        return st.session_state.employee_preferences[employee_id]
    
    def update_employee_skill(self, employee_id: int, skill: str, add: bool = True) -> bool:
        """
        Add or remove a skill for an employee
        """
        if self.employee_df is None:
            return False
        
        employee_idx = self.employee_df.index[self.employee_df['ID'] == employee_id].tolist()
        
        if not employee_idx:
            return False
        
        employee_idx = employee_idx[0]
        current_skills = self.employee_df.at[employee_idx, 'Skills']
        
        if add and skill not in current_skills:
            current_skills.append(skill)
            self.employee_df.at[employee_idx, 'Skills'] = current_skills
            return True
        elif not add and skill in current_skills:
            current_skills.remove(skill)
            self.employee_df.at[employee_idx, 'Skills'] = current_skills
            return True
            
        return False

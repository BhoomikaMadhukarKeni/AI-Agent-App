import pandas as pd
import streamlit as st
import os
from typing import List, Dict, Any, Optional

class DataHandler:
    """
    Handles loading, processing, and storing employee and task data
    """
    def __init__(self):
        # Initialized data containers
        self.employee_df = None
        self.tasks_df = pd.DataFrame(columns=["TaskID", "Description", "Required_Skills", 
                                             "Assigned_To", "Status", "Due_Date", "Priority"])
        
        # Define status options
        self.task_status_options = ["Not Started", "In Progress", "Completed", "Blocked"]
        self.employee_status_options = ["Unassigned", "Partially Assigned", "Fully Assigned"]
        
        # Initialize session state for tasks if not exists
        if 'tasks' not in st.session_state:
            st.session_state.tasks = []
        
        if 'task_counter' not in st.session_state:
            st.session_state.task_counter = 1
        
        if 'employee_data_loaded' not in st.session_state:
            st.session_state.employee_data_loaded = False
    
    def load_employee_data(self, file_path: str) -> bool:
        """
        Load employee data from CSV file
        """
        try:
            if os.path.exists(file_path):
                self.employee_df = pd.read_csv(file_path)
                
                # Process skills column to ensure it's a list
                self.employee_df['Skills'] = self.employee_df['Skills'].apply(
                    lambda x: [skill.strip() for skill in str(x).split(',')]
                )
                
                # Initialize availability status for all employees
                if 'Status' not in self.employee_df.columns:
                    self.employee_df['Status'] = 'Unassigned'
                
                # Initialize task count for all employees
                if 'TaskCount' not in self.employee_df.columns:
                    self.employee_df['TaskCount'] = 0
                
                # Initialize completed tasks count
                if 'CompletedTasks' not in self.employee_df.columns:
                    self.employee_df['CompletedTasks'] = 0
                
                st.session_state.employee_data_loaded = True
                return True
            else:
                st.error(f"File not found: {file_path}")
                return False
        except Exception as e:
            st.error(f"Error loading employee data: {e}")
            return False
    
    def get_all_skills(self) -> List[str]:
        """
        Get a unique list of all skills from the employee data
        """
        if self.employee_df is None:
            return []
        
        all_skills = []
        for skills_list in self.employee_df['Skills']:
            all_skills.extend(skills_list)
        
        return sorted(list(set(all_skills)))
    
    def add_task(self, description: str, required_skills: List[str], due_date: Optional[str] = None, 
                priority: str = "Medium") -> int:
        """
        Add a new task to the task list
        """
        task_id = st.session_state.task_counter
        
        new_task = {
            "TaskID": task_id,
            "Description": description,
            "Required_Skills": required_skills,
            "Assigned_To": None,
            "Status": "Not Started",
            "Due_Date": due_date,
            "Priority": priority
        }
        
        st.session_state.tasks.append(new_task)
        st.session_state.task_counter += 1
        
        # Update tasks DataFrame
        self.tasks_df = pd.DataFrame(st.session_state.tasks)
        
        return task_id
    
    def assign_task(self, task_id: int, employee_id: int) -> bool:
        """
        Assign a task to an employee
        """
        # Check if employee exists
        if self.employee_df is None or employee_id not in self.employee_df['ID'].values:
            return False
        
        # Find the task in session state
        for task in st.session_state.tasks:
            if task["TaskID"] == task_id:
                task["Assigned_To"] = employee_id
                task["Status"] = "In Progress"
                
                # Update employee task count
                employee_idx = self.employee_df.index[self.employee_df['ID'] == employee_id].tolist()[0]
                self.employee_df.at[employee_idx, 'TaskCount'] += 1
                
                # Update employee status based on task count
                task_count = self.employee_df.at[employee_idx, 'TaskCount']
                if task_count == 0:
                    self.employee_df.at[employee_idx, 'Status'] = 'Unassigned'
                elif 1 <= task_count <= 3:
                    self.employee_df.at[employee_idx, 'Status'] = 'Partially Assigned'
                else:
                    self.employee_df.at[employee_idx, 'Status'] = 'Fully Assigned'
                
                # Update tasks DataFrame
                self.tasks_df = pd.DataFrame(st.session_state.tasks)
                
                return True
        
        return False
    
    def update_task_status(self, task_id: int, status: str) -> bool:
        """
        Update the status of a task
        """
        for task in st.session_state.tasks:
            if task["TaskID"] == task_id:
                prev_status = task["Status"]
                task["Status"] = status
                
                # If task is completed, increment employee's completed task count
                if status == "Completed" and prev_status != "Completed" and task["Assigned_To"] is not None:
                    employee_id = task["Assigned_To"]
                    employee_idx = self.employee_df.index[self.employee_df['ID'] == employee_id].tolist()[0]
                    self.employee_df.at[employee_idx, 'CompletedTasks'] += 1
                    self.employee_df.at[employee_idx, 'TaskCount'] -= 1
                
                # Update tasks DataFrame
                self.tasks_df = pd.DataFrame(st.session_state.tasks)
                
                return True
        
        return False
    
    def get_employee_tasks(self, employee_id: int) -> List[Dict[str, Any]]:
        """
        Get all tasks assigned to a specific employee
        """
        if not st.session_state.tasks:
            return []
        
        return [task for task in st.session_state.tasks if task["Assigned_To"] == employee_id]
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """
        Get all tasks
        """
        return st.session_state.tasks
    
    def get_leaderboard_data(self) -> pd.DataFrame:
        """
        Get data for the performance leaderboard
        """
        if self.employee_df is None:
            return pd.DataFrame()
        
        leaderboard = self.employee_df[['ID', 'Name', 'Role', 'CompletedTasks']].copy()
        leaderboard = leaderboard.sort_values(by='CompletedTasks', ascending=False)
        
        return leaderboard

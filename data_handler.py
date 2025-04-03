import pandas as pd
import streamlit as st
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
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
                
                # Add email column if it doesn't exist
                if 'Email' not in self.employee_df.columns:
                    # Generate emails based on name
                    self.employee_df['Email'] = self.employee_df['Name'].apply(
                        lambda name: f"{name.lower().replace(' ', '.')}@example.com"
                    )
                
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
    
    def send_email_notification(self, to_email: str, subject: str, message: str) -> bool:
        """
        Send an email notification to the employee
        """
        # This is a mock function for demonstration. In production, you would use actual email service.
        try:
            # Store email in session state for demo purposes
            if 'sent_emails' not in st.session_state:
                st.session_state.sent_emails = []
            
            email_data = {
                "to": to_email,
                "subject": subject,
                "message": message,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            st.session_state.sent_emails.append(email_data)
            
            # In a real implementation, you would use:
            # sender_email = "your_email@gmail.com"
            # sender_password = "your_app_password"
            # 
            # msg = MIMEMultipart()
            # msg['From'] = sender_email
            # msg['To'] = to_email
            # msg['Subject'] = subject
            # 
            # msg.attach(MIMEText(message, 'html'))
            # 
            # server = smtplib.SMTP('smtp.gmail.com', 587)
            # server.starttls()
            # server.login(sender_email, sender_password)
            # server.send_message(msg)
            # server.quit()
            
            return True
        except Exception as e:
            st.error(f"Error sending email: {e}")
            return False
    
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
                task["Assigned_Date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
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
                
                # Send email notification to the employee
                employee_email = self.employee_df.at[employee_idx, 'Email']
                employee_name = self.employee_df.at[employee_idx, 'Name']
                
                email_subject = f"New Task Assignment: {task['Description'][:30]}..."
                email_message = f"""
                <html>
                <body>
                    <h2>New Task Assignment</h2>
                    <p>Hello {employee_name},</p>
                    <p>You have been assigned a new task:</p>
                    <div style="background-color:#f0f0f0; padding:15px; border-radius:5px;">
                        <p><strong>Task ID:</strong> {task_id}</p>
                        <p><strong>Description:</strong> {task['Description']}</p>
                        <p><strong>Required Skills:</strong> {', '.join(task['Required_Skills'])}</p>
                        <p><strong>Priority:</strong> {task['Priority']}</p>
                        <p><strong>Due Date:</strong> {task['Due_Date']}</p>
                        <p><strong>Status:</strong> {task['Status']}</p>
                    </div>
                    <p>Please log in to the Task Management System to view more details and update your progress.</p>
                    <p>Thank you,<br>Task Management System</p>
                </body>
                </html>
                """
                
                self.send_email_notification(employee_email, email_subject, email_message)
                
                # Update tasks DataFrame
                self.tasks_df = pd.DataFrame(st.session_state.tasks)
                
                return True
        
        return False
    
    def update_task_status(self, task_id: int, status: str, progress_percentage: int = None) -> bool:
        """
        Update the status of a task with optional progress percentage
        """
        for task in st.session_state.tasks:
            if task["TaskID"] == task_id:
                prev_status = task["Status"]
                task["Status"] = status
                task["Last_Updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Update progress percentage if provided
                if progress_percentage is not None:
                    task["Progress"] = progress_percentage
                elif "Progress" not in task:
                    # Initialize progress based on status
                    if status == "Not Started":
                        task["Progress"] = 0
                    elif status == "In Progress":
                        task["Progress"] = 25
                    elif status == "Completed":
                        task["Progress"] = 100
                    else:  # Blocked
                        task["Progress"] = task.get("Progress", 25)  # Keep existing or default to 25%
                
                # If task is completed, increment employee's completed task count
                if status == "Completed" and prev_status != "Completed" and task["Assigned_To"] is not None:
                    employee_id = task["Assigned_To"]
                    employee_idx = self.employee_df.index[self.employee_df['ID'] == employee_id].tolist()[0]
                    self.employee_df.at[employee_idx, 'CompletedTasks'] += 1
                    self.employee_df.at[employee_idx, 'TaskCount'] -= 1
                    
                    # Update employee status if needed
                    new_task_count = self.employee_df.at[employee_idx, 'TaskCount']
                    if new_task_count == 0:
                        self.employee_df.at[employee_idx, 'Status'] = 'Unassigned'
                    elif 1 <= new_task_count <= 3:
                        self.employee_df.at[employee_idx, 'Status'] = 'Partially Assigned'
                    
                    # Send email notification about task completion
                    employee_email = self.employee_df.at[employee_idx, 'Email']
                    employee_name = self.employee_df.at[employee_idx, 'Name']
                    
                    email_subject = f"Task Completed: {task['Description'][:30]}..."
                    email_message = f"""
                    <html>
                    <body>
                        <h2>Task Completed</h2>
                        <p>Hello {employee_name},</p>
                        <p>You have successfully completed the following task:</p>
                        <div style="background-color:#f0f0f0; padding:15px; border-radius:5px;">
                            <p><strong>Task ID:</strong> {task_id}</p>
                            <p><strong>Description:</strong> {task['Description']}</p>
                            <p><strong>Completion Date:</strong> {task['Last_Updated']}</p>
                        </div>
                        <p>Thank you for your hard work!</p>
                        <p>Best regards,<br>Task Management System</p>
                    </body>
                    </html>
                    """
                    
                    self.send_email_notification(employee_email, email_subject, email_message)
                
                # If task status has changed from previous status, send notification
                elif status != prev_status and task["Assigned_To"] is not None and status != "Completed":
                    employee_id = task["Assigned_To"]
                    employee_idx = self.employee_df.index[self.employee_df['ID'] == employee_id].tolist()[0]
                    employee_email = self.employee_df.at[employee_idx, 'Email']
                    employee_name = self.employee_df.at[employee_idx, 'Name']
                    
                    email_subject = f"Task Status Update: {task['Description'][:30]}..."
                    email_message = f"""
                    <html>
                    <body>
                        <h2>Task Status Update</h2>
                        <p>Hello {employee_name},</p>
                        <p>The status of your task has been updated:</p>
                        <div style="background-color:#f0f0f0; padding:15px; border-radius:5px;">
                            <p><strong>Task ID:</strong> {task_id}</p>
                            <p><strong>Description:</strong> {task['Description']}</p>
                            <p><strong>Previous Status:</strong> {prev_status}</p>
                            <p><strong>New Status:</strong> {status}</p>
                            <p><strong>Progress:</strong> {task['Progress']}%</p>
                            <p><strong>Last Updated:</strong> {task['Last_Updated']}</p>
                        </div>
                        <p>Please log in to the Task Management System to view more details.</p>
                        <p>Thank you,<br>Task Management System</p>
                    </body>
                    </html>
                    """
                    
                    self.send_email_notification(employee_email, email_subject, email_message)
                
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

import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
from data_handler import DataHandler
from task_matcher import TaskMatcher
from employee_management import EmployeeManagement
from components import create_sidebar_navigation, employee_card, task_card, display_leaderboard
from employee_interface import login_screen, employee_task_dashboard, notifications_view

# Setup page config
st.set_page_config(
    page_title="AI Employee Task Assignment System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'active_section' not in st.session_state:
    st.session_state.active_section = "Assign Task"

if 'selected_employee' not in st.session_state:
    st.session_state.selected_employee = None
    
if 'task_to_assign' not in st.session_state:
    st.session_state.task_to_assign = None
    
if 'employee_data_loaded' not in st.session_state:
    st.session_state.employee_data_loaded = False
    
if 'tasks' not in st.session_state:
    st.session_state.tasks = []
    
if 'task_counter' not in st.session_state:
    st.session_state.task_counter = 1

# Initialize app components
@st.cache_resource
def initialize_components():
    data_handler = DataHandler()
    task_matcher = TaskMatcher()
    employee_manager = EmployeeManagement()
    return data_handler, task_matcher, employee_manager

data_handler, task_matcher, employee_manager = initialize_components()

# Function to change active section
def change_section(section):
    st.session_state.active_section = section
    st.session_state.selected_employee = None
    st.session_state.task_to_assign = None

# Define navigation sections
navigation_sections = [
    "Assign Task", 
    "Search by Skills", 
    "View All Employees", 
    "View Assigned Tasks", 
    "Performance Leaderboard", 
    "Employee Preferences",
    "Employee Access"
]

# Create sidebar navigation
create_sidebar_navigation(navigation_sections, st.session_state.active_section, change_section)

# Main title
st.title("AI Employee Task Assignment System")

# Load employee data if not loaded yet
if not st.session_state.employee_data_loaded:
    # Check if the file exists and load it
    default_file_path = "attached_assets/employee_positions_dataset.csv"
    
    if os.path.exists(default_file_path):
        if data_handler.load_employee_data(default_file_path):
            st.success("Employee data loaded successfully!")
            # Update the matcher and manager with employee data
            task_matcher.set_employee_data(data_handler.employee_df)
            employee_manager.set_employee_data(data_handler.employee_df)
    else:
        # If file doesn't exist, show file uploader
        uploaded_file = st.file_uploader("Upload employee dataset (CSV)", type=["csv"])
        
        if uploaded_file is not None:
            # Save the uploaded file
            with open("employee_data.csv", "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            if data_handler.load_employee_data("employee_data.csv"):
                st.success("Employee data loaded successfully!")
                # Update the matcher and manager with employee data
                task_matcher.set_employee_data(data_handler.employee_df)
                employee_manager.set_employee_data(data_handler.employee_df)

# Main content based on active section
if st.session_state.active_section == "Assign Task":
    st.header("Assign a Task")
    
    st.write("Enter task details to find the best matching employee")
    
    with st.form(key="task_form"):
        task_description = st.text_area("Task Description")
        
        # Get all available skills from loaded employee data
        available_skills = data_handler.get_all_skills()
        
        required_skills = st.multiselect("Required Skills", available_skills)
        
        cols = st.columns(3)
        with cols[0]:
            priority = st.selectbox("Priority", ["Low", "Medium", "High"])
        
        with cols[1]:
            experience_preference = st.selectbox(
                "Preferred Experience Level", 
                ["Any", "Junior", "Mid-Level", "Senior", "Expert"]
            )
        
        with cols[2]:
            due_date = st.date_input(
                "Due Date", 
                datetime.now().date() + timedelta(days=7)
            )
        
        submit_task = st.form_submit_button("Find Matching Employees")
    
    if submit_task and task_description and required_skills:
        # Add the task
        task_id = data_handler.add_task(
            description=task_description,
            required_skills=required_skills,
            due_date=due_date.strftime("%Y-%m-%d") if due_date else None,
            priority=priority
        )
        
        # Find matching employees
        matching_employees = task_matcher.find_matching_employees(
            required_skills=required_skills,
            experience_level=None if experience_preference == "Any" else experience_preference
        )
        
        # Show matching results
        if len(matching_employees) > 0:
            st.subheader(f"Found {len(matching_employees)} matching employees")
            
            # Show best match with highlight
            best_match = task_matcher.recommend_best_match(
                required_skills=required_skills,
                experience_preference=None if experience_preference == "Any" else experience_preference
            )
            
            if best_match:
                st.info(f"Best match: {best_match['Name']} - {best_match['Position']} ({best_match['MatchPercentage']:.1f}% skill match)")
            
            # Display all matches
            for idx, employee in matching_employees.iterrows():
                with st.container():
                    cols = st.columns([3, 2, 1, 1])
                    
                    with cols[0]:
                        st.write(f"**{employee['Name']}**")
                        st.caption(f"{employee['Role']} - {employee['Position']}")
                    
                    with cols[1]:
                        st.write(f"**Skills match: {employee['MatchPercentage']:.1f}%**")
                        st.caption(f"Experience: {employee['Experience']}")
                    
                    with cols[2]:
                        status_color = {
                            "Unassigned": "green",
                            "Partially Assigned": "orange",
                            "Fully Assigned": "red"
                        }.get(employee['Status'], "gray")
                        
                        st.markdown(f"<span style='color:{status_color};'>●</span> {employee['Status']}", unsafe_allow_html=True)
                        st.caption(f"Tasks: {employee['TaskCount']}")
                    
                    with cols[3]:
                        if st.button("Assign", key=f"assign_{employee['ID']}_{task_id}"):
                            if data_handler.assign_task(task_id, employee['ID']):
                                st.success(f"Task assigned to {employee['Name']}")
                                # Update the employee data in the matcher and manager
                                task_matcher.set_employee_data(data_handler.employee_df)
                                employee_manager.set_employee_data(data_handler.employee_df)
                                st.rerun()
                    
                    st.divider()
        else:
            st.warning("No matching employees found for the required skills")

elif st.session_state.active_section == "Search by Skills":
    st.header("Search Employees by Skills")
    
    # Get all available skills
    available_skills = data_handler.get_all_skills()
    
    # Skill selection
    selected_skill = st.selectbox("Select a skill to find employees", available_skills)
    
    if selected_skill:
        # Find employees with the selected skill
        matching_employees = task_matcher.find_employees_by_skill(selected_skill)
        
        if len(matching_employees) > 0:
            st.subheader(f"Found {len(matching_employees)} employees with {selected_skill} skill")
            
            # Display matching employees
            for idx, employee in matching_employees.iterrows():
                employee_card(employee)
                st.divider()
        else:
            st.info(f"No employees found with {selected_skill} skill")

elif st.session_state.active_section == "View All Employees":
    st.header("All Employees")
    
    if data_handler.employee_df is not None:
        # Filters
        with st.expander("Filters", expanded=False):
            cols = st.columns(3)
            
            with cols[0]:
                filter_role = st.multiselect(
                    "Filter by Role",
                    options=data_handler.employee_df['Role'].unique().tolist()
                )
            
            with cols[1]:
                filter_experience = st.multiselect(
                    "Filter by Experience",
                    options=data_handler.employee_df['Experience'].unique().tolist()
                )
            
            with cols[2]:
                filter_status = st.multiselect(
                    "Filter by Status",
                    options=data_handler.employee_df['Status'].unique().tolist()
                )
        
        # Apply filters
        filtered_df = data_handler.employee_df.copy()
        
        if filter_role:
            filtered_df = filtered_df[filtered_df['Role'].isin(filter_role)]
        
        if filter_experience:
            filtered_df = filtered_df[filtered_df['Experience'].isin(filter_experience)]
        
        if filter_status:
            filtered_df = filtered_df[filtered_df['Status'].isin(filter_status)]
        
        # Display employees
        st.write(f"Showing {len(filtered_df)} employees")
        
        for idx, employee in filtered_df.iterrows():
            employee_card(employee.to_dict())
            st.divider()
    else:
        st.info("No employee data available. Please load employee data first.")

elif st.session_state.active_section == "View Assigned Tasks":
    st.header("Assigned Tasks")
    
    # Get all tasks
    all_tasks = data_handler.get_all_tasks()
    
    if not all_tasks:
        st.info("No tasks have been assigned yet.")
    else:
        # Filter options
        task_status_filter = st.multiselect(
            "Filter by Status",
            options=["Not Started", "In Progress", "Completed", "Blocked"],
            default=[]
        )
        
        # Apply filters
        filtered_tasks = all_tasks
        if task_status_filter:
            filtered_tasks = [task for task in all_tasks if task["Status"] in task_status_filter]
        
        # Display tasks
        st.write(f"Showing {len(filtered_tasks)} tasks")
        
        for task in filtered_tasks:
            # Handler for status change
            def update_task_status(task_id, new_status, progress=None):
                if data_handler.update_task_status(task_id, new_status, progress):
                    st.success(f"Task #{task_id} status updated to {new_status}")
                    task_matcher.set_employee_data(data_handler.employee_df)
                    employee_manager.set_employee_data(data_handler.employee_df)
                    st.rerun()
            
            task_card(
                task, 
                data_handler.employee_df, 
                on_status_change=update_task_status
            )

elif st.session_state.active_section == "Performance Leaderboard":
    st.header("Performance Leaderboard")
    
    # Get leaderboard data
    leaderboard_data = data_handler.get_leaderboard_data()
    
    # Display leaderboard
    display_leaderboard(leaderboard_data)

elif st.session_state.active_section == "Employee Preferences":
    st.header("Employee Preferences")
    
    if data_handler.employee_df is not None:
        # Employee selection
        employee_id = st.selectbox(
            "Select Employee",
            options=data_handler.employee_df['ID'].tolist(),
            format_func=lambda x: f"{data_handler.employee_df[data_handler.employee_df['ID'] == x].iloc[0]['Name']} (ID: {x})"
        )
        
        if employee_id:
            employee = employee_manager.get_employee_by_id(employee_id)
            
            if employee:
                st.subheader(f"Preferences for {employee['Name']}")
                
                # Preferences form
                with st.form(key=f"preferences_{employee_id}"):
                    # Preferred working hours
                    preferred_hours = st.slider(
                        "Preferred Working Hours per Day",
                        min_value=4,
                        max_value=12,
                        value=employee_manager.get_employee_preference(employee_id, "preferred_hours") or 8,
                        step=1
                    )
                    
                    # Preferred task types
                    all_roles = data_handler.employee_df['Role'].unique().tolist()
                    preferred_tasks = st.multiselect(
                        "Preferred Task Types",
                        options=all_roles,
                        default=employee_manager.get_employee_preference(employee_id, "preferred_tasks") or []
                    )
                    
                    # Communication preferences
                    communication_preference = st.selectbox(
                        "Preferred Communication Channel",
                        options=["Email", "Slack", "Teams", "Phone"],
                        index=["Email", "Slack", "Teams", "Phone"].index(
                            employee_manager.get_employee_preference(employee_id, "communication_preference") or "Email"
                        )
                    )
                    
                    # Notification preferences
                    notification_preferences = st.multiselect(
                        "Notification Preferences",
                        options=["New Task Assignments", "Task Status Updates", "Deadline Reminders", "Performance Reports"],
                        default=employee_manager.get_employee_preference(employee_id, "notification_preferences") or [
                            "New Task Assignments", "Deadline Reminders"
                        ]
                    )
                    
                    # Submit button
                    if st.form_submit_button("Save Preferences"):
                        # Save all preferences
                        employee_manager.set_employee_preference(employee_id, "preferred_hours", preferred_hours)
                        employee_manager.set_employee_preference(employee_id, "preferred_tasks", preferred_tasks)
                        employee_manager.set_employee_preference(employee_id, "communication_preference", communication_preference)
                        employee_manager.set_employee_preference(employee_id, "notification_preferences", notification_preferences)
                        
                        st.success(f"Preferences saved for {employee['Name']}")
                
                # Skills management
                st.subheader("Skills Management")
                
                with st.container():
                    cols = st.columns([2, 1])
                    
                    with cols[0]:
                        st.write("Current Skills:")
                        current_skills = employee['Skills']
                        for skill in current_skills:
                            st.write(f"- {skill}")
                    
                    with cols[1]:
                        # Add new skill
                        all_skills = data_handler.get_all_skills()
                        new_skill = st.selectbox(
                            "Add New Skill",
                            options=[skill for skill in all_skills if skill not in current_skills]
                        )
                        
                        if st.button("Add Skill"):
                            if employee_manager.update_employee_skill(employee_id, new_skill, add=True):
                                st.success(f"Added {new_skill} to {employee['Name']}'s skills")
                                # Update employee data in task matcher
                                task_matcher.set_employee_data(data_handler.employee_df)
                                st.rerun()
                        
                        # Remove skill
                        skill_to_remove = st.selectbox(
                            "Remove Skill",
                            options=current_skills
                        )
                        
                        if st.button("Remove Skill"):
                            if employee_manager.update_employee_skill(employee_id, skill_to_remove, add=False):
                                st.success(f"Removed {skill_to_remove} from {employee['Name']}'s skills")
                                # Update employee data in task matcher
                                task_matcher.set_employee_data(data_handler.employee_df)
                                st.rerun()
            else:
                st.error("Employee not found")
    else:
        st.info("No employee data available. Please load employee data first.")

elif st.session_state.active_section == "Employee Access":
    st.header("Employee Portal")
    
    # Initialize employee login session state
    if 'logged_in_employee_id' not in st.session_state:
        st.session_state.logged_in_employee_id = None
    
    if 'employee_view' not in st.session_state:
        st.session_state.employee_view = "Tasks"  # Default view
    
    # If not logged in, show login screen
    if st.session_state.logged_in_employee_id is None:
        employee_id = login_screen()
        
        if employee_id:
            # Verify employee exists
            if data_handler.employee_df is not None and employee_id in data_handler.employee_df['ID'].values:
                st.session_state.logged_in_employee_id = employee_id
                st.rerun()
            else:
                st.error("Employee ID not found. Please try again.")
    else:
        # Employee is logged in
        employee_id = st.session_state.logged_in_employee_id
        employee_data = employee_manager.get_employee_by_id(employee_id)
        
        if employee_data:
            # Navigation tabs for employee portal
            tabs, tab_view = st.tabs(["My Tasks", "Notifications", "Logout"])
            
            with tabs[0]:
                if st.session_state.employee_view == "Tasks":
                    # Get tasks assigned to this employee
                    employee_tasks = data_handler.get_employee_tasks(employee_id)
                    
                    # Create handler for task updates
                    def handle_task_update(task_id, new_status, progress):
                        if data_handler.update_task_status(task_id, new_status, progress):
                            st.success(f"Task #{task_id} status updated to {new_status}")
                            st.rerun()
                    
                    # Display employee dashboard
                    employee_task_dashboard(
                        employee_id=employee_id,
                        employee_data=employee_data,
                        tasks=employee_tasks,
                        on_task_update=handle_task_update
                    )
            
            with tabs[1]:
                if st.session_state.employee_view == "Notifications":
                    # Filter emails for this employee
                    if 'sent_emails' in st.session_state:
                        employee_email = employee_data.get('Email')
                        employee_emails = [
                            email for email in st.session_state.sent_emails 
                            if email.get('to') == employee_email
                        ]
                        notifications_view(employee_emails)
                    else:
                        st.info("No notifications available.")
            
            with tabs[2]:
                if st.button("Logout", key="employee_logout"):
                    st.session_state.logged_in_employee_id = None
                    st.session_state.employee_view = "Tasks"
                    st.rerun()
        else:
            st.error("Could not load employee information. Please log in again.")
            st.session_state.logged_in_employee_id = None
            if st.button("Back to Login"):
                st.rerun()

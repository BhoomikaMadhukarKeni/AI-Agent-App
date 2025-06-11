import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
from data_handler import DataHandler
from task_matcher import TaskMatcher
from employee_management import EmployeeManagement
from components import create_top_navigation, employee_card, task_card, display_leaderboard, display_ai_performance_metrics
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
    st.session_state.active_section = "Auto-Assign Task"

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
    
if 'ai_predictions' not in st.session_state:
    st.session_state.ai_predictions = []

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
    "Auto-Assign Task", 
    "Search by Skills", 
    "View All Employees", 
    "View Assigned Tasks", 
    "Performance Leaderboard", 
    "Employee Preferences",
    "Employee Access",
    "AI Training"
]

# Create top navigation
create_top_navigation(navigation_sections, st.session_state.active_section, change_section)

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
if st.session_state.active_section == "Auto-Assign Task":
    st.header("Create & Auto-Assign Task")
    
    st.write("Enter task details to automatically assign it to the best matching employee")
    
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
            
        auto_assign = st.checkbox("Auto-assign to best matching employee", value=True,
                                help="When enabled, the task will be automatically assigned to the best available employee")
        
        submit_task = st.form_submit_button("Create Task")
    
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
            # Get the best match using AI recommendation
            best_match = task_matcher.recommend_best_match(
                required_skills=required_skills,
                experience_preference=None if experience_preference == "Any" else experience_preference
            )
            
            # Auto-assign if enabled
            if auto_assign and best_match:
                ai_powered = best_match.get('AI_Powered', False)
                match_score = best_match.get('MatchPercentage', 0) / 100.0
                
                # Record AI prediction for tracking
                if ai_powered:
                    data_handler.record_ai_prediction(task_id, best_match['ID'], match_score)
                
                # Assign the task automatically
                if data_handler.assign_task(task_id, best_match['ID'], ai_powered, match_score):
                    st.success(f"✅ Task automatically assigned to {best_match['Name']} ({best_match['MatchPercentage']:.1f}% match)")
                    
                    # Update the employee data
                    task_matcher.set_employee_data(data_handler.employee_df)
                    employee_manager.set_employee_data(data_handler.employee_df)
                    
                    # Show assignment details
                    st.info(f"🤖 **AI-Powered Assignment**" if ai_powered else "**Best Match Assignment**")
                    with st.expander("Assignment Details"):
                        st.write(f"**Employee:** {best_match['Name']} - {best_match['Position']}")
                        st.write(f"**Match Score:** {best_match['MatchPercentage']:.1f}%")
                        st.write(f"**Skills:** {', '.join(best_match['Skills'])}")
                        st.write(f"**Experience:** {best_match['Experience']}")
                        st.write(f"**Current Workload:** {best_match['TaskCount']} tasks")
            
            # If not auto-assigning, show all matching employees
            elif not auto_assign:
                st.subheader(f"Found {len(matching_employees)} matching employees")
                
                # Show best match with highlight
                if best_match:
                    ai_powered = best_match.get('AI_Powered', False)
                    match_text = f"Best match: {best_match['Name']} - {best_match['Position']} ({best_match['MatchPercentage']:.1f}% skill match)"
                    
                    if ai_powered:
                        st.info(f"🤖 AI RECOMMENDED: {match_text}")
                    else:
                        st.info(match_text)
                    
                    # Option to directly assign to best match
                    col1, col2 = st.columns([3, 1])
                    with col2:
                        if st.button(f"Assign to {best_match['Name']}", key=f"auto_assign_{task_id}"):
                            # Get match score for tracking performance
                            match_score = best_match.get('MatchPercentage', 0) / 100.0
                            
                            # Record AI prediction for tracking
                            if ai_powered:
                                data_handler.record_ai_prediction(task_id, best_match['ID'], match_score)
                            
                            # Assign the task
                            if data_handler.assign_task(task_id, best_match['ID'], ai_powered, match_score):
                                st.success(f"Task assigned to {best_match['Name']}")
                                # Update the employee data in the matcher and manager
                                task_matcher.set_employee_data(data_handler.employee_df)
                                employee_manager.set_employee_data(data_handler.employee_df)
                                st.rerun()
            
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
                            # Not an AI recommendation, manual assignment
                            match_score = employee['MatchPercentage'] / 100.0 if 'MatchPercentage' in employee else 0.0
                            if data_handler.assign_task(task_id, employee['ID'], False, match_score):
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
                    
                    # If task is completed, update AI prediction success
                    if new_status == "Completed":
                        # Mark AI prediction as successful
                        data_handler.update_ai_prediction_success(task_id, True)
                    
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
            selected_tab = st.session_state.get("employee_view", "Tasks")
            st.session_state.employee_view = selected_tab

            tabs = st.tabs(["My Tasks", "Notifications", "Logout"])
            
            with tabs[0]:
                if st.session_state.get("employee_view", "") == "Tasks":
                    # Get tasks assigned to this employee
                    employee_tasks = data_handler.get_employee_tasks(employee_id)
                    
                    # Create handler for task updates
                    def handle_task_update(task_id, new_status, progress):
                        if data_handler.update_task_status(task_id, new_status, progress):
                            st.success(f"Task #{task_id} status updated to {new_status}")
                            
                            # If task is completed, update AI prediction success
                            if new_status == "Completed":
                                # Mark AI prediction as successful
                                data_handler.update_ai_prediction_success(task_id, True)
                                
                            st.rerun()
                    
                    # Display employee dashboard
                    employee_task_dashboard(
                        employee_id=employee_id,
                        employee_data=employee_data,
                        tasks=employee_tasks,
                        on_task_update=handle_task_update
                    )
            
            with tabs[1]:
                if st.session_state.get("employee_view", "") == "Notifications":
                    # Filter emails for this employee
                    if 'sent_emails' in st.session_state:
                        employee_email = employee_data.get('Email', '')
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

elif st.session_state.active_section == "AI Training":
    st.header("AI Task Assignment Model")
    
    st.write("""
    This page allows you to train and manage the AI task assignment models. 
    The system uses two types of models:
    1. **Machine Learning Model**: A Random Forest model that learns from completed tasks
    2. **Skill Similarity Model**: A simpler model that uses TF-IDF and cosine similarity
    """)
    
    # Check if we have task data for training
    all_tasks = data_handler.get_all_tasks()
    completed_tasks = [task for task in all_tasks if task["Status"] == "Completed"]
    
    # Update task data in the task matcher
    task_matcher.set_tasks_data(data_handler.tasks_df)
    
    # Training section
    st.subheader("Model Training")
    
    # Display stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Employees", len(data_handler.employee_df) if data_handler.employee_df is not None else 0)
    with col2:
        st.metric("Total Tasks", len(all_tasks))
    with col3:
        st.metric("Completed Tasks", len(completed_tasks))
    
    # Training button for ML model
    st.write("Machine Learning models require sufficient completed task data to be trained effectively.")
    
    if len(completed_tasks) >= 5:
        if st.button("Train AI Assignment Model"):
            with st.spinner("Training the model with historical task data..."):
                if task_matcher.train_prediction_model():
                    st.success("AI model trained successfully!")
                else:
                    st.error("Failed to train the model. Not enough data or an error occurred.")
    else:
        st.warning(f"Need at least 5 completed tasks to train the ML model. Currently have {len(completed_tasks)}.")
        st.info("The system will automatically use the Skill Similarity model until enough data is available.")
    
    # Model testing section
    st.subheader("Model Testing")
    
    # Create a test task
    st.write("Create a test task to see AI-recommended employee matches:")
    
    # Get all available skills from loaded employee data
    available_skills = data_handler.get_all_skills()
    
    test_skills = st.multiselect("Required Skills", available_skills, key="test_skills")
    priority = st.selectbox("Priority", ["Low", "Medium", "High"], key="test_priority")
    
    if test_skills:
        # Create a test task
        test_task = {
            "Required_Skills": test_skills,
            "Priority": priority,
            "Status": "Not Started"
        }
        
        # Get AI matches
        ai_matches = task_matcher.find_ai_matches(test_task)
        
        if ai_matches is not None and len(ai_matches) > 0:
            st.subheader("AI-Recommended Matches")
            
            # Display the AI method used
            if 'AI_Method' in ai_matches.columns:
                ai_method = ai_matches.iloc[0]['AI_Method']
                st.info(f"Matches generated using: {ai_method}")
            
            # Display top matches
            for idx, employee in ai_matches.head(5).iterrows():
                with st.container():
                    cols = st.columns([3, 2, 1])
                    
                    with cols[0]:
                        st.write(f"**{employee['Name']}**")
                        st.caption(f"{employee['Role']} - {employee['Position']}")
                    
                    with cols[1]:
                        match_score = employee.get('PredictionScore', employee.get('SimilarityScore', 0)) * 100
                        st.write(f"**Match Score: {match_score:.1f}%**")
                        st.caption(f"Experience: {employee['Experience']}")
                    
                    with cols[2]:
                        status_color = {
                            "Unassigned": "green",
                            "Partially Assigned": "orange",
                            "Fully Assigned": "red"
                        }.get(employee['Status'], "gray")
                        
                        st.markdown(f"<span style='color:{status_color};'>●</span> {employee['Status']}", unsafe_allow_html=True)
                        st.caption(f"Tasks: {employee['TaskCount']}")
                    
                    st.divider()
        else:
            st.warning("No matching employees found for the selected skills")
    
    # AI Performance Metrics
    st.subheader("AI Performance Metrics")
    
    # Get AI prediction data
    ai_prediction_data = data_handler.get_ai_performance_data()
    
    # Get completed tasks for comparison
    completed_tasks = [task for task in all_tasks if task.get("Status") == "Completed"]
    
    # Display AI metrics and visualizations
    display_ai_performance_metrics(ai_prediction_data, completed_tasks)
    
    # Model explanation
    with st.expander("How the AI Models Work"):
        st.write("""
        ### Machine Learning Model
        
        The Machine Learning model uses historical task assignments to learn which employees
        are the best match for specific tasks. It considers factors such as:
        
        - Skill match score between employee and task
        - Employee experience level
        - Task priority
        - Employee's current workload
        - Employee's completed task count
        
        The model uses a Random Forest classifier which is trained on successfully completed tasks.
        
        ### Skill Similarity Model
        
        For cases where there isn't enough historical data, the system uses a simpler model based on:
        
        - TF-IDF vectorization of employee skills
        - Cosine similarity between task requirements and employee skill sets
        - Current workload adjustment
        
        This model doesn't require training data and can work immediately with the current employee dataset.
        """)
    
    # Performance monitoring
    st.subheader("Performance Monitoring")
    
    st.write("""
    As more tasks are assigned and completed, the AI will continue to learn and improve.
    The system automatically adjusts between the ML and similarity models based on available data.
    """)
    
    # Placeholder for future performance metrics visualization
    if len(completed_tasks) > 0:
        st.write("Task completion time by employee (days):")
        
        # Calculate average completion time per employee
        completion_data = {}
        for task in completed_tasks:
            if 'Assigned_To' in task and task['Assigned_To'] is not None:
                emp_id = task['Assigned_To']
                assigned_date = task.get('Assigned_Date')
                completion_date = task.get('Completion_Date')
                
                if assigned_date and completion_date:
                    assigned_date = datetime.strptime(assigned_date, "%Y-%m-%d")
                    completion_date = datetime.strptime(completion_date, "%Y-%m-%d")
                    days_taken = (completion_date - assigned_date).days
                    
                    if emp_id not in completion_data:
                        completion_data[emp_id] = []
                    
                    completion_data[emp_id].append(days_taken)
        
        if completion_data:
            # Calculate averages
            avg_completion = {emp_id: sum(days)/len(days) for emp_id, days in completion_data.items()}
            
            # Create chart data
            chart_data = []
            for emp_id, avg_days in avg_completion.items():
                employee = employee_manager.get_employee_by_id(emp_id)
                if employee:
                    chart_data.append({
                        "Employee": employee['Name'],
                        "Average Days": avg_days
                    })
            
            if chart_data:
                chart_df = pd.DataFrame(chart_data)
                st.bar_chart(chart_df.set_index("Employee"))
    else:
        st.info("Performance metrics will be available once tasks are completed.")
        
    # AI Prediction Metrics
    st.subheader("AI Recommendation Analysis")
    
    # Get AI prediction data
    prediction_data = data_handler.get_ai_performance_data()
    
    if prediction_data:
        # Calculate overall metrics
        ai_success_rate = data_handler.get_ai_success_rate() * 100
        
        # Display metrics
        st.write(f"Overall AI recommendation success rate: **{ai_success_rate:.1f}%**")
        
        # Show the prediction history
        st.markdown("### AI Prediction History")
        
        # Create a dataframe for visualization
        evaluated_predictions = [p for p in prediction_data if p["success"] is not None]
        
        if not evaluated_predictions:
            st.info("No AI predictions have been evaluated yet. Once tasks that were assigned by AI are completed, you'll see detailed performance metrics here.")
    else:
        st.info("No AI prediction data available yet. Use the AI-recommended assignments to generate performance data.")

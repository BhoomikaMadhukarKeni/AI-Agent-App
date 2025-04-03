import streamlit as st
import pandas as pd
from typing import Optional, Dict, Any, List, Callable
from components import task_card

def login_screen() -> Optional[int]:
    """
    Display a login screen for employees to access their tasks
    """
    st.header("Employee Login")
    st.write("Please enter your employee ID to access your tasks.")
    
    employee_id = st.number_input("Employee ID", min_value=1, max_value=9999, step=1)
    
    if st.button("Login"):
        # For a real implementation, add authentication
        return int(employee_id)
    
    return None

def employee_task_dashboard(
    employee_id: int, 
    employee_data: Dict[str, Any], 
    tasks: List[Dict[str, Any]],
    on_task_update: Callable[[int, str, int], None]
) -> None:
    """
    Display the employee task dashboard with all assigned tasks
    """
    st.header(f"Hello, {employee_data['Name']}!")
    
    # Employee information
    with st.container():
        cols = st.columns([2, 1])
        with cols[0]:
            st.subheader("Your Information")
            st.write(f"**Role:** {employee_data['Role']}")
            st.write(f"**Position:** {employee_data['Position']}")
            st.write(f"**Experience:** {employee_data['Experience']}")
            st.write(f"**Skills:** {', '.join(employee_data['Skills'])}")
        
        with cols[1]:
            status_color = {
                "Unassigned": "green",
                "Partially Assigned": "orange",
                "Fully Assigned": "red"
            }.get(employee_data['Status'], "gray")
            
            st.subheader("Work Status")
            st.markdown(f"<span style='color:{status_color};'>●</span> {employee_data['Status']}", unsafe_allow_html=True)
            st.write(f"**Active Tasks:** {employee_data['TaskCount']}")
            st.write(f"**Completed Tasks:** {employee_data['CompletedTasks']}")
    
    st.divider()
    
    # Tasks section
    st.subheader("Your Tasks")
    
    if not tasks:
        st.info("You don't have any assigned tasks at the moment.")
        return
    
    # Filter options
    task_status_filter = st.multiselect(
        "Filter by Status",
        options=["Not Started", "In Progress", "Completed", "Blocked"],
        default=["Not Started", "In Progress"]
    )
    
    # Apply filters
    filtered_tasks = tasks
    if task_status_filter:
        filtered_tasks = [task for task in tasks if task["Status"] in task_status_filter]
    
    # Task count
    total_tasks = len(tasks)
    active_tasks = len([t for t in tasks if t["Status"] not in ["Completed"]])
    completed_tasks = len([t for t in tasks if t["Status"] == "Completed"])
    
    # Stats
    stats_cols = st.columns(3)
    with stats_cols[0]:
        st.metric("Total Tasks", total_tasks)
    with stats_cols[1]:
        st.metric("Active Tasks", active_tasks)
    with stats_cols[2]:
        st.metric("Completed Tasks", completed_tasks)
    
    # Display filtered tasks
    st.write(f"Showing {len(filtered_tasks)} tasks")
    
    for task in filtered_tasks:
        # Create a handler for the task status update
        def handle_task_update(task_id, new_status, progress):
            on_task_update(task_id, new_status, progress)
        
        task_card(
            task=task,
            on_status_change=handle_task_update,
            employee_view=True
        )

def notifications_view(emails: List[Dict[str, Any]]) -> None:
    """
    Display all email notifications received by the employee
    """
    st.header("Notifications")
    
    if not emails:
        st.info("You don't have any notifications.")
        return
    
    # Sort emails by timestamp (newest first)
    sorted_emails = sorted(emails, key=lambda x: x['timestamp'], reverse=True)
    
    for email in sorted_emails:
        with st.expander(f"{email['subject']} - {email['timestamp']}"):
            st.write(f"**From:** Task Management System")
            st.write(f"**To:** {email['to']}")
            st.write(f"**Date:** {email['timestamp']}")
            st.write(f"**Subject:** {email['subject']}")
            st.divider()
            st.markdown(email['message'], unsafe_allow_html=True)
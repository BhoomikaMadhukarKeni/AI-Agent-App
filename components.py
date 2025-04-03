import streamlit as st
import pandas as pd
from typing import List, Dict, Any, Optional, Callable

def create_sidebar_navigation(sections: List[str], active_section: str, on_section_change: Callable[[str], None]) -> None:
    """
    Create a sidebar for navigation
    """
    with st.sidebar:
        st.title("Navigation")
        for section in sections:
            if st.button(section, key=f"nav_{section}", 
                        help=f"Navigate to {section}",
                        use_container_width=True,
                        type="primary" if section == active_section else "secondary"):
                on_section_change(section)

def employee_card(employee: Dict[str, Any], on_select: Optional[Callable[[Dict[str, Any]], None]] = None) -> None:
    """
    Display an employee card with details
    """
    with st.container():
        cols = st.columns([3, 2, 2, 1])
        
        # Main info
        with cols[0]:
            st.write(f"**{employee['Name']}**")
            st.caption(f"{employee['Role']} - {employee['Position']}")
        
        # Experience level
        with cols[1]:
            st.write("**Experience:**")
            st.caption(employee['Experience'])
        
        # Skills
        with cols[2]:
            st.write("**Skills:**")
            skills_text = ", ".join(employee['Skills'][:3])
            if len(employee['Skills']) > 3:
                skills_text += f" (+{len(employee['Skills']) - 3} more)"
            st.caption(skills_text)
        
        # Status and action
        with cols[3]:
            status_color = {
                "Unassigned": "green",
                "Partially Assigned": "orange",
                "Fully Assigned": "red"
            }.get(employee.get('Status', 'Unassigned'), "gray")
            
            st.markdown(f"<span style='color:{status_color};'>●</span> {employee.get('Status', 'Unassigned')}", unsafe_allow_html=True)
            
            if on_select:
                if st.button("Select", key=f"select_emp_{employee['ID']}"):
                    on_select(employee)

def task_card(task: Dict[str, Any], employees_df: Optional[pd.DataFrame] = None, 
             on_status_change: Optional[Callable[[int, str, int], None]] = None,
             on_assign: Optional[Callable[[int], None]] = None,
             employee_view: bool = False) -> None:
    """
    Display a task card with details
    """
    status_color = {
        "Not Started": "gray",
        "In Progress": "blue",
        "Completed": "green",
        "Blocked": "red"
    }.get(task['Status'], "gray")
    
    with st.container():
        st.divider()
        
        # Determine layout based on view type
        if employee_view:
            cols = st.columns([3, 1, 2])
        else:
            cols = st.columns([3, 2, 1, 1])
            
        # Task description and skills
        with cols[0]:
            st.write(f"**Task #{task['TaskID']}**")
            st.write(task['Description'])
            st.caption(f"Required Skills: {', '.join(task['Required_Skills'])}")
            
            # Display additional details for employee view
            if employee_view:
                if 'Assigned_Date' in task:
                    st.caption(f"Assigned on: {task['Assigned_Date']}")
                if 'Due_Date' in task and task['Due_Date']:
                    st.caption(f"Due Date: {task['Due_Date']}")
                if 'Priority' in task:
                    priority_color = {
                        "Low": "green",
                        "Medium": "orange",
                        "High": "red"
                    }.get(task['Priority'], "gray")
                    st.markdown(f"Priority: <span style='color:{priority_color};'>{task['Priority']}</span>", unsafe_allow_html=True)
        
        # Assigned to (only in manager view)
        if not employee_view and cols[1] is not None:
            with cols[1]:
                st.write("**Assigned To:**")
                if task['Assigned_To'] is not None and employees_df is not None:
                    employee = employees_df[employees_df['ID'] == task['Assigned_To']]
                    if len(employee) > 0:
                        st.caption(f"{employee.iloc[0]['Name']} ({employee.iloc[0]['Role']})")
                else:
                    st.caption("Not assigned")
        
        # Status and Progress
        if employee_view:
            with cols[1]:
                st.write("**Status:**")
                st.markdown(f"<span style='color:{status_color};'>●</span> {task['Status']}", unsafe_allow_html=True)
                
                # Show progress
                progress = task.get('Progress', 0)
                st.progress(progress/100)
                st.caption(f"Progress: {progress}%")
        else:
            with cols[2]:
                st.write("**Status:**")
                st.markdown(f"<span style='color:{status_color};'>●</span> {task['Status']}", unsafe_allow_html=True)
                
                # Show progress if available
                if 'Progress' in task:
                    st.progress(task['Progress']/100)
                    st.caption(f"Progress: {task['Progress']}%")
                
                if on_status_change:
                    new_status = st.selectbox(
                        "Change status",
                        ["Not Started", "In Progress", "Completed", "Blocked"],
                        index=["Not Started", "In Progress", "Completed", "Blocked"].index(task['Status']),
                        key=f"status_{task['TaskID']}"
                    )
                    
                    if new_status != task['Status']:
                        if st.button("Update", key=f"update_task_{task['TaskID']}"):
                            on_status_change(task['TaskID'], new_status, None)
        
        # Actions
        action_col = cols[2] if employee_view else cols[3]
        with action_col:
            st.write("**Actions:**")
            
            if employee_view and task['Status'] != "Completed":
                # Update progress
                progress_value = st.slider(
                    "Update Progress", 
                    min_value=0, 
                    max_value=100, 
                    value=task.get('Progress', 0),
                    step=5,
                    key=f"progress_{task['TaskID']}"
                )
                
                new_status = st.selectbox(
                    "Update Status",
                    ["Not Started", "In Progress", "Completed", "Blocked"],
                    index=["Not Started", "In Progress", "Completed", "Blocked"].index(task['Status']),
                    key=f"emp_status_{task['TaskID']}"
                )
                
                if st.button("Update Task", key=f"emp_update_{task['TaskID']}"):
                    on_status_change(task['TaskID'], new_status, progress_value)
            
            elif on_assign and task['Assigned_To'] is None:
                if st.button("Assign", key=f"assign_task_{task['TaskID']}"):
                    on_assign(task['TaskID'])
                    
            # Add Last Update timestamp if available
            if 'Last_Updated' in task:
                st.caption(f"Last updated: {task['Last_Updated']}")

def display_leaderboard(leaderboard_data: pd.DataFrame) -> None:
    """
    Display a performance leaderboard
    """
    if len(leaderboard_data) == 0:
        st.info("No performance data available yet.")
        return
    
    st.subheader("Top Performers")
    
    # Display top 10 performers
    top_performers = leaderboard_data.head(10)
    
    for i, (idx, row) in enumerate(top_performers.iterrows()):
        with st.container():
            cols = st.columns([1, 3, 2, 1])
            
            with cols[0]:
                st.write(f"**#{i+1}**")
            
            with cols[1]:
                st.write(f"**{row['Name']}**")
                st.caption(row['Role'])
            
            with cols[2]:
                st.write("**Tasks Completed**")
            
            with cols[3]:
                st.write(f"**{int(row['CompletedTasks'])}**")
            
            st.divider()

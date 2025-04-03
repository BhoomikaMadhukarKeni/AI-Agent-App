## Overview
TaskFlowBoard is an intelligent task management system that uses AI to automatically assign tasks to employees based on their skills, experience, and workload.

1.git clone <repository-url>  
2.cd <repository-name>  
3.streamlit run app.py --server.port=8501  

# If port is already in use  
lsof -ti:5000 | xargs kill -9  
streamlit run app.py --server.port=8501  

# If git push is rejected  
git pull origin main --rebase  
git push origin main  


## Features
- Automatic task assignment using AI
- Skill-based employee matching
- Performance leaderboard
- Real-time task tracking
- Employee workload management
- AI performance metrics

## Getting Started
1. Access the system through your web browser
2. Navigate using the top navigation bar
3. Create tasks in the "Auto-Assign Task" section
4. Monitor assignments in "View Assigned Tasks"
5. Track performance in "Performance Leaderboard"

## Usage
### Creating Tasks
1. Go to "Auto-Assign Task"
2. Enter task description
3. Select required skills
4. Set priority and due date
5. Enable auto-assign for AI matching

### Viewing Performance
- Check "Performance Leaderboard" for top performers
- Monitor AI metrics in the dedicated section
- Track task completion rates

## Tech Stack
- Frontend: Streamlit
- Backend: Python
- AI: Sklearn for task matching
- Data Storage: Pandas DataFrames

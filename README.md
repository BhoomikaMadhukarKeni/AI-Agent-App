
AI-Powered Task Assignment System

1. Solution Approach

This is a Streamlit-based web application that intelligently assigns tasks to employees using AI. The system automates task allocation by considering various factors such as required skills, experience level, and priority. It leverages Machine Learning (ML) and Natural Language Processing (NLP) techniques to optimize task distribution efficiently. The application provides real-time tracking of task statuses and evaluates AI performance in comparison to manual assignments.

Task Assignment Process:

----When a new task is created, the system captures:-----

Task description

Required skills

Priority level

Experience preference

Due date
-------------------------------------------------------------------------------------

---The system then processes this data to find the most suitable employee based on:---

Skill match percentage

Employee experience level

Current workload

Past performance

Task completion history

Tasks are categorized under different statuses:

Not Started

In Progress

Completed

Blocked
----------------------------------------------------------------------------------------------

--AI Performance Metrics tracked include:--

AI recommendation success rate

Prediction accuracy

Task completion efficiency

Comparison between AI and manual assignments

2. Implementation Details

Main Components:

Task Assignment System: app.py (Main application logic)

Task Matching Engine: task_matcher.py (Handles AI-based task assignments)

AI Models: task_prediction_model.py (Machine Learning models for predictions)

UI Components: components.py (Frontend UI elements for Streamlit)

Employee Management: employee_management.py (Handles employee data and preferences)

AI Models Used:

Machine Learning Model - A Random Forest classifier trained on historical task assignments.

Skill Similarity Model - Uses TF-IDF and cosine similarity to match tasks with employees when historical data is insufficient.
---------------------------------------------------------------------------------------------------------------

3. Execution Steps

To Run the Application:

Clone the repository:

git clone https://github.com/Ananyahc516/Team-Hackonauts
cd task-assignment

Install dependencies:

pip install -r requirements.txt

Run the Streamlit app:

streamlit run app.py

Open the application in your browser at (http://127.0.0.1:8501/)
------------------------------------------------------------------------------------------

4. Dependencies

Required Software & Libraries:

1.Clone the repository
2.cd <repo-folder-name>
3."streamlit run app.py" (else use -- "python -m streamlit run app.py")

---else import dependency from requirement.txt---- 

Python 3.x

Streamlit 

Pandas

Scikit-learn

NumPy

TF-IDF Vectorizer (from scikit-learn)

Cosine Similarity (from scikit-learn)
--------------------------------------------------------------------------------------------------

5. Expected Output

Task Auto-Assignment: The system automatically assigns tasks based on AI predictions.

Real-Time Tracking: Employees can track the progress of their assigned tasks.

Performance Metrics: AI vs. manual assignment success rates are displayed.

Employee Skill Management: Employees' skills and preferences are used for better assignments.

Leaderboards: Employees can view performance-based rankings.

Task Search by Skills: Users can search for tasks based on required skills.

AI Training: The system continuously improves by learning from past task assignments.

This application ensures efficient task allocation, reduces manual effort, and enhances productivity through AI-driven insights.
---------------------------------------------------------------------------------------------------------------------------------
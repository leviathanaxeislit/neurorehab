import os
import sqlite3
from pathlib import Path

def create_database():
    """
    Create and pre-seed a SQLite database for the NeuroWell application.
    """
    print("Creating NeuroWell SQLite Database")
    print("=================================")
    
    # Define database path
    db_path = Path("neurowell.db")
    
    # Check if database already exists
    if db_path.exists():
        print(f"Database already exists at {db_path}")
        choice = input("Overwrite existing database? (y/n) [Default: n]: ").strip().lower()
        if choice != 'y':
            print("Database creation canceled.")
            return
        else:
            print("Overwriting existing database...")
    
    # Create the database and connect to it
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create patients table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER,
        gender TEXT,
        speech_score REAL,
        emoji_score REAL,
        snake_score REAL,
        ball_score REAL,
        created_date TEXT,
        last_assessment TEXT
    )
    ''')
    
    # Create assessment_results table for detailed assessment data
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS assessment_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        assessment_type TEXT,
        score REAL,
        details TEXT,
        assessment_date TEXT,
        FOREIGN KEY (patient_id) REFERENCES patients (id)
    )
    ''')
    
    # Create rehabilitation_plans table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS rehabilitation_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        plan_name TEXT,
        description TEXT,
        created_date TEXT,
        status TEXT,
        FOREIGN KEY (patient_id) REFERENCES patients (id)
    )
    ''')
    
    # Create exercises table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS exercises (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plan_id INTEGER,
        exercise_name TEXT,
        description TEXT,
        frequency TEXT,
        duration TEXT,
        completed BOOLEAN DEFAULT 0,
        FOREIGN KEY (plan_id) REFERENCES rehabilitation_plans (id)
    )
    ''')
    
    # Pre-seed the database with sample data
    print("Adding sample patients...")
    
    # Sample patients data
    patients = [
        ('John Smith', 68, 'Male', 75.5, 82.0, 65.0, 70.0, '2023-01-15', '2023-04-20'),
        ('Mary Johnson', 72, 'Female', 68.0, 75.5, 60.0, 62.5, '2023-02-10', '2023-04-18'),
        ('Robert Davis', 65, 'Male', 80.0, 78.5, 72.0, 75.0, '2023-02-22', '2023-04-15'),
        ('Patricia Wilson', 70, 'Female', 72.5, 69.0, 65.5, 68.0, '2023-03-05', '2023-04-10'),
        ('James Brown', 75, 'Male', 65.0, 70.0, 62.0, 60.0, '2023-03-12', '2023-04-05'),
        ('Jennifer Garcia', 63, 'Female', 82.0, 85.0, 78.0, 80.0, '2023-03-18', '2023-04-01'),
        ('Michael Miller', 69, 'Male', 76.0, 72.5, 68.0, 70.5, '2023-03-25', '2023-03-28'),
        ('Linda Martinez', 71, 'Female', 70.0, 73.0, 67.0, 69.0, '2023-04-02', '2023-04-22'),
        ('William Anderson', 66, 'Male', 78.0, 80.0, 75.0, 77.5, '2023-04-08', '2023-04-16'),
        ('Elizabeth Thomas', 74, 'Female', 62.0, 65.5, 60.0, 58.5, '2023-04-15', '2023-04-19')
    ]
    
    cursor.executemany('''
    INSERT INTO patients 
    (name, age, gender, speech_score, emoji_score, snake_score, ball_score, created_date, last_assessment)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', patients)
    
    # Sample assessment results
    print("Adding sample assessment results...")
    
    assessment_results = []
    
    # Generate sample assessment results for each patient
    for patient_id in range(1, len(patients) + 1):
        assessment_types = ['Speech', 'Emoji', 'Snake', 'Ball']
        
        for assessment_type in assessment_types:
            # Create multiple assessments per type to show progress
            for i in range(3):
                # Gradually increasing scores to show improvement
                base_score = 60 + (i * 5) + (patient_id % 5) * 2
                score = min(100, base_score)
                
                # Date in format: 2023-04-01
                month = 2 + i
                day = 1 + patient_id % 28
                date = f'2023-{month:02d}-{day:02d}'
                
                details = f'Assessment details for {assessment_type} test on {date}'
                
                assessment_results.append((
                    patient_id,
                    assessment_type,
                    score,
                    details,
                    date
                ))
    
    cursor.executemany('''
    INSERT INTO assessment_results
    (patient_id, assessment_type, score, details, assessment_date)
    VALUES (?, ?, ?, ?, ?)
    ''', assessment_results)
    
    # Sample rehabilitation plans
    print("Adding sample rehabilitation plans...")
    
    rehab_plans = [
        (1, 'Motor Skills Improvement', 'Plan focused on improving fine motor skills', '2023-04-21', 'Active'),
        (2, 'Speech Recovery Program', 'Comprehensive speech therapy program', '2023-04-19', 'Active'),
        (3, 'Cognitive Enhancement', 'Program designed to enhance cognitive functions', '2023-04-16', 'Active'),
        (4, 'Hand-Eye Coordination', 'Exercises for better hand-eye coordination', '2023-04-11', 'Active'),
        (5, 'Balance Improvement', 'Program focused on improving balance', '2023-04-06', 'Active'),
        (6, 'Memory Enhancement', 'Memory-focused rehabilitation program', '2023-04-02', 'Completed'),
        (7, 'Daily Living Skills', 'Program to improve daily living activities', '2023-03-29', 'Active'),
        (8, 'Combined Therapy', 'Multi-faceted therapy approach', '2023-04-23', 'Active'),
        (9, 'Focused Recovery', 'Targeted recovery for specific impairments', '2023-04-17', 'Paused'),
        (10, 'General Rehabilitation', 'General rehabilitation program', '2023-04-20', 'Active')
    ]
    
    cursor.executemany('''
    INSERT INTO rehabilitation_plans
    (patient_id, plan_name, description, created_date, status)
    VALUES (?, ?, ?, ?, ?)
    ''', rehab_plans)
    
    # Sample exercises
    print("Adding sample exercises...")
    
    exercises = [
        # For plan 1 (Motor Skills Improvement)
        (1, 'Finger Tapping', 'Tap each finger to your thumb 10 times', 'Daily', '5 minutes', 0),
        (1, 'Wrist Flexion', 'Gently bend your wrist forward and backward 15 times', 'Daily', '5 minutes', 0),
        (1, 'Object Manipulation', 'Practice picking up and manipulating small objects', 'Daily', '10 minutes', 1),
        
        # For plan 2 (Speech Recovery Program)
        (2, 'Articulation Exercises', 'Practice specific sounds and words', 'Twice daily', '15 minutes', 1),
        (2, 'Reading Aloud', 'Read passages aloud with emphasis on clarity', 'Daily', '10 minutes', 0),
        
        # For plan 3 (Cognitive Enhancement)
        (3, 'Memory Games', 'Card matching and other memory exercises', '3 times per week', '20 minutes', 1),
        (3, 'Problem Solving', 'Complete puzzles of increasing difficulty', 'Daily', '15 minutes', 0),
        
        # For plan 4 (Hand-Eye Coordination)
        (4, 'Ball Catching', 'Practice catching balls of different sizes', '3 times per week', '10 minutes', 0),
        (4, 'Target Practice', 'Throw small objects at targets of varying distances', '3 times per week', '15 minutes', 1),
        
        # For plan 5 (Balance Improvement)
        (5, 'Standing on One Foot', 'Practice balancing on one foot', 'Daily', '5 minutes per foot', 0),
        (5, 'Walking Heel to Toe', 'Walk in a straight line placing heel to toe', 'Daily', '10 minutes', 0),
        
        # Additional exercises for various plans
        (6, 'Word Association', 'Practice associating related words', 'Daily', '10 minutes', 1),
        (7, 'Buttoning Exercise', 'Practice buttoning and unbuttoning clothes', 'Daily', '5 minutes', 0),
        (8, 'Coordination Drills', 'Perform exercises combining movements', '3 times per week', '20 minutes', 1),
        (9, 'Specific Movement Practice', 'Practice specific movements needed for recovery', 'Daily', '15 minutes', 0),
        (10, 'General Mobility', 'Various exercises to improve general mobility', 'Daily', '30 minutes', 1)
    ]
    
    cursor.executemany('''
    INSERT INTO exercises
    (plan_id, exercise_name, description, frequency, duration, completed)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', exercises)
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print(f"Database created successfully at {db_path.absolute()}")
    print("Ready to be used with the NeuroWell application.")

if __name__ == "__main__":
    create_database() 
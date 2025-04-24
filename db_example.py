"""
Example script showing how to use the SQLite database in the NeuroWell application.
This demonstrates how to replace the CSV-based data access with SQLite database access.
"""

from db_utils import db
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

def demo_patient_management():
    """Demonstrate basic patient management functions"""
    print("\n=== Patient Management ===")
    
    # Get all patients
    patients = db.get_all_patients()
    print(f"Found {len(patients)} patients in the database")
    
    # Display the first 3 patients
    print("\nSample patients:")
    print(patients[['name', 'age', 'gender']].head(3))
    
    # Search for a patient by name
    search_results = db.get_patient_by_name("John")
    print(f"\nSearch results for 'John': {len(search_results)} matches")
    if not search_results.empty:
        print(search_results[['name', 'age', 'gender']])
    
    # Add a new patient
    new_patient_id = db.add_patient("New Test Patient", 70, "Female")
    print(f"\nAdded new patient with ID: {new_patient_id}")
    
    # Generate CSV file for backward compatibility
    csv_path = db.export_patient_data_to_csv()
    print(f"\nExported patient data to CSV: {csv_path}")

def demo_assessment_scores():
    """Demonstrate assessment score functions"""
    print("\n=== Assessment Scores ===")
    
    # Get first patient for demo
    patients = db.get_all_patients()
    if patients.empty:
        print("No patients found")
        return
    
    patient_id = patients.iloc[0]['id']
    patient_name = patients.iloc[0]['name']
    print(f"Working with patient: {patient_name} (ID: {patient_id})")
    
    # Get current assessment scores
    patient = db.get_patient_by_id(patient_id)
    print("\nCurrent assessment scores:")
    for assessment_type in ['speech', 'emoji', 'snake', 'ball']:
        score = patient[f'{assessment_type}_score']
        print(f"  {assessment_type.capitalize()}: {score}")
    
    # Update an assessment score
    new_score = 85.5
    assessment_type = "Snake"
    print(f"\nUpdating {assessment_type} score to {new_score}")
    db.update_assessment_score(patient_id, assessment_type, new_score)
    
    # Get updated patient data
    updated_patient = db.get_patient_by_id(patient_id)
    print(f"Updated {assessment_type} score: {updated_patient['snake_score']}")
    
    # Get assessment history
    history = db.get_patient_assessment_history(patient_id, assessment_type)
    print(f"\nAssessment history for {assessment_type} ({len(history)} records):")
    if not history.empty:
        print(history[['assessment_date', 'score']].head())

def demo_rehabilitation_plans():
    """Demonstrate rehabilitation plan functions"""
    print("\n=== Rehabilitation Plans ===")
    
    # Get first patient for demo
    patients = db.get_all_patients()
    if patients.empty:
        print("No patients found")
        return
    
    patient_id = patients.iloc[0]['id']
    patient_name = patients.iloc[0]['name']
    print(f"Working with patient: {patient_name} (ID: {patient_id})")
    
    # Get existing rehabilitation plans
    plans = db.get_rehabilitation_plans(patient_id)
    print(f"\nExisting rehabilitation plans: {len(plans)}")
    if not plans.empty:
        print(plans[['plan_name', 'description', 'status']].head())
        
        # Get exercises for the first plan
        plan_id = plans.iloc[0]['id']
        plan_name = plans.iloc[0]['plan_name']
        exercises = db.get_exercises_for_plan(plan_id)
        print(f"\nExercises for plan '{plan_name}' ({len(exercises)}):")
        if not exercises.empty:
            print(exercises[['exercise_name', 'frequency', 'duration', 'completed']].head())
    
    # Create a new rehabilitation plan
    new_plan_name = "Test Rehabilitation Plan"
    new_plan_description = "A test plan created by the demo script"
    new_plan_id = db.create_rehabilitation_plan(patient_id, new_plan_name, new_plan_description)
    print(f"\nCreated new rehabilitation plan: {new_plan_name} (ID: {new_plan_id})")
    
    # Add exercises to the new plan
    exercise_name = "Test Exercise"
    exercise_description = "A simple exercise for testing"
    frequency = "Daily"
    duration = "10 minutes"
    exercise_id = db.add_exercise_to_plan(new_plan_id, exercise_name, exercise_description, frequency, duration)
    print(f"Added exercise: {exercise_name} (ID: {exercise_id})")
    
    # Toggle exercise completion
    new_status = db.toggle_exercise_completion(exercise_id)
    print(f"Toggled exercise completion status to: {'Completed' if new_status == 1 else 'Not Completed'}")

def demo_visualization():
    """Demonstrate how to visualize data from the database"""
    print("\n=== Data Visualization ===")
    
    # Get assessment data for all patients
    patients = db.get_all_patients()
    if patients.empty:
        print("No patients found")
        return
    
    # Create a chart directory if it doesn't exist
    chart_dir = Path("charts")
    chart_dir.mkdir(exist_ok=True)
    
    # Plot average scores by assessment type
    avg_scores = {
        'Speech': patients['speech_score'].mean(),
        'Emoji': patients['emoji_score'].mean(),
        'Snake': patients['snake_score'].mean(),
        'Ball': patients['ball_score'].mean()
    }
    
    plt.figure(figsize=(10, 6))
    plt.bar(avg_scores.keys(), avg_scores.values(), color=['blue', 'green', 'red', 'orange'])
    plt.title('Average Assessment Scores')
    plt.ylabel('Score')
    plt.ylim(0, 100)
    
    # Add value labels on top of bars
    for i, (assessment, score) in enumerate(avg_scores.items()):
        plt.text(i, score + 2, f'{score:.1f}', ha='center')
    
    # Save the chart
    chart_path = chart_dir / "average_scores.png"
    plt.savefig(chart_path)
    plt.close()
    print(f"Chart saved to: {chart_path}")
    
    # Get a patient with assessment history
    patient_id = patients.iloc[0]['id']
    patient_name = patients.iloc[0]['name']
    
    # Get assessment history for this patient
    speech_history = db.get_patient_assessment_history(patient_id, "Speech")
    
    if not speech_history.empty:
        # Plot progress over time
        plt.figure(figsize=(10, 6))
        
        # Convert assessment_date to datetime for proper plotting
        speech_history['assessment_date'] = pd.to_datetime(speech_history['assessment_date'])
        
        # Sort by date
        speech_history = speech_history.sort_values('assessment_date')
        
        plt.plot(speech_history['assessment_date'], speech_history['score'], 
                marker='o', linestyle='-', color='blue')
        
        plt.title(f'Speech Assessment Progress for {patient_name}')
        plt.ylabel('Score')
        plt.ylim(0, 100)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Save the chart
        progress_chart_path = chart_dir / f"patient_{patient_id}_speech_progress.png"
        plt.savefig(progress_chart_path)
        plt.close()
        print(f"Progress chart saved to: {progress_chart_path}")
    else:
        print(f"No assessment history found for patient {patient_name}")

def run_all_demos():
    """Run all demo functions"""
    print("NeuroWell SQLite Database Demo")
    print("==============================")
    
    demo_patient_management()
    demo_assessment_scores()
    demo_rehabilitation_plans()
    demo_visualization()
    
    print("\nDemo completed successfully!")

if __name__ == "__main__":
    run_all_demos() 
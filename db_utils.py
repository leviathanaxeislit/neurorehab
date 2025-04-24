import sqlite3
import os
import pandas as pd
from pathlib import Path

class DatabaseManager:
    """Class to manage all database operations for the NeuroWell application"""
    
    def __init__(self, db_path="neurowell.db"):
        """Initialize the database manager with the database path"""
        self.db_path = Path(db_path)
        self.ensure_db_exists()
        self.ensure_tables_exist()
    
    def ensure_db_exists(self):
        """Ensure the database exists, create it if it doesn't"""
        if not self.db_path.exists():
            # Try to create the database using the create_database module
            try:
                from create_database import create_database
                create_database()
            except (ImportError, Exception) as e:
                print(f"Error creating database: {e}")
                self._create_minimal_db()
    
    def ensure_tables_exist(self):
        """Check if all required tables exist and create them if they don't"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get list of existing tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [table[0] for table in cursor.fetchall()]
        
        print(f"Existing tables in database: {tables}")
        
        # Check if patients table exists
        if 'patients' not in tables:
            print("Creating missing patients table")
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
                physio_score REAL
            )
            ''')
        else:
            # Check if physio_score column exists
            cursor.execute("PRAGMA table_info(patients)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'physio_score' not in columns:
                print("Adding missing physio_score column to patients table")
                try:
                    cursor.execute("ALTER TABLE patients ADD COLUMN physio_score REAL DEFAULT 0")
                    conn.commit()
                    print("Successfully added physio_score column")
                except Exception as e:
                    print(f"Error adding physio_score column: {e}")
        
        # Check if assessment_results table exists
        if 'assessment_results' not in tables:
            print("Creating missing assessment_results table")
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
        
        # Check if rehabilitation_plans table exists
        if 'rehabilitation_plans' not in tables:
            print("Creating missing rehabilitation_plans table")
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
        
        # Check if exercises table exists
        if 'exercises' not in tables:
            print("Creating missing exercises table")
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS exercises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id INTEGER,
                exercise_name TEXT,
                description TEXT,
                frequency TEXT,
                duration TEXT,
                completed INTEGER,
                FOREIGN KEY (plan_id) REFERENCES rehabilitation_plans (id)
            )
            ''')
        
        conn.commit()
        conn.close()
    
    def _create_minimal_db(self):
        """Create a minimal database with just the essential tables"""
        conn = sqlite3.connect(self.db_path)
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
            physio_score REAL
        )
        ''')
        
        # Create assessment_results table
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
        
        # Add a sample patient
        cursor.execute('''
        INSERT INTO patients 
        (name, age, gender, speech_score, emoji_score, snake_score, ball_score, physio_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('Sample Patient', 65, 'Male', 0, 0, 0, 0, 0))
        
        conn.commit()
        conn.close()
    
    def get_connection(self):
        """Get a database connection"""
        return sqlite3.connect(self.db_path)
    
    def get_all_patients(self):
        """Get all patients from the database as a pandas DataFrame"""
        conn = self.get_connection()
        query = "SELECT * FROM patients"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def get_patient_by_id(self, patient_id):
        """Get a specific patient by ID"""
        conn = self.get_connection()
        query = "SELECT * FROM patients WHERE id = ?"
        df = pd.read_sql_query(query, conn, params=(patient_id,))
        conn.close()
        return df.iloc[0] if not df.empty else None
    
    def get_patient_by_name(self, name):
        """Get a patient by name (approximate match)"""
        conn = self.get_connection()
        query = "SELECT * FROM patients WHERE name LIKE ?"
        df = pd.read_sql_query(query, conn, params=(f"%{name}%",))
        conn.close()
        return df
    
    def add_patient(self, name, age, gender):
        """Add a new patient"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO patients 
        (name, age, gender, speech_score, emoji_score, snake_score, ball_score)
        VALUES (?, ?, ?, 0, 0, 0, 0)
        """, (name, age, gender))
        patient_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return patient_id
    
    def update_assessment_score(self, patient_id, assessment_type, score):
        """Update a patient's assessment score"""
        try:
            print(f"Inside db update_assessment_score - Patient ID: {patient_id}, Type: {assessment_type}, Score: {score}")
            score_column = f"{assessment_type.lower()}_score"
            valid_columns = ["speech_score", "emoji_score", "snake_score", "ball_score", "physio_score"]
            
            if score_column not in valid_columns:
                print(f"ERROR: Invalid assessment type: {assessment_type}")
                raise ValueError(f"Invalid assessment type: {assessment_type}")
            
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Check if patient exists
            cursor.execute("SELECT id FROM patients WHERE id = ?", (patient_id,))
            patient_exists = cursor.fetchone()
            if not patient_exists:
                print(f"ERROR: Patient with ID {patient_id} not found in database")
                conn.close()
                return False
                
            # Update the main score in patients table
            print(f"Updating {score_column} column with value {score} for patient ID {patient_id}")
            query = f"UPDATE patients SET {score_column} = ? WHERE id = ?"
            cursor.execute(query, (score, patient_id))
            
            # Verify the update was successful
            rows_affected = cursor.rowcount
            print(f"Rows affected by update: {rows_affected}")
            
            if rows_affected == 0:
                print(f"WARNING: No rows were updated in the patients table")
            
            # Also record the assessment details
            print(f"Recording assessment details in assessment_results table")
            cursor.execute("""
            INSERT INTO assessment_results 
            (patient_id, assessment_type, score, details, assessment_date)
            VALUES (?, ?, ?, ?, datetime('now'))
            """, (patient_id, assessment_type, score, f"Assessment on {assessment_type}"))
            
            # Commit the transaction
            conn.commit()
            print(f"Database changes committed successfully")
            
            # Verify that the score was updated
            verify_query = f"SELECT {score_column} FROM patients WHERE id = ?"
            cursor.execute(verify_query, (patient_id,))
            updated_score = cursor.fetchone()
            print(f"Verification - Updated score: {updated_score}")
            
            conn.close()
            return True
        except Exception as e:
            print(f"ERROR in update_assessment_score: {str(e)}")
            import traceback
            traceback.print_exc()
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            return False
    
    def update_detailed_assessment(self, patient_id, assessment_type, score, details, category=None):
        """Add a detailed assessment record for a patient
        
        Args:
            patient_id: The ID of the patient
            assessment_type: The type of assessment (e.g., 'Physio', 'Hand')
            score: The numerical score for this specific assessment
            details: Additional details about this assessment
            category: Optional subcategory for the assessment
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Add category to details if provided
            full_details = details
            if category:
                full_details = f"[{category}] {details}"
            
            # Record the assessment details
            cursor.execute("""
            INSERT INTO assessment_results 
            (patient_id, assessment_type, score, details, assessment_date)
            VALUES (?, ?, ?, ?, datetime('now'))
            """, (patient_id, assessment_type, score, full_details))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error adding detailed assessment: {str(e)}")
            return False
    
    def get_patient_assessment_history(self, patient_id, assessment_type=None):
        """Get assessment history for a patient"""
        conn = self.get_connection()
        
        if assessment_type:
            query = """
            SELECT * FROM assessment_results 
            WHERE patient_id = ? AND assessment_type = ?
            ORDER BY assessment_date DESC
            """
            df = pd.read_sql_query(query, conn, params=(patient_id, assessment_type))
        else:
            query = """
            SELECT * FROM assessment_results 
            WHERE patient_id = ?
            ORDER BY assessment_date DESC
            """
            df = pd.read_sql_query(query, conn, params=(patient_id,))
        
        conn.close()
        return df
    
    def get_rehabilitation_plans(self, patient_id):
        """Get rehabilitation plans for a patient"""
        conn = self.get_connection()
        query = """
        SELECT * FROM rehabilitation_plans 
        WHERE patient_id = ?
        ORDER BY created_date DESC
        """
        df = pd.read_sql_query(query, conn, params=(patient_id,))
        conn.close()
        return df
    
    def get_exercises_for_plan(self, plan_id):
        """Get exercises for a specific rehabilitation plan"""
        conn = self.get_connection()
        query = """
        SELECT * FROM exercises 
        WHERE plan_id = ?
        """
        df = pd.read_sql_query(query, conn, params=(plan_id,))
        conn.close()
        return df
    
    def create_rehabilitation_plan(self, patient_id, plan_name, description):
        """Create a new rehabilitation plan for a patient"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO rehabilitation_plans 
        (patient_id, plan_name, description, created_date, status)
        VALUES (?, ?, ?, datetime('now'), 'Active')
        """, (patient_id, plan_name, description))
        plan_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return plan_id
    
    def add_exercise_to_plan(self, plan_id, exercise_name, description, frequency, duration):
        """Add an exercise to a rehabilitation plan"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO exercises 
        (plan_id, exercise_name, description, frequency, duration, completed)
        VALUES (?, ?, ?, ?, ?, 0)
        """, (plan_id, exercise_name, description, frequency, duration))
        exercise_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return exercise_id
    
    def toggle_exercise_completion(self, exercise_id):
        """Toggle an exercise's completion status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # First get current status
        cursor.execute("SELECT completed FROM exercises WHERE id = ?", (exercise_id,))
        result = cursor.fetchone()
        
        if result:
            current_status = result[0]
            new_status = 1 if current_status == 0 else 0
            
            cursor.execute("""
            UPDATE exercises 
            SET completed = ?
            WHERE id = ?
            """, (new_status, exercise_id))
            
            conn.commit()
            conn.close()
            return new_status
        else:
            conn.close()
            return None
    
    def export_patient_data_to_csv(self, output_path="patients_data.csv"):
        """Export all patient data to a CSV file for compatibility with legacy code"""
        df = self.get_all_patients()
        # Rename columns to match the expected format in the legacy code
        column_mapping = {
            'name': 'Name', 
            'age': 'Age', 
            'gender': 'Gender', 
            'speech_score': 'Speech Score', 
            'emoji_score': 'Emoji Score', 
            'snake_score': 'Snake Score', 
            'ball_score': 'Ball Score'
        }
        df = df.rename(columns=column_mapping)
        # Select only the columns needed for compatibility
        columns_to_export = list(column_mapping.values())
        df[columns_to_export].to_csv(output_path, index=False)
        return output_path
    
    def delete_patient(self, patient_id):
        """Delete a patient from the database by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Delete related assessment results first
            cursor.execute("DELETE FROM assessment_results WHERE patient_id = ?", (patient_id,))
            
            # Delete related rehabilitation plans and exercises
            cursor.execute("SELECT id FROM rehabilitation_plans WHERE patient_id = ?", (patient_id,))
            plan_ids = [row[0] for row in cursor.fetchall()]
            
            for plan_id in plan_ids:
                cursor.execute("DELETE FROM exercises WHERE plan_id = ?", (plan_id,))
            
            cursor.execute("DELETE FROM rehabilitation_plans WHERE patient_id = ?", (patient_id,))
            
            # Now delete the patient
            cursor.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting patient: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

# Create a singleton instance for easy import throughout the application
db = DatabaseManager()

# Example usage:
if __name__ == "__main__":
    # Get all patients
    patients = db.get_all_patients()
    print(f"Found {len(patients)} patients")
    
    # Example of getting a patient and their assessment history
    if not patients.empty:
        patient_id = patients.iloc[0]['id']
        patient = db.get_patient_by_id(patient_id)
        print(f"Patient: {patient['name']}")
        
        history = db.get_patient_assessment_history(patient_id)
        print(f"Assessment history: {len(history)} records") 
import sqlite3
from pathlib import Path

def update_database():
    """Update the database schema to add missing columns"""
    db_path = Path("neurowell.db")
    
    if not db_path.exists():
        print(f"Database file {db_path} does not exist!")
        return
    
    print(f"Updating database {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if physio_score column exists
        cursor.execute("PRAGMA table_info(patients)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'physio_score' not in columns:
            print("Adding missing physio_score column to patients table...")
            try:
                cursor.execute("ALTER TABLE patients ADD COLUMN physio_score REAL DEFAULT 0")
                conn.commit()
                print("Successfully added physio_score column!")
            except Exception as e:
                print(f"Error adding physio_score column: {e}")
        else:
            print("physio_score column already exists in patients table.")
        
        # Verify the update
        cursor.execute("PRAGMA table_info(patients)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"Current columns in patients table: {columns}")
        
        # Add any other missing tables
        # Check if assessment_results table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='assessment_results'")
        if not cursor.fetchone():
            print("Creating assessment_results table...")
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
            print("Successfully created assessment_results table!")
        
        # Commit and close
        conn.commit()
        conn.close()
        print("Database update completed successfully!")
        
    except Exception as e:
        print(f"Error updating database: {e}")

if __name__ == "__main__":
    update_database() 
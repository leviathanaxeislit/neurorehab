import sqlite3
import os
from pathlib import Path

def check_database():
    """Check the database structure and contents"""
    db_path = Path("neurowell.db")
    
    if not db_path.exists():
        print(f"Database file {db_path} does not exist!")
        return
    
    print(f"Database file {db_path} exists (size: {db_path.stat().st_size} bytes)")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check integrity
        cursor.execute("PRAGMA integrity_check")
        integrity = cursor.fetchone()[0]
        print(f"Integrity check: {integrity}")
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]
        print(f"Tables in database: {tables}")
        
        # Check each table's schema
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            print(f"\nSchema for table '{table}':")
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
        
        # Check number of records in each table
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"Records in '{table}': {count}")
        
        # Check patients table contents if it exists and has records
        if 'patients' in tables:
            cursor.execute("SELECT * FROM patients LIMIT 5")
            rows = cursor.fetchall()
            
            if rows:
                # Get column names
                cursor.execute("PRAGMA table_info(patients)")
                columns = [col[1] for col in cursor.fetchall()]
                
                print("\nSample patient records:")
                for row in rows:
                    print("\nPatient:")
                    for i, col in enumerate(columns):
                        print(f"  {col}: {row[i]}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error examining database: {e}")

if __name__ == "__main__":
    check_database() 
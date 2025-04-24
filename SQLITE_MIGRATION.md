# Migrating from CSV to SQLite Database

This document explains how to transition the NeuroWell application from using CSV files to a SQLite database for data storage.

## Overview

The application has been enhanced to use a SQLite database instead of CSV files. This provides several benefits:

- **Improved data integrity**: Prevents data corruption and enforces relationships between data
- **Better performance**: Faster queries and updates, especially with larger datasets
- **Richer data model**: Support for more complex data structures and relationships
- **Transaction support**: Changes can be grouped and rolled back if errors occur
- **Concurrent access**: Multiple parts of the application can access the data simultaneously

## Files Added

1. **create_database.py**: Creates and seeds the SQLite database with sample data
2. **db_utils.py**: Provides a database access layer with helper functions
3. **db_example.py**: Demonstrates how to use the database in your code
4. **neurowell.db**: The SQLite database file (created by running create_database.py)

## Database Schema

The database includes the following tables:

- **patients**: Patient profiles and current assessment scores
- **assessment_results**: Detailed history of assessments for tracking progress
- **rehabilitation_plans**: Rehabilitation plans for patients
- **exercises**: Specific exercises assigned as part of rehabilitation plans

## How to Use the Database

### 1. Access the Database

Import the database instance from `db_utils`:

```python
from db_utils import db
```

### 2. Get Patient Data

Replace CSV reading code like:

```python
import pandas as pd
patients_df = pd.read_csv("patients_data.csv")
```

With database access:

```python
patients_df = db.get_all_patients()
```

### 3. Update Assessment Scores

Replace CSV writing code like:

```python
patients_df.loc[patient_index, 'Snake Score'] = new_score
patients_df.to_csv("patients_data.csv", index=False)
```

With database updates:

```python
db.update_assessment_score(patient_id, "Snake", new_score)
```

### 4. Backward Compatibility

To maintain compatibility with code that still expects CSV files:

```python
# Export current database data to CSV
csv_path = db.export_patient_data_to_csv()
```

## Implementation Guide

### Step 1: Replace Data Loading

Find all instances where CSV files are loaded:

```python
# Old CSV code
df = pd.read_csv("patients_data.csv")

# New SQLite code
from db_utils import db
df = db.get_all_patients()
```

### Step 2: Replace Data Saving

Find all places where data is saved to CSV:

```python
# Old CSV code
df.to_csv("patients_data.csv", index=False)

# New SQLite code - update specific fields
db.update_assessment_score(patient_id, assessment_type, score)

# Or add a new patient
db.add_patient(name, age, gender)
```

### Step 3: Use New Features

Take advantage of new database capabilities:

```python
# Get patient assessment history
history_df = db.get_patient_assessment_history(patient_id)

# Create rehabilitation plan
plan_id = db.create_rehabilitation_plan(patient_id, plan_name, description)

# Add exercises to a plan
db.add_exercise_to_plan(plan_id, exercise_name, description, frequency, duration)
```

## Example Usage

See `db_example.py` for complete examples of:

- Retrieving and displaying patient data
- Updating assessment scores
- Managing rehabilitation plans and exercises
- Visualizing assessment data

To run the example:

```
python db_example.py
```

## Building the Executable

The build script has been updated to include the SQLite database in the executable. Use the new batch file:

```
build_neurowell_with_db.bat
```

This will:
1. Create and seed the database if it doesn't exist
2. Build the executable with the database included

## Troubleshooting

### Database Not Found

If you see errors about the database not being found:

1. Run `python create_database.py` to create it
2. Make sure `neurowell.db` is in the same directory as your script

### Migration Issues

If you encounter issues while migrating:

1. The `export_patient_data_to_csv()` function can be used as a fallback
2. Both systems can run in parallel during transition
3. Test thoroughly before deploying changes 
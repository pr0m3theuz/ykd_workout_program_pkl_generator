# CSV to PKL Workout Program Converter

![Python](https://img.shields.io/badge/python-3.7+-blue.svg?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-GPLv3-green?style=for-the-badge)

> Convert workout program templates from CSV format to PKL (Pickle Configuration Language) for the YKD workout tracking ecosystem.

## Overview

This utility script converts structured workout program data from CSV spreadsheets into PKL format, which is used by YKD's desktop program editor and mobile app. It automates the process of creating properly formatted workout programs with mesocycles, microcycles, workouts, exercises, and set schemes.

### What It Does

- **Parses CSV** - Reads workout program templates from CSV files
- **Normalizes Exercise Names** - Maps variant exercise names to standardized database entries (1,100+ exercise mappings)
- **Structures Data** - Organizes programs into hierarchical mesocycle/microcycle/workout structure
- **Generates PKL** - Outputs valid PKL configuration files ready for import

### Use Cases

- Creating new workout programs from spreadsheets
- Importing third-party training programs into YKD
- Batch converting multiple program templates
- Standardizing exercise nomenclature across programs

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [CSV Format](#csv-format)
- [PKL Output Structure](#pkl-output-structure)
- [Exercise Mapping](#exercise-mapping)
- [Set Types](#set-types)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Installation

### Prerequisites

- Python 3.7 or higher
- No external dependencies (uses only standard library)

### Setup

1. **Download the script:**
   ```bash
   wget https://raw.githubusercontent.com/pr0m3theuz/workout-app/main/gemini-csv_to_pkl_v3.py
   # or
   curl -O https://raw.githubusercontent.com/pr0m3theuz/workout-app/main/gemini-csv_to_pkl_v3.py
   ```

2. **Make it executable (optional):**
   ```bash
   chmod +x gemini-csv_to_pkl_v3.py
   ```

## Usage

### Basic Usage

```bash
python gemini-csv_to_pkl_v3.py
```

The script will:
1. Look for a CSV file in the current directory
2. Parse the workout program structure
3. Generate a corresponding `.pkl` file

### Command-Line Arguments

**Modify the script to specify input/output files:**

```python
# At the bottom of the script, modify:
csv_file_path = "your_program.csv"      # Input CSV file
output_filename = "your_program.pkl"     # Output PKL file
```

### Batch Processing

Process multiple programs:

```bash
# Create a wrapper script
for csv_file in programs/*.csv; do
    python gemini-csv_to_pkl_v3.py "$csv_file"
done
```

## CSV Format

The CSV must follow a specific structure representing the program hierarchy:

### Required Columns

Your CSV should include columns that represent:

1. **Program metadata** (name, author, description, level, equipment, etc.)
2. **Mesocycle information** (training phases/blocks)
3. **Microcycle information** (weekly training cycles)
4. **Workout details** (day, name, notes)
5. **Exercise data** (name, sets, reps, RIR, RPE, weight, etc.)

### Example CSV Structure

```csv
Program Name,Author,Description,Level,Equipment,Days Per Week,Length
MAX Muscle Plan,Brad Schoenfeld,Hypertrophy program,Intermediate,Full Gym,6,6 Months

Mesocycle,Description,Order
Break-In,Adaptation phase,1
Hypertrophy Block 1,Volume accumulation,2

Microcycle,Description,Order
Week 1,Break-in week 1,1

Workout,Day,Notes
Upper A,1,Focus on compound movements

Exercise,Sets,Reps,RIR,Weight (lbs),Set Type,Notes
Barbell Bench Press,3,10,2,185,NORMAL,Controlled tempo
Dumbbell Row,3,12,1,70,NORMAL,
Cable Triceps Extension,2,15,0,40,DROP_SET,Drop 20% after failure
```

### Important Notes

- Exercise names will be automatically mapped to the YKD database using the built-in exercise replacement map
- Unmapped exercises will be flagged during conversion
- Set types must match the defined set type constants (see [Set Types](#set-types))

## PKL Output Structure

The generated PKL file follows this hierarchical structure:

```pkl
program = new Program {
  name = "MAX Muscle Plan"
  arthur = "Brad Schoenfeld"
  description = """
    A periodized hypertrophy program designed to maximize
    muscle growth through strategic volume and intensity manipulation.
  """
  level = "Intermediate"
  programEquipment = "Full Gym"
  daysPerWeek = "6"
  programLength = "6 Months"
  
  mesocycles = new Listing<Mesocycle> {
    new Mesocycle {
      name = "Break-In"
      description = "Adaptation phase"
      order = 1
      
      microcycles = new Listing<Microcycle> {
        new Microcycle {
          name = "Week 1"
          order = 1
          
          advancedWorkouts = new Listing<AdvancedWorkout> {
            new AdvancedWorkout {
              name = "Upper A"
              day = 1
              
              advancedExercisesSets = new Listing<AdvancedExerciseSets> {
                new AdvancedExerciseSets {
                  exerciseName = "Barbell Bench Press"
                  advancedSetScheme = new AdvancedSetScheme {
                    sets = 3
                    repetitions = new Listing<Int> { 10 10 10 }
                    targetRepetitionsInReserve = new Listing<Int> { 2 2 2 }
                    setType = 1
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

## Exercise Mapping

The script includes **1,100+ exercise name mappings** to ensure compatibility with the YKD exercise database.

### How Mapping Works

```python
# Input CSV might have:
"Flat Dumbbell Press"

# Automatically mapped to:
"Dumbbell Bench Press"
```

### Common Mappings

| CSV Name | YKD Database Name |
|----------|-------------------|
| Flat Dumbbell Press | Dumbbell Bench Press |
| Lat Pulldown | Cable Pulldown |
| Leg Press (Glute Biased) | Sled 45° Leg Press |
| Romanian Deadlift | Barbell Straight-back Straight-leg Deadlift |
| Single Arm Cable Y Raise | Cable Y Raise |

### Adding Custom Mappings

To add new exercise mappings, edit the `exercise_replacement_map` dictionary:

```python
exercise_replacement_map = {
    "Your Custom Exercise Name": "Standard YKD Exercise Name",
    # ... existing mappings
}
```

## Set Types

The script supports the following set types (matching YKD's SetType enum):

| Type | ID | Description |
|------|----|----|
| NORMAL | 1 | Standard working set |
| WARM_UP | 2 | Warm-up set |
| DROP_SET | 3 | Drop set (reduce weight and continue) |
| MYO_REP | 4 | Myo-rep set |
| MYO_REP_MATCH | 5 | Myo-rep match set |
| GIANT_SET | 6 | Giant set (4+ exercises) |
| AMRAP | 7 | As many reps as possible |
| FAILURE | 8 | To failure |
| CLUSTER | 9 | Cluster set (rest-pause) |
| LEFT | 10 | Left side only |
| RIGHT | 11 | Right side only |
| PARTIAL | 12 | Partial range of motion |
| NEGATIVE | 13 | Eccentric/negative emphasis |
| BACK_OFF | 14 | Back-off set (reduced intensity) |

### Usage in CSV

```csv
Exercise,Sets,Set Type
Bench Press,3,NORMAL
Triceps Extension,2,DROP_SET
Leg Press,1,FAILURE
```

## Examples

### Example 1: Simple Strength Program

**Input CSV:** `strength_program.csv`
```csv
Program Name,Author,Level
5x5 Strength,Bill Starr,Beginner

Workout,Day
Full Body A,1

Exercise,Sets,Reps,Set Type
Barbell Squat,5,5,NORMAL
Barbell Bench Press,5,5,NORMAL
Barbell Row,5,5,NORMAL
```

**Run Conversion:**
```bash
python gemini-csv_to_pkl_v3.py
```

**Output:** `strength_program.pkl`

### Example 2: Hypertrophy Program with RIR

**Input CSV:** `hypertrophy_program.csv`
```csv
Exercise,Sets,Reps,RIR,Weight (lbs)
Incline Dumbbell Press,4,10,2,80
Cable Fly,3,15,1,35
```

**Output includes RIR targets:**
```pkl
targetRepetitionsInReserve = new Listing<Int> { 2 2 2 2 }
```

## Troubleshooting

### Common Issues

**1. Exercise Not Found**
```
Warning: Exercise "XYZ" not found in mapping
```
**Solution:** Add the exercise to `exercise_replacement_map` or use a mapped exercise name.

**2. Invalid Set Type**
```
Error: Unknown set type "SUPERSET"
```
**Solution:** Use one of the defined set types from the SET_TYPE_MAP.

**3. CSV Parsing Error**
```
Error: Could not parse CSV structure
```
**Solution:** Verify your CSV follows the expected column structure and hierarchy.

**4. Empty Output**
```
Generated PKL file is empty
```
**Solution:** Check that your CSV has data in the expected format and that required fields are populated.

### Debug Mode

Add debug output to see parsing progress:

```python
# Add at the start of parse_advanced_template_csv():
print(f"Reading CSV with {len(rows)} rows")
for i, row in enumerate(rows):
    print(f"Row {i}: {row}")
```

### Validation

After conversion, validate the PKL file:

1. Check file size (should not be 0 bytes)
2. Open in text editor and verify structure
3. Import into YKD desktop app to confirm compatibility

## Advanced Usage

### Custom Schemes

The script supports pre-defined progression schemes. To use them:

```python
# Define schemes in schemes_map
schemes_map = {
    "linear_progression": AdvancedSetScheme(
        progressionSchemeID=1,
        weightIncrementPounds=5.0
    )
}

# Reference in CSV
progressionScheme = "linear_progression"
```

### Multi-line Descriptions

For longer descriptions in PKL output:

```csv
Description
"This is a multi-line description
that spans multiple lines
and will be properly formatted in the PKL output"
```

### Conditional Set Schemes

Different reps per set:

```csv
Exercise,Sets,Reps (Set 1),Reps (Set 2),Reps (Set 3)
Pyramid Bench Press,3,10,8,6
```

Generates:
```pkl
repetitions = new Listing<Int> { 10 8 6 }
```

## File Structure

```
gemini-csv_to_pkl_v3.py
├── SET_TYPE_MAP          # Set type constants
├── PKLBase               # Base class for PKL serialization
├── Listing               # Custom list for typed collections
├── Program               # Program container
├── Mesocycle             # Training phase/block
├── Microcycle            # Weekly cycle
├── AdvancedWorkout       # Individual workout
├── AdvancedExerciseSets  # Exercise within workout
├── AdvancedSetScheme     # Set configuration and progression
├── exercise_replacement_map  # 1,100+ exercise mappings
└── parse_advanced_template_csv()  # Main parsing logic
```

## Integration with YKD Ecosystem

This script is part of the YKD workout tracking ecosystem:

1. **Create programs** in spreadsheet software (Excel, Google Sheets)
2. **Export to CSV** format
3. **Run this converter** to generate PKL files
4. **Import into YKD desktop app** for program editing
5. **Sync to mobile app** for workout execution

## Contributing

Contributions welcome! Areas for improvement:

- **More exercise mappings** - Add mappings for additional exercise variations
- **CSV template generator** - Create blank CSV templates for different program types
- **Validation** - Add pre-flight validation of CSV structure
- **CLI arguments** - Accept input/output files as command-line arguments
- **Batch mode** - Process entire directories of CSV files
- **Error reporting** - More detailed error messages with line numbers

### How to Contribute

1. Fork the repository
2. Add your improvements
3. Test with sample CSV files
4. Submit a pull request

## License

This project is licensed under the **GNU General Public License v3.0**.

See the main [YKD repository](https://github.com/pr0m3theuz/workout-app) for full license details.

---

**Related Projects:**
- [YKD Mobile App](https://github.com/pr0m3theuz/workout-app) - Android workout tracking application
- [YKD Server](https://github.com/pr0m3theuz/workout-app-server) - Sync infrastructure

*Part of the YKD ecosystem - Local-first workout tracking with structured programming.*

import csv
import datetime
import re
import os
from io import StringIO


# --- PKL Class Definitions ---
# These classes model the structure of the output PKL file.

class PKLBase:
    """Base class for handling conversion of Python objects to PKL string format."""

    def to_pkl_string(self, indent_level=0, is_listing_item=False):
        raise NotImplementedError

    def _format_value(self, value, indent_level, is_listing_item=False):
        indent = "  " * indent_level
        if isinstance(value, PKLBase):
            return value.to_pkl_string(indent_level, is_listing_item)
        elif isinstance(value, str):
            if '\n' in value:
                content_indent = "  " * (indent_level + 1)
                return f'"""\n' + "\n".join(
                    [f"{content_indent}{line.lstrip()}" for line in value.strip().split('\n')]) + f'\n{indent}"""'
            return f'"{value}"'
        elif isinstance(value, bool):
            return str(value).lower()
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, list) or (hasattr(value, '__class__') and value.__class__.__name__ == 'Listing'):
            if not value:
                item_type_str = f"<{value.item_type}>" if hasattr(value, 'item_type') and value.item_type else ""
                return f"new Listing{item_type_str} {{}}"

            item_type_str = f"<{value.item_type}>" if hasattr(value, 'item_type') and value.item_type else ""
            items_strs = [self._format_value(item, indent_level + 1, True) for item in value]

            if not items_strs:
                return f"new Listing{item_type_str} {{}}"

            joined_items = f"\n{indent}    ".join(items_strs)
            return f"new Listing{item_type_str} {{\n{indent}    {joined_items}\n{indent}  }}"
        elif value is None:
            return "null"
        else:
            return str(value)

    def _format_attr(self, attr_name, attr_value, indent_level):
        indent = "  " * (indent_level + 1)
        # Skip None attributes and default empty values unless explicitly handled
        if attr_value is None or (isinstance(attr_value, str) and not attr_value) or (
                isinstance(attr_value, list) and not attr_value):
            return ""

        formatted_value = self._format_value(attr_value, indent_level + 1)
        return f"{indent}{attr_name} = {formatted_value}"


class Listing(list):
    """A custom list class to represent PKL Listings with a specific item type."""

    def __init__(self, item_type_name=None, *args):
        super().__init__(*args)
        self.item_type = item_type_name


class Program(PKLBase):
    def __init__(self, name="", arthur="", description="", shortDescription="", programLength="", level="",
                 programEquipment="",
                 daysPerWeek="", mesocycles=None):
        self.name = name
        self.arthur = arthur
        self.description = description
        self.shortDescription = shortDescription
        self.programLength = programLength
        self.level = level
        self.programEquipment = programEquipment
        self.daysPerWeek = daysPerWeek
        self.mesocycles = mesocycles if mesocycles is not None else Listing("Mesocycle")

    def to_pkl_string(self, indent_level=0, is_listing_item=False):
        obj_name = "program"
        attrs = [self._format_attr(k, v, indent_level) for k, v in self.__dict__.items()]
        valid_attrs = [attr for attr in attrs if attr]
        return f"{obj_name} = new Program {{\n" + "\n".join(valid_attrs) + f"\n}}"


class Mesocycle(PKLBase):
    def __init__(self, name="", description="", order=0, microcycles=None):
        self.name = name
        self.description = description
        self.order = order
        self.microcycles = microcycles if microcycles is not None else Listing("Microcycle")

    def to_pkl_string(self, indent_level=0, is_listing_item=False):
        attrs = [self._format_attr(k, v, indent_level) for k, v in self.__dict__.items()]
        return f"new Mesocycle {{\n" + "\n".join(filter(None, attrs)) + f"\n{'  ' * indent_level}  }}"


class Microcycle(PKLBase):
    def __init__(self, name="", description="", order=0, advancedWorkouts=None):
        self.name = name
        self.description = description
        self.order = order
        self.advancedWorkouts = advancedWorkouts if advancedWorkouts is not None else Listing("AdvancedWorkout")

    def to_pkl_string(self, indent_level=0, is_listing_item=False):
        attrs = [self._format_attr(k, v, indent_level) for k, v in self.__dict__.items()]
        return f"new Microcycle {{\n" + "\n".join(filter(None, attrs)) + f"\n{'  ' * indent_level}  }}"


class AdvancedWorkout(PKLBase):
    def __init__(self, name="", day=0, notes="", advancedExercisesSets=None):
        self.name = name
        self.day = day
        self.notes = notes
        self.advancedExercisesSets = advancedExercisesSets if advancedExercisesSets is not None else Listing(
            "AdvancedExerciseSets")

    def to_pkl_string(self, indent_level=0, is_listing_item=False):
        attrs = [self._format_attr(k, v, indent_level) for k, v in self.__dict__.items()]
        return f"new AdvancedWorkout {{\n" + "\n".join(filter(None, attrs)) + f"\n{'  ' * indent_level}  }}"


class AdvancedSetScheme(PKLBase):
    def __init__(self, sets=0, setType=1, setTypes=None, repetitions=None,
                 targetWeightPounds=None, targetWeightKilograms=None,
                 weightIncrementPounds=None, weightIncrementKilograms=None,
                 targetRepetitionsInReserve=None, targetRatePerceivedEffort=None,
                 percentage1RM=None, progressionSchemeID=None,
                 minRepetitions=None, maxRepetitions=None,
                 minRepetitionsList=None, maxRepetitionsList=None, notes=None):
        self.sets = sets
        self.setType = setType
        self.setTypes = setTypes if isinstance(setTypes, Listing) else Listing("Int", setTypes or [])
        self.repetitions = repetitions if isinstance(repetitions, Listing) else Listing("Int", repetitions or [])

        self.targetWeightPounds = targetWeightPounds if isinstance(targetWeightPounds, Listing) else Listing("Float",
                                                                                                             targetWeightPounds or [])
        self.targetWeightKilograms = targetWeightKilograms if isinstance(targetWeightKilograms, Listing) else Listing(
            "Float", targetWeightKilograms or [])

        self.weightIncrementPounds = weightIncrementPounds
        self.weightIncrementKilograms = weightIncrementKilograms

        self.targetRepetitionsInReserve = targetRepetitionsInReserve if isinstance(targetRepetitionsInReserve,
                                                                                   Listing) else Listing("Int",
                                                                                                         targetRepetitionsInReserve or [])
        self.targetRatePerceivedEffort = targetRatePerceivedEffort if isinstance(targetRatePerceivedEffort,
                                                                                 Listing) else Listing("Int",
                                                                                                       targetRatePerceivedEffort or [])

        self.percentage1RM = percentage1RM if isinstance(percentage1RM, Listing) else Listing("Float",
                                                                                              percentage1RM or [])

        self.progressionSchemeID = progressionSchemeID
        self.minRepetitions = minRepetitions
        self.maxRepetitions = maxRepetitions

        self.minRepetitionsList = minRepetitionsList if isinstance(minRepetitionsList, Listing) else Listing("Int",
                                                                                                             minRepetitionsList or [])
        self.maxRepetitionsList = maxRepetitionsList if isinstance(maxRepetitionsList, Listing) else Listing("Int",
                                                                                                             maxRepetitionsList or [])
        self.notes = notes

    def to_pkl_string(self, indent_level=0, is_listing_item=False):
        attrs = [self._format_attr(k, v, indent_level) for k, v in self.__dict__.items()]
        return f"new AdvancedSetScheme {{\n" + "\n".join(filter(None, attrs)) + f"\n{'  ' * indent_level}  }}"


class AdvancedExerciseSets(PKLBase):
    def __init__(self, name="", sets=0, setType=0, targetRepetitions=None, minRepetitions=None,
                 maxRepetitions=None, targetWeightPounds=None, targetWeightKilograms=None,
                 weightIncrementPounds=None, weightIncrementKilograms=None, targetRPE=None,
                 targetRIR=None, percentage1RM=None, progressionSchemeID=None, advancedSetScheme=None):
        self.name = name
        self.sets = sets
        self.setType = setType
        self.repetitions = targetRepetitions
        self.minRepetitions = minRepetitions
        self.maxRepetitions = maxRepetitions
        self.targetWeightPounds = targetWeightPounds
        self.targetWeightKilograms = targetWeightKilograms
        self.weightIncrementPounds = weightIncrementPounds
        self.weightIncrementKilograms = weightIncrementKilograms
        self.targetRatePerceivedEffort = targetRPE
        self.targetRepetitionsInReserve = targetRIR
        self.percentage1RM = percentage1RM
        self.progressionSchemeID = progressionSchemeID
        self.advancedSetScheme = advancedSetScheme

    def to_pkl_string(self, indent_level=0, is_listing_item=False):
        attrs = [self._format_attr(k, v, indent_level) for k, v in self.__dict__.items()]
        return f"new AdvancedExerciseSets {{\n" + "\n".join(filter(None, attrs)) + f"\n{'  ' * indent_level}  }}"


# --- Helper Functions ---

def to_int(s):
    """Safely converts a string to an integer, returning None on failure."""
    if not s or (isinstance(s, str) and s.lower() in ['n/a', '']): return None
    try:
        return int(float(s.strip()))  # handle "5.0"
    except (ValueError, TypeError):
        return None


def to_float(s):
    """Safely converts a string to a float, returning None on failure."""
    if not s or (isinstance(s, str) and s.lower() in ['n/a', '']): return None
    try:
        return float(s.strip())
    except (ValueError, TypeError):
        return None


def parse_list(s, item_type_str, cast_func):
    """Parses a comma-separated string into a PKL Listing."""
    if not s or (isinstance(s, str) and s.lower() in ['n/a', '']): return None
    items = [cast_func(item) for item in s.split(',') if cast_func(item) is not None]
    return Listing(item_type_str, items) if items else None


def clean_pkl_list_string(s):
    """Parses a PKL List(...) string into a Python list."""
    s = s.strip()
    if s.startswith("List(") and s.endswith(")"):
        content = s[5:-1]
        if not content.strip():
            return []
        # Split by comma but ignore whitespace
        return [x.strip() for x in content.split(',')]
    return []


def parse_pkl_schemes_file(filepath):
    """
    Parses a text file containing PKL AdvancedSetScheme definitions.
    Returns a dictionary mapping scheme IDs to AdvancedSetScheme objects.
    """
    schemes = {}
    if not os.path.exists(filepath):
        print(f"Warning: Schemes file not found at {filepath}")
        return schemes

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex to find scheme definitions: ["scheme_id"] = new AdvancedSetScheme { ... }
    # Matches the Key and the Content inside the braces
    pattern = re.compile(r'\["(.*?)"\]\s*=\s*new\s+AdvancedSetScheme\s*\{([\s\S]*?)\n\s*\}', re.MULTILINE)

    matches = pattern.findall(content)

    for scheme_id, body in matches:
        scheme_data = {}
        # Parse individual attributes within the scheme body
        # Matches: key = value
        # Note: Values might be multiline strings or Lists

        # Simple line-based parser for the body
        lines = body.strip().split('\n')
        current_key = None
        current_value = ""

        for line in lines:
            line = line.strip()
            if not line: continue

            # Check if it's a new key assignment
            if '=' in line and not line.startswith('"'):  # heuristic
                parts = line.split('=', 1)
                key = parts[0].strip()
                value = parts[1].strip()

                # If value starts with quote but doesn't end with quote (multiline string)
                if value.startswith('"') and not (value.endswith('"') and len(value) > 1):
                    current_key = key
                    current_value = value
                else:
                    scheme_data[key] = value
            elif current_key:
                # Continuation of multiline value
                current_value += "\n" + line
                if line.endswith('"'):
                    scheme_data[current_key] = current_value
                    current_key = None

        # Construct AdvancedSetScheme object
        scheme_obj = AdvancedSetScheme(
            sets=to_int(scheme_data.get('sets')),
            setType=to_int(scheme_data.get('setType')),
            setTypes=Listing("Int", [to_int(x) for x in clean_pkl_list_string(scheme_data.get('setTypes', ''))]),
            repetitions=Listing("Int", [to_int(x) for x in clean_pkl_list_string(scheme_data.get('repetitions', ''))]),
            targetRatePerceivedEffort=Listing("Int", [to_int(x) for x in clean_pkl_list_string(
                scheme_data.get('targetRatePerceivedEffort', ''))]),
            targetRepetitionsInReserve=Listing("Int", [to_int(x) for x in clean_pkl_list_string(
                scheme_data.get('targetRepetitionsInReserve', ''))]),
            minRepetitions=to_int(scheme_data.get('minRepetitions')),
            maxRepetitions=to_int(scheme_data.get('maxRepetitions')),
            minRepetitionsList=Listing("Int", [to_int(x) for x in
                                               clean_pkl_list_string(scheme_data.get('minRepetitionsList', ''))]),
            maxRepetitionsList=Listing("Int", [to_int(x) for x in
                                               clean_pkl_list_string(scheme_data.get('maxRepetitionsList', ''))]),
            notes=scheme_data.get('notes', '').strip('"') if scheme_data.get('notes') else None,
            # Add floats if present in source (not in current sample but for completeness)
            targetWeightPounds=Listing("Float", [to_float(x) for x in
                                                 clean_pkl_list_string(scheme_data.get('targetWeightPounds', ''))]),
            targetWeightKilograms=Listing("Float", [to_float(x) for x in clean_pkl_list_string(
                scheme_data.get('targetWeightKilograms', ''))]),
            percentage1RM=Listing("Float",
                                  [to_float(x) for x in clean_pkl_list_string(scheme_data.get('percentage1RM', ''))]),
        )
        schemes[scheme_id] = scheme_obj

    return schemes


# --- Main Parsing Logic ---

def parse_advanced_template_csv(csv_filepath, exercise_replacements, schemes_map=None):
    """
    Parses a CSV file based on the AdvancedProgramTemplete.csv structure
    and returns a populated Program object.
    """
    program_obj = Program()

    current_mesocycle_obj = None
    current_microcycle_obj = None
    current_workout_obj = None

    last_meso_name, last_micro_name, last_workout_name = "", "", ""

    with open(csv_filepath, 'r', encoding='utf-8') as f:
        # Detect delimiter
        sample = f.read(2048)
        f.seek(0)
        sniffer = csv.Sniffer()
        try:
            dialect = sniffer.sniff(sample)
        except csv.Error:
            dialect = None

        delimiter = dialect.delimiter if dialect else ';'  # Default to semicolon
        reader = list(csv.DictReader(f, delimiter=delimiter))

        # 1. Populate Program object from the first 1 rows
        if reader:
            program_details = reader[0]
            program_obj.name = program_details.get("Program Name", "").strip()
            program_obj.arthur = program_details.get("Program Arthur",
                                                     "").strip()  # Handle typo in CSV if needed (Arthur -> Author)
            if not program_obj.arthur: program_obj.arthur = program_details.get("Program Author", "").strip()
            program_obj.description = program_details.get("Program Description", "").strip()
            program_obj.shortDescription = program_details.get("Program Short Description", "").strip()
            program_obj.programLength = program_details.get("Program Length", "").strip()
            program_obj.level = program_details.get("Program Level", "").strip()
            program_obj.programEquipment = program_details.get("Program Equipment", "").strip()
            program_obj.daysPerWeek = program_details.get("Days Per Week", "").strip()

        # 3. Process each data row (starting from row 1, index 9)
        for row_data in reader:
            # Skip empty rows
            if not any(v for v in row_data.values() if v and v.strip()): continue

            # Get data for the current row
            meso_name = row_data.get("Mesocycle Name", "").strip()
            micro_name = row_data.get("Microcycle Name", "").strip()
            workout_name = row_data.get("Workout Name", "").strip()
            exercise_name = row_data.get("Exercise Name", "").strip()

            # Create new Mesocycle if name changes
            if meso_name and meso_name != last_meso_name:
                current_mesocycle_obj = Mesocycle(
                    name=meso_name,
                    description=row_data.get("Mesocycle Description", "").strip(),
                    order=to_int(row_data.get("Mesocycle Order")),
                )
                program_obj.mesocycles.append(current_mesocycle_obj)
                last_meso_name = meso_name
                last_micro_name, last_workout_name = "", ""  # Reset lower levels

            # Create new Microcycle if name changes
            if micro_name and micro_name != last_micro_name:
                current_microcycle_obj = Microcycle(
                    name=micro_name,
                    description=row_data.get("Microcycle Description", "").strip(),
                    order=to_int(row_data.get("Microcycle Order")),
                )
                if current_mesocycle_obj:
                    current_mesocycle_obj.microcycles.append(current_microcycle_obj)
                last_micro_name = micro_name
                last_workout_name = ""  # Reset workout

            # Create new Workout if name changes
            if workout_name and workout_name != last_workout_name:
                current_workout_obj = AdvancedWorkout(
                    name=workout_name,
                    day=to_int(row_data.get("Workout Day")),
                    notes=row_data.get("Workout Notes", "").strip()
                )
                if current_microcycle_obj:
                    current_microcycle_obj.advancedWorkouts.append(current_workout_obj)
                last_workout_name = workout_name

            # Process the exercise for the current workout
            if current_workout_obj and exercise_name:
                final_exercise_name = exercise_replacements.get(exercise_name, exercise_name)

                # Handle AdvancedSetScheme lookup
                scheme_id = row_data.get("AdvancedSetScheme", "").strip()
                scheme_obj = None
                if scheme_id and schemes_map and scheme_id.strip('"') in schemes_map:
                    scheme_obj = schemes_map[scheme_id.strip('"')]

                adv_exercise_set = AdvancedExerciseSets(
                    name=final_exercise_name,
                    sets=to_int(row_data.get("Sets")),
                    setType=to_int(row_data.get("Set Type", "1").strip()) if row_data.get("Set Type") and row_data.get(
                        "Set Type").strip().isdigit() else 1,  # Default to 1 if missing/invalid
                    targetRepetitions=parse_list(row_data.get("Target Repetitions"), "Int", to_int),
                    minRepetitions=to_int(row_data.get("Target Min Repetitions")),
                    maxRepetitions=to_int(row_data.get("Target Max Repetitions")),
                    targetWeightPounds=to_float(row_data.get("Target Weight (lbs)")),
                    targetWeightKilograms=to_float(row_data.get("Target Weight (kg)")),
                    weightIncrementPounds=to_float(row_data.get("Weight Increment (lbs)")),
                    weightIncrementKilograms=to_float(row_data.get("Weight Increment (kg)")),
                    targetRPE=parse_list(row_data.get("Target RPE"), "Int", to_int),
                    targetRIR=parse_list(row_data.get("Target RIR"), "Int", to_int),
                    percentage1RM=parse_list(row_data.get("Percentage of 1RM"), "Float", to_float),
                    progressionSchemeID=row_data.get("Progression Scheme ID", "").strip(),
                    advancedSetScheme=scheme_obj
                )
                current_workout_obj.advancedExercisesSets.append(adv_exercise_set)

    return program_obj


# --- Main Execution ---
if __name__ == "__main__":
    # Configuration for X Frame 2.0 (as an example of new functionality)
    csv_file_path = "X Frame 2.0.csv"
    schemes_file_path = "X Frame 2.0 ExerciseSchemes.txt"
    output_filename = f"X Frame 2.0 - Generated_{datetime.datetime.now().timestamp()}.pkl"

    # Load Schemes if file exists
    schemes_map = {}
    if os.path.exists(schemes_file_path):
        print(f"Loading schemes from {schemes_file_path}...")
        schemes_map = parse_pkl_schemes_file(schemes_file_path)
        print(f"Loaded {len(schemes_map)} schemes.")

    # --- USER-DEFINED EXERCISE REPLACEMENTS ---
    exercise_replacement_map = {
        # ... (Keep existing map or update as needed)
        "Smith Machine Squat": "Squat (Smith Machine)",
        "KAS Glute Bridge": "Glute Bridge (Smith Machine)",  # Example mapping
        # Add more as needed for the new programs
    }

    print(f"Parsing CSV: {csv_file_path}...")
    try:
        program = parse_advanced_template_csv(csv_file_path, exercise_replacement_map, schemes_map)

        pkl_output = program.to_pkl_string()

        # Wrap in header/footer if necessary, usually just the object is fine
        # But based on the schemes file, we might want to amend.
        # For now, just output the program object.

        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(pkl_output)

        print(f"Successfully generated PKL file: {output_filename}")

    except FileNotFoundError:
        print(f"Error: Could not find file {csv_file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")
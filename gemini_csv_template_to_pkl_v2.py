import csv
import re
from io import StringIO


# --- PKL Class Definitions for AdvancedProgramTemplate ---
# These classes model the hierarchical structure of the workout program.

class PKLBase:
  """Base class for handling the conversion of Python objects to PKL string format."""

  def to_pkl_string(self, indent_level=0, is_listing_item=False):
    raise NotImplementedError

  def _format_value(self, value, indent_level, is_listing_item=False):
    """Helper to format different Python types into PKL syntax."""
    indent_str = "  " * indent_level
    if isinstance(value, PKLBase):
      return value.to_pkl_string(indent_level, is_listing_item)
    elif isinstance(value, str):
      # Handle multiline strings
      if '\n' in value:
        lines = value.strip().split('\n')
        if len(lines) == 1 and not is_listing_item:
          return f'"{lines[0]}"'
        content_indent = "  " * (indent_level + 1)
        formatted_lines = '"""\n'
        formatted_lines += "\n".join([f"{content_indent}{line.lstrip()}" for line in lines])
        formatted_lines += f'\n{indent_str}"""'
        return formatted_lines
      return f'"{value}"'
    elif isinstance(value, bool):
      return str(value).lower()
    elif isinstance(value, (int, float)):
      return str(value)
    elif isinstance(value, Listing):
      if not value:
        return f"new Listing<{value.item_type}> {{}}" if value.item_type else "new Listing {{}}"

      item_type_str = f"<{value.item_type}>" if value.item_type else ""
      item_indent = "  " * (indent_level + 1)
      items_strs = [self._format_value(item, indent_level + 1, True) for item in value]

      if not items_strs:
        return f"new Listing{item_type_str} {{}}"

      # Improved formatting for lists of primitives
      if all(isinstance(i, (str, int, float, bool)) for i in value):
        return f"List({', '.join(map(str, items_strs))})"

      joined_items = f"\n{item_indent}".join(items_strs)
      return f"new Listing{item_type_str} {{\n{item_indent}{joined_items}\n{indent_str}  }}"
    elif value is None:
      return "null"
    else:
      return str(value)

  def _format_attr(self, attr_name, attr_value, indent_level):
    """Formats a single attribute line for a PKL object."""
    indent = "  " * (indent_level + 1)
    # Skip attributes that are None, empty strings, or empty lists, as they are default
    if attr_value is None or (isinstance(attr_value, str) and not attr_value) or (
        isinstance(attr_value, list) and not attr_value):
      return ""

    formatted_value = self._format_value(attr_value, indent_level + 1)
    return f"{indent}{attr_name} = {formatted_value}"


class Listing(list):
  """A custom list subclass to hold the type name for PKL Listings."""

  def __init__(self, item_type_name=None, *args):
    super().__init__(*args)
    self.item_type = item_type_name


class AdvancedExerciseSets(PKLBase):
  def __init__(self, name="", sets=0, setType="", repetitions=None, minRepetitions=None, maxRepetitions=None,
               targetWeightPounds=None, targetWeightKilograms=None, weightIncrementPounds=None,
               weightIncrementKilograms=None,
               targetRPE=None, targetRIR=None, percentage1RM=None, progressionSchemeID=None, notes=None):
    self.name = name
    self.sets = sets
    self.setType = setType
    self.repetitions = repetitions if repetitions is not None else Listing("Int")
    self.minRepetitions = minRepetitions
    self.maxRepetitions = maxRepetitions
    self.targetWeightPounds = targetWeightPounds if targetWeightPounds is not None else Listing("Float")
    self.targetWeightKilograms = targetWeightKilograms if targetWeightKilograms is not None else Listing("Float")
    self.weightIncrementPounds = weightIncrementPounds
    self.weightIncrementKilograms = weightIncrementKilograms
    self.targetRPE = targetRPE if targetRPE is not None else Listing("Int")
    self.targetRIR = targetRIR if targetRIR is not None else Listing("Int")
    self.percentage1RM = percentage1RM if percentage1RM is not None else Listing("Float")
    self.progressionSchemeID = progressionSchemeID
    self.notes = notes  # This field can now hold combined notes

  def to_pkl_string(self, indent_level=0, is_listing_item=False):
    base_indent_str = "  " * indent_level
    # Define the order of attributes for consistent output
    ordered_attrs = ['name', 'sets', 'setType', 'repetitions', 'minRepetitions', 'maxRepetitions',
                     'targetRPE', 'targetRIR', 'percentage1RM', 'targetWeightPounds', 'targetWeightKilograms',
                     'weightIncrementPounds', 'weightIncrementKilograms', 'progressionSchemeID', 'notes']
    attrs = [self._format_attr(attr, getattr(self, attr, None), indent_level) for attr in ordered_attrs]
    valid_attrs = [attr for attr in attrs if attr]
    return f"new AdvancedExerciseSets {{\n" + "\n".join(valid_attrs) + f"\n{base_indent_str}  }}"


class AdvancedWorkout(PKLBase):
  def __init__(self, name="", day=0, notes="", advancedExercisesSets=None):
    self.name = name
    self.day = day
    self.notes = notes
    self.advancedExercisesSets = advancedExercisesSets if advancedExercisesSets is not None else Listing(
      "AdvancedExerciseSets")

  def to_pkl_string(self, indent_level=0, is_listing_item=False):
    base_indent_str = "  " * indent_level
    attrs = [self._format_attr(k, v, indent_level) for k, v in self.__dict__.items()]
    return f"new AdvancedWorkout {{\n" + "\n".join(filter(None, attrs)) + f"\n{base_indent_str}  }}"


class Microcycle(PKLBase):
  def __init__(self, name="", description="", order=0, advancedWorkouts=None):
    self.name = name
    self.description = description
    self.order = order
    self.advancedWorkouts = advancedWorkouts if advancedWorkouts is not None else Listing("AdvancedWorkout")

  def to_pkl_string(self, indent_level=0, is_listing_item=False):
    base_indent_str = "  " * indent_level
    attrs = [self._format_attr(k, v, indent_level) for k, v in self.__dict__.items()]
    return f"new Microcycle {{\n" + "\n".join(filter(None, attrs)) + f"\n{base_indent_str}  }}"


class Mesocycle(PKLBase):
  def __init__(self, name="", description="", order=0, microcycles=None):
    self.name = name
    self.description = description
    self.order = order
    self.microcycles = microcycles if microcycles is not None else Listing("Microcycle")

  def to_pkl_string(self, indent_level=0, is_listing_item=False):
    base_indent_str = "  " * indent_level
    attrs = [self._format_attr(k, v, indent_level) for k, v in self.__dict__.items()]
    return f"new Mesocycle {{\n" + "\n".join(filter(None, attrs)) + f"\n{base_indent_str}  }}"


class Program(PKLBase):
  def __init__(self, name="", arthur="", shortDescription="", description="", programLength="", uri="", level="",
               programEquipment="", daysPerWeek="", mesocycles=None):
    self.name = name;
    self.arthur = arthur;
    self.shortDescription = shortDescription;
    self.description = description
    self.programLength = programLength;
    self.uri = uri;
    self.level = level;
    self.programEquipment = programEquipment
    self.daysPerWeek = daysPerWeek;
    self.mesocycles = mesocycles if mesocycles is not None else Listing("Mesocycle")

  def to_pkl_string(self, indent_level=0, is_listing_item=False):
    base_indent_str = "  " * indent_level
    obj_name = "program"
    attrs = [self._format_attr(k, v, indent_level) for k, v in self.__dict__.items()]
    valid_attrs = [attr for attr in attrs if attr]
    return f"{obj_name} = new Program {{\n" + "\n".join(valid_attrs) + f"\n{base_indent_str}}}"


# --- Helper Functions ---

def parse_csv_list(cell_value, value_type=str):
  """Parses a comma-separated string from a CSV cell into a list of a specified type."""
  if not cell_value or cell_value.lower() == 'n/a':
    return None
  try:
    # Split by comma and strip whitespace from each item
    items = [item.strip() for item in cell_value.split(',')]
    # Convert each item to the desired type (int, float, etc.)
    return [value_type(item) for item in items if item]
  except (ValueError, TypeError):
    # Return None if conversion fails
    return None


# --- Main Parsing Logic ---
def parse_advanced_template_csv(csv_filepath):
  """Parses the AdvancedProgramTemplete.csv and builds the Program object."""
  program_obj = Program()
  current_mesocycle_obj = None
  current_microcycle_obj = None
  current_advanced_workout_obj = None

  with open(csv_filepath, 'r', encoding='utf-8') as f:
    reader = list(csv.reader(f))  # Read all rows to easily access metadata and data

  # 1. Parse Program-level metadata from the first few rows
  program_meta_map = {
    "Program Name": "name", "Program Arthur": "arthur", "Program Description": "description",
    "Program Length": "programLength", "Program Level": "level",
    "Program Equipment": "programEquipment", "Days Per Week": "daysPerWeek"
  }
  for row in reader[:7]:
    key, value = row[0], row[1]
    if key in program_meta_map:
      setattr(program_obj, program_meta_map[key], value)

  # 2. Find the header row and map column names to indices
  header_row_index = -1
  for i, row in enumerate(reader):
    if row and row[0] == "Mesocycle Name":
      header_row_index = i
      break
  if header_row_index == -1:
    raise ValueError("Could not find the header row in the CSV.")

  headers = reader[header_row_index]
  col_map = {header: i for i, header in enumerate(headers)}
  data_rows = reader[header_row_index + 1:]

  # 3. Iterate through data rows and build the object hierarchy
  for row in data_rows:
    if not any(field.strip() for field in row) or len(row) < len(headers):
      continue  # Skip empty rows

    # --- Check for new Mesocycle ---
    meso_name = row[col_map["Mesocycle Name"]]
    if not current_mesocycle_obj or current_mesocycle_obj.name != meso_name:
      current_mesocycle_obj = Mesocycle(
        name=meso_name,
        description=row[col_map["Mesocycle Description"]],
        order=int(row[col_map["Mesocycle Order"]])
      )
      program_obj.mesocycles.append(current_mesocycle_obj)

    # --- Check for new Microcycle ---
    micro_name = row[col_map["Microcycle Name"]]
    if not current_microcycle_obj or current_microcycle_obj.name != micro_name:
      current_microcycle_obj = Microcycle(
        name=micro_name,
        description=row[col_map["Microcycle Description"]],
        order=int(row[col_map["Microcycle Order"]])
      )
      current_mesocycle_obj.microcycles.append(current_microcycle_obj)

    # --- Check for new Workout ---
    workout_name = row[col_map["Workout Name"]]
    if not current_advanced_workout_obj or current_advanced_workout_obj.name != workout_name:
      current_advanced_workout_obj = AdvancedWorkout(
        name=workout_name,
        day=int(row[col_map["Workout Day"]]),
        notes=row[col_map["Workout Notes"]]
      )
      current_microcycle_obj.advancedWorkouts.append(current_advanced_workout_obj)

    # --- Create and Add the AdvancedExerciseSets object for the current row ---
    exercise_sets = AdvancedExerciseSets(
      name=row[col_map["Exercise Name"]],
      sets=int(row[col_map["Sets"]]) if row[col_map["Sets"]].isdigit() else 0,
      setType=row[col_map["Set Type"]],
      repetitions=Listing("Int", parse_csv_list(row[col_map["Target Repetitions"]], int)),
      minRepetitions=int(row[col_map["Target Min Repetitions"]]) if row[
        col_map["Target Min Repetitions"]].isdigit() else None,
      maxRepetitions=int(row[col_map["Target Max Repetitions"]]) if row[
        col_map["Target Max Repetitions"]].isdigit() else None,
      targetWeightPounds=Listing("Float", parse_csv_list(row[col_map["Target Weight (lbs)"]], float)),
      targetWeightKilograms=Listing("Float", parse_csv_list(row[col_map["Target Weight (kg)"]], float)),
      weightIncrementPounds=float(row[col_map["Weight Increment (lbs)"]]) if row[
        col_map["Weight Increment (lbs)"]] else None,
      weightIncrementKilograms=float(row[col_map["Weight Increment (kg)"]]) if row[
        col_map["Weight Increment (kg)"]] else None,
      targetRPE=Listing("Int", parse_csv_list(row[col_map["Target RPE"]], int)),
      targetRIR=Listing("Int", parse_csv_list(row[col_map["Target RIR"]], int)),
      percentage1RM=Listing("Float", parse_csv_list(row[col_map["Percentage of 1RM"]], float)),
      progressionSchemeID=row[col_map["Progression Scheme ID"]]
    )
    current_advanced_workout_obj.advancedExercisesSets.append(exercise_sets)

  return program_obj


# --- Main Execution Block ---
if __name__ == "__main__":
  csv_file_path = 'AdvancedProgramTemplete.csv'
  output_filename = "generated_program_from_template.pkl"

  print(f"--- Parsing {csv_file_path} ---")
  try:
    program_data = parse_advanced_template_csv(csv_file_path)
    print("Parsing complete. Generating PKL file...")
  except Exception as e:
    print(f"An error occurred during parsing: {e}")
    exit()

  # Define the PKL class schema to be included at the top of the output file
  class_definitions_pkl_str = """"\
class Program {
  name: String
  arthur: String
  shortDescription: String
  description: String
  programLength: String
  uri: String
  level: String
  programEquipment: String
  daysPerWeek: String
  mesocycles: Listing<Mesocycle>
}

class Mesocycle {
  name: String
  description: String
  order: Int
  microcycles: Listing<Microcycle>
}

class Microcycle {
  name: String
  description: String
  order: Int
  workouts: Listing<Workout>
  advancedWorkouts: Listing<AdvancedWorkout>
}

class Workout {
  name: String
  day: Int
  notes: Listing
  exercisesSets: Listing<ExerciseSets>
}

class AdvancedWorkout {
  name: String
  day: Int
  notes: Listing<String>
  exercisesSets: Listing<ExerciseSets>
  advancedExercisesSets: Listing<AdvancedExerciseSets>
}

class ExerciseSets {
  name: String
  notes: Listing
  // Number of sets to be performed
  sets: Int
  // Target Repetitions
  repetitions: Int? = null

  // Normal by default, Listing - length/number of elements must equal number of sets
  setType: String = ""

  targetWeightPounds: Float? = null
  targetWeightKilograms: Float? = null

  weightIncrementPounds: Float? = null
  weightIncrementKilograms: Float? = null

  targetRepetitionsInReserve: Int? = null // Reps in Reserve
  targetRatePerceivedEffort: Int? = null // Rate of Perceived Exertion
  percentage1RM: Float? = null // Percentage of 1 Rep Max

  // TODO Determine Correct Type
  progressionSchemeID: String? = null
  minRepetitions: Int? = null
  maxRepetitions: Int? = null
}

class AdvancedExerciseSets {
  name: String
  description: String
  notes: Listing<String>
  sets: Int
  setType: Int = 1
  repetitions: Listing<Int>? = null
  targetRepetitionsInReserve: Listing<Int>? = null
  targetRatePerceivedEffort: Listing<Int>? = null
  targetWeightPounds: Listing<Float>? = null
  targetWeightKilograms: Listing<Float>? = null
  weightIncrementPounds: Float? = null
  weightIncrementKilograms: Float? = null
  percentage1RM: Listing<Float>? = null
  progressionSchemeID: String? = null
  minRepetitions: Int? = null
  maxRepetitions: Int? = null
  setScheme: Listing<SetScheme>
}

class SetScheme {
  sets: Int
  setType: Int = 1
  repetitions: Listing<Int>
  targetWeightPounds: Listing<Float>
  targetWeightKilograms: Listing<Float>
  weightIncrementPounds: Float? = null
  weightIncrementKilograms: Float? = null
  targetRepetitionsInReserve: Listing<Int>
  targetRatePerceivedEffort: Listing<Int> // rpe for each set
  percentage1RM: Listing<Float>
  progressionSchemeID: String? = null
  minRepetitions: Int? = null
  maxRepetitions: Int? = null
}
"""

  # Combine the module header, class definitions, and the generated program instance
  header = f"module com.example.programs.MyAdvancedProgram\n\n{class_definitions_pkl_str}\n"
  full_pkl_output = f"{header}\n// --- Program Instance ---\n{program_data.to_pkl_string()}\n"

  try:
    with open(output_filename, "w", encoding='utf-8') as f:
      f.write(full_pkl_output)
    print(f"\nSuccessfully generated PKL file: {output_filename}")
  except Exception as e:
    print(f"\nError writing to file: {e}")

import csv
import datetime
import re
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
  def __init__(self, name="", arthur="", description="", shortDescription="", programLength="", level="", programEquipment="",
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


class AdvancedExerciseSets(PKLBase):
  def __init__(self, name="", sets=0, setType=0, targetRepetitions=None, minRepetitions=None,
               maxRepetitions=None, targetWeightPounds=None, targetWeightKilograms=None,
               weightIncrementPounds=None, weightIncrementKilograms=None, targetRPE=None,
               targetRIR=None, percentage1RM=None, progressionSchemeID=None):
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

  def to_pkl_string(self, indent_level=0, is_listing_item=False):
    attrs = [self._format_attr(k, v, indent_level) for k, v in self.__dict__.items()]
    return f"new AdvancedExerciseSets {{\n" + "\n".join(filter(None, attrs)) + f"\n{'  ' * indent_level}  }}"


# --- Helper Functions ---

def to_int(s):
  """Safely converts a string to an integer, returning None on failure."""
  if not s or s.lower() in ['n/a', '']: return None
  try:
    return int(s.strip())
  except (ValueError, TypeError):
    return None


def to_float(s):
  """Safely converts a string to a float, returning None on failure."""
  if not s or s.lower() in ['n/a', '']: return None
  try:
    return float(s.strip())
  except (ValueError, TypeError):
    return None


def parse_list(s, item_type_str, cast_func):
  """Parses a comma-separated string into a PKL Listing."""
  if not s or s.lower() in ['n/a', '']: return None
  items = [cast_func(item) for item in s.split(',') if cast_func(item) is not None]
  return Listing(item_type_str, items) if items else None


# --- Main Parsing Logic ---

def parse_advanced_template_csv(csv_filepath, exercise_replacements):
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
    reader = list(csv.DictReader(f))

    # 1. Populate Program object from the first 1 rows
    program_details = reader[0]
    program_obj.name = program_details.get("Program Name", "").strip()
    program_obj.arthur = program_details.get("Program Arthur", "").strip()
    program_obj.description = program_details.get("Program Description", "").strip()
    program_obj.shortDescription = program_details.get("Program Short Description", "").strip()
    program_obj.programLength = program_details.get("Program Length", "").strip()
    program_obj.level = program_details.get("Program Level", "").strip()
    program_obj.programEquipment = program_details.get("Program Equipment", "").strip()
    program_obj.daysPerWeek = program_details.get("Days Per Week", "").strip()

    # 2. Define column indices from the header (row 9, index 8)
    header = [h.strip() for h in reader[0]]
    # cols = {name: i for i, name in enumerate(header)}

    # 3. Process each data row (starting from row 1, index 9)
    for row_data in reader:
      if not any(field.strip() for field in row_data): continue

      # Get data for the current row
      meso_name = row_data["Mesocycle Name"].strip()
      micro_name = row_data["Microcycle Name"].strip()
      workout_name = row_data["Workout Name"].strip()
      exercise_name = row_data["Exercise Name"].strip()

      # Create new Mesocycle if name changes
      if meso_name and meso_name != last_meso_name:
        current_mesocycle_obj = Mesocycle(
          name=meso_name,
          description=row_data["Mesocycle Description"].strip(),
          order=to_int(row_data["Mesocycle Order"]),
        )
        program_obj.mesocycles.append(current_mesocycle_obj)
        last_meso_name = meso_name
        last_micro_name, last_workout_name = "", ""  # Reset lower levels

      # Create new Microcycle if name changes
      if micro_name and micro_name != last_micro_name:
        current_microcycle_obj = Microcycle(
          name=micro_name,
          description=row_data["Microcycle Description"].strip(),
          order=to_int(row_data["Microcycle Order"]),
        )
        if current_mesocycle_obj:
          current_mesocycle_obj.microcycles.append(current_microcycle_obj)
        last_micro_name = micro_name
        last_workout_name = ""  # Reset workout

      # Create new Workout if name changes
      if workout_name and workout_name != last_workout_name:
        current_workout_obj = AdvancedWorkout(
          name=workout_name,
          day=to_int(row_data["Workout Day"]),
          notes=row_data["Workout Notes"].strip()
        )
        if current_microcycle_obj:
          current_microcycle_obj.advancedWorkouts.append(current_workout_obj)
        last_workout_name = workout_name

      # Process the exercise for the current workout
      if current_workout_obj and exercise_name:
        final_exercise_name = exercise_replacements.get(exercise_name, exercise_name)

        adv_exercise_set = AdvancedExerciseSets(
          name=final_exercise_name,
          sets=to_int(row_data["Sets"]),
          setType=to_int(row_data["Set Type"].strip()),
          targetRepetitions=parse_list(row_data["Target Repetitions"], "Int", to_int),
          minRepetitions=to_int(row_data["Target Min Repetitions"]),
          maxRepetitions=to_int(row_data["Target Max Repetitions"]),
          targetWeightPounds=to_float(row_data["Target Weight (lbs)"]),
          targetWeightKilograms=to_float(row_data["Target Weight (kg)"]),
          weightIncrementPounds=to_float(row_data["Weight Increment (lbs)"]),
          weightIncrementKilograms=to_float(row_data["Weight Increment (kg)"]),
          targetRPE=parse_list(row_data["Target RPE"], "Int", to_int),
          targetRIR=parse_list(row_data["Target RIR"], "Int", to_int),
          percentage1RM=parse_list(row_data["Percentage of 1RM"], "Float", to_float),
          progressionSchemeID=row_data["Progression Scheme ID"].strip()
        )
        current_workout_obj.advancedExercisesSets.append(adv_exercise_set)

  return program_obj


# --- Main Execution ---
if __name__ == "__main__":
  csv_file_path = "/home/pablo/Downloads/workout_programs/Strong & Sculpted Program/Brad Schoenfeld - Strong & Sculpted_updated.csv"
  output_filename = f"Brad Schoenfeld - Strong & Sculpted AdvancedProgramTemplate_{datetime.datetime.now().timestamp()}.pkl"

  # --- USER-DEFINED EXERCISE REPLACEMENTS ---
  # This allows for easy substitution of exercises without editing the CSV.
  exercise_replacement_map = {
    "1-Arm 45° Cable Rear Delt Flye": "Cable One Arm Reverse Fly",
    "1-Arm Dumbbell Row": "Dumbbell Bent-over Row",
    "11 Heel-Elevated Goblet Squat": "Goblet Squat",  # 1 ¼ Heel-Elevated Goblet Squat
    "1l Barbell Hip Thrust": "Barbell Hip Thrust",  # 1 ¼ Barbell Hip Thrust
    "45-Degree Side Bend": "45° Side Bend",
    "45-Dgree Side Bend": "45° Side Bend",
    "45° Hyperextension": "45° Hyperextension",
    "45° Incline Barbell Press": "Barbell Incline Bench Press",
    "45° Incline DB Press": "Dumbbell Incline Bench Press",
    "45° Incline Machine Press": "Lever Incline Bench Press",
    "Ab Wheel Rollout From Knees": "Wheel Rollout",
    "Ab Wheel Rollout": "Wheel Rollout",
    "American Deadlift": "Barbell Straight-back Straight-leg Deadlift",
    "American Hip Thrust": "Barbell Hip Thrust",
    "Antirotation Press": "Cable Push Pull",
    "Arnold Press": "Dumbbell Shoulder Press",
    "Back Squat": "Barbell Full Squat",
    "Band Rotary Hold": "Cable Push Pull",
    "Band Seated Abduction": "Lever Seated Hip Abduction",
    "Band Seated Hip Abduction": "Lever Seated Hip Abduction",
    "Band Standing Abduction": "Cable Hip Abduction",
    "Banded 45-Degree Kickback": "Cable Glute Kickback",
    "Banded Abduction (Seated)": "Lever Seated Hip Abduction",
    "Banded Cha-Cha": "Lever Bent-over Glute Kickback",
    "Banded Fire Hydrant": "Lever Seated Hip Abduction",
    "Banded Frog Pump": "Weighted Single Leg Hip Thrust (leg extended)",
    "Banded Front Raise": "Cable One Arm Front Raise",
    "Banded Hip Abduction": "Lever Seated Hip Abduction",
    "Banded Hip Rotation": "Cable Lying Hip External Rotation",
    "Banded Hip Thrust": "Barbell Hip Thrust",
    "Banded Kneeling Hip Thrust": "Barbell Hip Thrust",
    "Banded Lateral Raise": "Cable One Arm Lateral Raise",
    "Banded Pallof Press": "Cable Push Pull",
    "Banded Seat Abduction": "Lever Seated Hip Abduction",
    "Banded Seated Hip Abduction": "Lever Seated Hip Abduction",
    "Banded Side Lying Clams": "Lever Seated Hip Adduction",
    "Banded Side Walk": "Lever Seated Hip Adduction",
    "Banded Squat Bouncer": "Goblet Squat",
    "Banded Standing Hip Abduction": "Lever Seated Hip Adduction",
    "Banded Standing Hip External Rotation": "Cable Lying Hip External Rotation",
    "Banded Sumo Walk": "Lever Seated Hip Adduction",
    "Banded Supine Abduction": "Lever Seated Hip Abduction",
    "Barbell American Deadlift": "Barbell Straight-back Straight-leg Deadlift",
    "Barbell American Hip Thrust (Constant Tension Method)": "Barbell Hip Thrust",
    "Barbell American Hip Thrust": "Barbell Hip Thrust",
    "Barbell Back Squat": "Barbell Full Squat",
    "Barbell Bench Press": "Barbell Bench Press",
    "Barbell Bent-Row": "Barbell Bent-over Row",
    "Barbell Box Squat": "Barbell Full Squat",
    "Barbell Chest Press": "Barbell Bench Press",
    "Barbell Decline Press": "Barbell Decline Bench Press",
    "Barbell Drag Curl": "Barbell Drag Curl",
    "Barbell Front Squat": "Barbell Front Squat",
    "Barbell Glute Bridge": "Barbell Hip Thrust",
    "Barbell Good Morning": "Barbell Good-morning",
    "Barbell High Box Squat": "Barbell Full Squat",
    "Barbell Hip Thrust (Constant Tension Method)": "Barbell Hip Thrust",
    "Barbell Hip Thrust (Dropset)": "Barbell Hip Thrust",
    "Barbell Hip Thrust (Isohold Method)": "Barbell Hip Thrust",
    "Barbell Hip Thrust (Pause Rep Method)": "Barbell Hip Thrust",
    "Barbell Hip Thrust (Rest Pause Method)": "Barbell Hip Thrust",
    "Barbell Hip Thrust (Rest/Pause Method)": "Barbell Hip Thrust",
    "Barbell Hip Thrust Dropset": "Barbell Hip Thrust",
    "Barbell Hip Thrust": "Barbell Hip Thrust",
    "Barbell Incline Press": "Barbell Incline Bench Press",
    "Barbell Kneeling Rollout": "Wheel Rollout",
    "Barbell Military Press": "Barbell Shoulder Press",
    "Barbell Parallel Squat": "Barbell Full Squat",
    "Barbell Push Press": "Barbell Shoulder Press",
    "Barbell RDL": "Barbell Straight-back Straight-leg Deadlift",
    "Barbell Reverse Bent Row": "Barbell Underhand Bent-over Row",
    "Barbell Reverse Curl": "Barbell Reverse Curl",
    "Barbell Romanian Deadlift": "Barbell Straight-back Straight-leg Deadlift",
    "Barbell Single-Leg Rdl": "Barbell Straight-back Straight-leg Deadlift",
    "Barbell Stiff-Leg Deadlift": "Barbell Straight-back Straight-leg Deadlift",
    "Barbell Upright Row": "Barbell Upright Row",
    "Barbell Zercher Squat": "Barbell Zercher Squat",
    "Bayesian Cable Curl": "Bayesian Curl",
    "Bench Dip": "Bench Dip",
    "Bench Press": "Barbell Bench Press",
    "Between Bench Dumbbell Squat": "Goblet Squat",
    "Bicycle Crunch": "Wrist-to-Knee (Bicycle) Crunch",
    "Body Saw": "Front Plank",
    "Bodyweight 45-Degree Back Ext.": "45° Hyperextension",
    "Bodyweight Back Extension": "45° Hyperextension",
    "Bodyweight Bent-Over Ytwl": "Dumbbell Incline Y Raise",
    "Bodyweight Box Squat": "Squat",
    "Bodyweight Bulgarian Split Squat": "Single Leg Split Squat",
    "Bodyweight Chin-Up": "Chin-up",
    "Bodyweight Eccentric Chin-Up": "Machine-assisted Chin-up",
    "Bodyweight Eccentric Push-Up": "Push-up",
    "Bodyweight Extra-Range Side-Lying Hip Abduction": "Weighted Lying Hip Abduction",
    "Bodyweight Feet-Elevated Glute Bridge": "Single Leg Hip Bridge",
    "Bodyweight Foot Elevated Single-Leg Glute Bridge": "Weighted Single Leg Hip Thrust (leg extended)",
    "Bodyweight Full Squat": "Squat",
    "Bodyweight Glute Bridge": "Single Leg Hip Bridge",
    "Bodyweight Glute-Dominant Back Extension": "45° Hyperextension",
    "Bodyweight High Step-Up": "Step-up",
    "Bodyweight Hip Thrust (Pause Rep Method)": "Glute-Ham Raise",
    "Bodyweight Hip Thrust": "Glute-Ham Raise",
    "Bodyweight Inverted Row": "Inverted Row",
    "Bodyweight Knee Push-Up": "ush-up (on knees)",
    "Bodyweight Knee-Banded Glute Bridge": "Single Leg Hip Bridge",
    "Bodyweight Medium Step-Up": "Step-up",
    "Bodyweight Neutral Grip Pull-Up": "Neutral Grip Pull-up",
    "Bodyweight Parallel Box Squat": "Squat",
    "Bodyweight Parallel Squat": "Squat",
    "Bodyweight Plank": "Front Plank",
    "Bodyweight Push-Up": "Push-up",
    "Bodyweight Reverse Hyper Extension": "Reverse Hyper-extension",
    "Bodyweight Reverse Hyperextension": "Reverse Hyper-extension",
    "Bodyweight Reverse Lunge": "Rear Lunge",
    "Bodyweight Rkc Plank": "Front Plank",
    "Bodyweight Shoulder And Foot Elevated Single-Leg Hip Thrust (Pause Rep Method)": "Weighted Single Leg Hip Thrust (leg extended)",
    "Bodyweight Shoulder Elevated Single-Leg Hip Thrust": "Weighted Single Leg Hip Thrust (leg extended)",
    "Bodyweight Side Plank": "Side Plank",
    "Bodyweight Side-Lying Clam": "Lever Seated Hip Abduction",
    "Bodyweight Side-Lying Hip Abduction": "Weighted Lying Hip Abduction",
    "Bodyweight Side-Lying Hip Raise": "Bent Knee Side Bridge Hip Abduction",
    "Bodyweight Single-Leg Glute Bridge": "Weighted Single Leg Hip Thrust (leg extended)",
    "Bodyweight Single-Leg Hip Thrust (Shoulder And Foot Elevated)": "Weighted Single Leg Hip Thrust (leg extended)",
    "Bodyweight Single-Leg Hip Thrust": "Weighted Single Leg Hip Thrust (leg extended)",
    "Bodyweight Single-Leg Rdl": "Single Leg Stiff-leg Deadlift",
    "Bodyweight Skater Squat": "Single Leg Squat (with leg back)",
    "Bodyweight Step Up": "Step-up",
    "Bodyweight Torso-Elevated Push-Up": "Incline Push-up",
    "Bodyweight Walking Lunge": "Lunge",
    "Bottom-Half DB Flye": "Dumbbell Fly",
    "Bottom-Half Seated Cable Flye": "Cable Seated Fly",
    "Braced Single-Leg Rdl": "Single Leg Stiff-leg Deadlift",
    "Bulgarian Split Squat": "Dumbbell Single Leg Split Squat",
    "Cable Crossover Ladder": "Cable Standing Fly",
    "Cable Crunch": "Cable Kneeling Crunch",
    "Cable Curl": "Bayesian Curl",
    "Cable Glute Back Kick": "Cable Glute Kickback",
    "Cable Glute Kick Back": "Cable Glute Kickback",
    "Cable Hip Abduction": "Cable Hip Abduction",
    "Cable Hip Rotation": "Cable Lying Hip External Rotation",
    "Cable Kickback": "Cable Glute Kickback",
    "Cable Kneeling Bent Reverse Fly": "Cable One Arm Reverse Fly",
    "Cable Kneeling Kickback": "Cable Glute Kickback",
    "Cable Kneeling Rope Crunch": "Cable Kneeling Crunch",
    "Cable Lateral Raise": "Cable One Arm Lateral Raise",
    "Cable Paused Shrug-In": "Cable Shrug (dual pulley)",
    "Cable Pull-Through": "Dumbbell Straight-back Straight-leg Deadlift",
    "Cable Pullthrough": "Dumbbell Straight-back Straight-leg Deadlift",
    "Cable Reverse Fly": "Cable One Arm Reverse Fly",
    "Cable Rope Hammer Curl": "Cable Hammer Curl",
    "Cable Rope Overhead Triceps Extension": "Cable Triceps Extension",
    "Cable Rope Tricep Extension": "Cable Triceps Extension (with rope)",
    "Cable Seated Row": "Cable Seated Row",
    "Cable Shoulder Press": "Cable Shoulder Press",
    "Cable Side Bend": "Cable Side Bend",
    "Cable Single-Arm Standing Low Row": "Cable Standing Low Row",
    "Cable Standing Abduction": "Cable Hip Abduction",
    "Cable Standing Glute Kickback": "Cable Glute Kickback",
    "Cable Standing Hip Abduction": "Cable Hip Abduction",
    "Cable Straight-Arm Pulldown": "Cable Bent-over Pullover",
    "Cable Straight-Leg Pull-Through": "Cable Straight-back Stiff-leg Deadlift",
    "Cable Tricep Pushdown": "Cable Pushdown",
    "Cable Triceps Kickback": "Cable One Arm Pushdown",
    "Cable Triceps Press-Down": "Cable Pushdown",
    "Cable Upright Row": "Cable Upright Row",
    "Cable Wide-Grip Seated Row": "Cable Wide Grip Seated Row",
    "Calves on Leg Press": "Lever 45° Calf Raise (plate loaded)",
    "Chest-Supported Machine Row": "Lever Seated Row",
    "Chest-Supported Row": "Dumbbell Incline Row",
    "Chest-Supported T-Bar Row": "Lever T-bar Row (plate loaded)",
    "Chin-Up (Band Assisted)": "Band-assisted Chin-up",
    "Chin-Up": "Chin-up",
    "Close Grip Barbell Bench Press": "Barbell Close Grip Bench Press",
    "Close Grip Lat Pulldown": "Cable Close Grip Pulldown",
    "Close Grip Seated Cable Row": "Cable Seated Row",
    "Close-Grip Bench Press": "Barbell Close Grip Bench Press",
    "Close-Grip Push-Up": "Close Grip Push-up",
    "Concentration Cable Curl": "Cable Concentration Curl",
    "Concentration Curl": "Dumbbell Concentration Curl",
    "Conventional Deadlift": "Barbell Deadlift",
    "Cross Cable Pull-Down": "Cable One Arm Kneeling Pulldown",
    "Crunch Variation (Abs)": "Crunch",
    "Crunch": "Crunch",
    "Cuff/Dip Belt Cable Hip Rotation": "Cable Lying Hip External Rotation",
    "D-Handle Lat Pulldown": "Cable Pulldown",
    "DB Bench Press": "Dumbbell Bench Press",
    "DB Bulgarian Split Squat": "Dumbbell Single Leg Split Squat",
    "DB Concentration Curl": "Dumbbell Concentration Curl",
    "DB Curl": "Dumbbell Curl",
    "DB Hammer Curl": "Dumbbell Hammer Curl",
    "DB Preacher Curl": "Dumbbell Preacher Curl",
    "DB RDL": "Dumbbell Straight-back Straight-leg Deadlift",
    "DB Shrug": "Dumbbell Shrug",
    "DB Skull Crusher": "Dumbbell Lying Triceps Extension",
    "DB Static Lunge": "Dumbbell Rear Lunge",
    "DB Step-Up": "Dumbbell Step-Up",
    "DB Triceps Kickback": "Dumbbell Kickback",
    "DB Walking Lunge": "Dumbbell Walking Lunge",
    "Deadlift ": "Barbell Deadlift",
    "Deadlift": "Barbell Deadlift",
    "Deadstop Foot-Elevated Single-Leg Hip Thrust": "Weighted Single Leg Hip Thrust (leg extended)",
    "Decline Weighted Crunch": "Weighted Incline Sit-up",
    "Deficit Bodyweight Bulgarian Split Squat": "Dumbbell Deficit Single Leg Split Squat",
    "Deficit Curtsy Lunge": "Deficit Curtsy Lunge",
    "Double-Banded Hip Thrust": "Barbell Hip Thrust",
    "Dual-Handle Elbows-Out Cable Row": "Cable Seated High Row",
    "Dual-Handle Lat Pulldown": "Cable Parallel Grip Pulldown",
    "Dumbbell 45-Degree Hyper": "Dumbbell 45° Hyperextension",
    "Dumbbell 45° Hyperextension": "Dumbbell 45° Hyperextension",
    "Dumbbell Back Extension": "Dumbbell 45° Hyperextension",
    "Dumbbell Bent Over Row": "Dumbbell Bent-over Row",
    "Dumbbell Between-Bench Squat": "Goblet Squat",
    "Dumbbell Biceps Curl": "Dumbbell Curl",
    "Dumbbell Bulgarian Split Squat": "Dumbbell Single Leg Split Squat",
    "Dumbbell Chest Press": "Dumbbell Bench Press",
    "Dumbbell Chest Supported Row": "Dumbbell Incline Row",
    "Dumbbell Chest-Supported Row": "Dumbbell Incline Row",
    "Dumbbell Curtsy Lunge": "Deficit Curtsy Lunge",
    "Dumbbell Decline Press": "Dumbbell Decline Bench Press",
    "Dumbbell Deficit Bulgarian Split Squat": "Dumbbell Deficit Single Leg Split Squat",
    "Dumbbell Deficit Curtsy Lunge": "Deficit Curtsy Lunge",
    "Dumbbell Deficit Reverse Lunge": "Dumbbell Rear Lunge",
    "Dumbbell Front Raise": "Dumbbell Front Raise",
    "Dumbbell Glute-Dominant Back Extension": "Dumbbell 45° Hyperextension",
    "Dumbbell High Step Up": "Dumbbell Step-up",
    "Dumbbell Hip Thrust": "Weighted Hip Thrust",
    "Dumbbell Incline Biceps Curl": "Dumbbell Incline Curl",
    "Dumbbell Incline Fly": "Dumbbell Incline Fly",
    "Dumbbell Incline Press": "Dumbbell Incline Bench Press",
    "Dumbbell Lateral Raise": "Dumbbell Lateral Raise",
    "Dumbbell Lunge": "Dumbbell Rear Lunge",
    "Dumbbell Military Press": "Dumbbell Shoulder Press",
    "Dumbbell One-Arm Row": "Dumbbell Bent-over Row",
    "Dumbbell Overhead Triceps Extension": "Dumbbell One Arm Triceps Extension",
    "Dumbbell Prone Incline Curl": "Dumbbell Prone Incline Curl",
    "Dumbbell Pullover": "Dumbbell Pullover",
    "Dumbbell Raise Complex": "Cable One Arm Lateral Raise",
    "Dumbbell Rear Delt Raise": "Dumbbell Rear Lateral Raise",
    "Dumbbell Reverse Lunge": "Dumbbell Rear Lunge",
    "Dumbbell Romanian Deadlift": "Dumbbell Straight-back Straight-leg Deadlift",
    "Dumbbell Seated Bent Reverse Fly": "Cable One Arm Reverse Fly",
    "Dumbbell Shoulder Press": "Dumbbell Shoulder Press",
    "Dumbbell Side Bend": "Dumbbell Side Bend",
    "Dumbbell Side Lunge": "Dumbbell Side Lunge",
    "Dumbbell Single-Arm Row": "Dumbbell Bent-over Row",
    "Dumbbell Single-Leg Rdl": "Dumbell Single Leg Stiff-leg Deadlift",
    "Dumbbell Single-Leg Romanian Deadlift": "Dumbell Single Leg Stiff-leg Deadlift",
    "Dumbbell Single-Leg Standing Calf Raise": "Dumbbell Single Leg Calf Raise",
    "Dumbbell Skull Crusher": "Dumbbell Lying Triceps Extension",
    "Dumbbell Squat": "Dumbbell Squat",
    "Dumbbell Standing Calf Raise": "Dumbbell Standing Calf Raise",
    "Dumbbell Standing Shoulder Press": "Dumbbell Shoulder Press",
    "Dumbbell Step Up/Reverse Lunge Combo": "Dumbbell Step-up",
    "Dumbbell Stiff-Leg Deadlift": "Dumbbell Straight-back Straight-leg Deadlift",
    "Dumbbell Swiss Ball Crunch": "Weighted Crunch (on stability ball)",
    "Dumbbell Triceps Kickback": "Dumbbell Kickback",
    "Dumbbell Upright Row": "Dumbbell Upright Row",
    "Dynamic Effort Deadlift": "Barbell Straight-back Straight-leg Deadlift",
    "EZ-Bar Cable Curl": "Cable Curl",
    "EZ-Bar Curl": "Barbell Curl",
    "EZ-Bar Preacher Curl": "Barbell Preacher Curl",
    "EZ-Bar Skull Crusher": "Barbell Lying Triceps Extension",
    "Eccentric Chin-Up": "Machine-assisted Chin-up",
    "Eccentric-Accentuated Chin-Up": "Machine-assisted Chin-up",
    "Eccentric-Accentuated Lying Leg Curl": "Lever Lying Leg Curl",
    "Eccentric-Accentuated Push Press": "Dumbbell Shoulder Press",
    "Eccentric-Neutral Grip Pull-Up": "Neutral Grip Pull-up",
    "Elevated Glute Bridge": "Weighted Single Leg Hip Thrust (leg extended)",
    "Enhanced-Eccentric Barbell Single-Leg Hip Thrust": "Weighted Single Leg Hip Thrust (leg extended)",
    "Extra-Range Side-Lying Hip Abduction": "Weighted Lying Hip Abduction",
    "Extra-Range Side-Lying Hip Raise": "Bent Knee Side Bridge Hip Abduction",
    "Feet Elevated Plank": "Front Plank",
    "Feet Elevated Push-Up": "Decline Push-up",
    "Feet-Elevated Inverted Row": "Inverted Row",
    "Feet-Elevated Push-Up": "Decline Push-up",
    "Flat Dumbbell Fly": "Dumbbell Fly",
    "Flat Dumbbell Flye ": "Dumbbell Fly",
    "Frog Pump": "Weighted Single Leg Hip Thrust (leg extended)",
    "Frog Reverse Hyper": "Reverse Hyper-extension",
    "Front Lat Pulldown": "Cable Pulldown",
    "Front Plank": "Front Plank",
    "Front Squat": "Barbell Front Squat",
    "Gliding Leg Curl": "Leg Curl (on power wheel)",
    "Gliding Leg Curls": "Leg Curl (on power wheel)",
    "Glute Kickback": "Lever Bent-over Glute Kickback",
    "Glute March": "Single Leg Hip Bridge",
    "Glute-Ham Raise": "Glute-Ham Raise",
    "Goblet Deep Squat": "Goblet Squat",
    "Goblet Full Squat": "Goblet Squat",
    "Goblet Parallel Box Squat": "Goblet Squat",
    "Goblet Squat Pulse": "Goblet Squat",
    "Goblet Squat": "Goblet Squat",
    "Good Morning": "Barbell Good-morning",
    "Hack Squat": "Sled Hack Squat",
    "Half-Kneeling Anti-Rotation Press": "Cable Push Pull",
    "Half-Kneeling Cable Anti-Rotation Press": "Cable Push Pull",
    "Hammer Curl": "Cable Hammer Curl",
    "Hammer Preacher Curl": "Hammer Preacher Curl",
    "Hammer Strength Machine Row": "Lever Seated Row",
    "Handle Push-Up": "Push-up",
    "Hanging Knee Raise": "Vertical Leg Raise (on parallel bars)",
    "Hanging Leg Raise": "Hanging Leg Raise",
    "High Bar Squat": "Barbell Full Squat",
    "High-Bar Back Squat": "Barbell Full Squat",
    "High-Cable Cuffed Lateral Raise": "High-Cable Cuffed Lateral Raise",
    "High-Cable Lateral Raise": "Cable One Arm Lateral Raise",
    "High-Pulley Cable Curl": "Bayesian Curl",
    "High-To-Low Face Pull": "Cable Standing Rear Delt Row (with rope)",
    "Hip Abduction": "Cable Hip Abduction",
    "Hollow Body Hold (Core)": "Hollow Body Hold",
    "Hyperextension": "Hyperextension (arms crossed)",
    "Incline Chest-Supported DB Row": "Dumbbell Lying Row",
    "Incline DB Stretch Curl": "Dumbbell Incline Curl",
    "Incline Dumbbell Chest Press": "Dumbbell Incline Bench Press",
    "Incline Dumbbell Flye": "Dumbbell Incline Fly",
    "Incline Medium Grip Bench Press": "Barbell Incline Bench Press",
    "Incline Press": "Barbell Incline Bench Press",
    "Inverted Row": "Inverted Row",
    "Katana Triceps Extension": "Cable One Arm Triceps Extension (pronated grip)",
    "Kettlebell Swing": "Kettlebell Swing",
    "Knee-Banded Abductions": "Lever Seated Hip Abduction",
    "Knee-Banded Bodyweight Glute Bridge": "Single Leg Hip Bridge",
    "Knee-Banded Bodyweight Hip Thrust": "Barbell Hip Thrust",
    "Knee-Banded Constant Tension Barbell Hip Thrust": "Barbell Hip Thrust",
    "Knee-Banded Glute Bridge": "Barbell Hip Thrust",
    "Knee-Banded Glute Bridges": "Single Leg Hip Bridge",
    "Knee-Banded Hip Abduction": "Lever Seated Hip Abduction",
    "Knee-Banded Machine Hip Thrust": "Lever Hip Thrust",
    "Landmine Core Rotation (Not In Exrx.Net Exercise Library)": "Landmine Power Twist (plate loaded)",
    "Landmine": "Landmine Power Twist (plate loaded)",
    "Lat Pull-Down": "Cable Pulldown",
    "Lateral Band Walk": "Lever Seated Hip Abduction",
    "Lateral Raise": "Cable One Arm Lateral Raise",
    "Lean Away Cable Lateral Raise": "Cable One Arm Lateral Raise",
    "Lean Away Dumbbell Lateral Raise": "Dumbbell Front Lateral Raise",
    "Lean-Back Lat Pulldown": "Cable Pulldown",
    "Lean-Back Machine Pulldown": "Lever Pulldown",
    "Lean-In DB Lateral Raise": "Lean-In Dumbbell Lateral Raise",
    "Leg Extension": "Lever Leg Extension",
    "Leg Press Calf Press": "Sled 45° Calf Raise (plate loaded)",
    "Leg Press": "Sled 45° Leg Press",
    "Leg Raise Variation (Abs)": "Vertical Leg-Hip Raise",
    "Long-Lever Plank": "Long-Lever Plank",
    "Low Cable Fly": "Cable Standing Incline Fly",
    "Low-Bar Parallel Box Squat": "Barbell Full Squat",
    "Low-to-High Cable Crossover": "Cable Standing Incline Fly",
    "Lower Back Extension (Pumper)": "Hyperextension (arms crossed)",
    "Lower Back Extension": "Hyperextension (arms crossed)",
    "Lunge Isohold": "Rear Lunge",
    "Lying Leg Curl": "Lever Lying Leg Curl",
    "Lying Leg Raise": "Lying Leg Raise",
    "Machine Chest Press": "Lever Chest Press",
    "Machine Crunch": "Lever Seated Crunch",
    "Machine Glute Kickdown": "Lever Bent-over Glute Kickback",
    "Machine Hip Abduction (Glutes Elevated)": "Lever Seated Hip Abduction",
    "Machine Hip Abduction": "Lever Seated Hip Abduction",
    "Machine Hip Adduction": "Lever Seated Hip Adduction",
    "Machine Incline Press": "Lever Incline Bench Press",
    "Machine Kneeling Leg Curl": "Lever Seated Leg Curl",
    "Machine Lateral Raise": "Lever Lateral Raise",
    "Machine Overhead Triceps Extension": "Lever Overhead Triceps Extension",
    "Machine Preacher Curl": "Lever Preacher Curl",
    "Machine Rear Deltoid Fly": "Lever Pec Deck Fly",
    "Machine Seated Calf Raise": "Lever Seated Calf Raise",
    "Machine Seated Hip Abduction": "Lever Seated Hip Abduction",
    "Machine Seated Leg Curl": "Lever Seated Leg Curl",
    "Machine Seated Row": "Lever Seated Row",
    "Machine Shoulder Press": "Lever Shoulder Press",
    "Machine Shrug": "Lever Shrug",
    "Machine Single-Leg Seated Calf Raise": "Lever Seated Calf Raise (plate loaded)",
    "Machine Standing Calf Raise": "Lever Standing Calf Raise",
    "Machine Wide-Grip Seated Row": "Lever Wide Grip Seated Row (high bar, plate loaded)",
    "Medium Grip Bench Press": "Barbell Bench Press",
    "Mid Cable Fly": "Cable Standing Fly",
    "Military Press": "Barbell Shoulder Press",
    "Modified Candlestick": "Modified Candlestick",
    "Modified Inverted Row": "Inverted Row",
    "Monster Walk": "Lever Seated Hip Abduction",
    "Narrow Base Push-Up": "Close Grip Push-up",
    "Narrow Neutral Grip Pull-Down": "Cable Parallel Grip Pulldown",
    "Narrow Neutral-Grip Pulldown": "Cable Close Grip Pulldown",
    "Negative Chin-Up": "Machine-assisted Chin-up",
    "Neutral-Grip Seated Cable Row": "Cable Seated Row",
    "Neutral Grip Pull-Up": "Weighted Neutral Grip Pull-up",
    "Neutral-Grip Lat Pull-Down": "Cable Close Grip Pulldown",
    "Neutral-Grip Lat Pulldown": "Cable Parallel Grip Pulldown",
    "Neutral-Grip Pull-Up": "Neutral-Grip Pull-Up",
    "Nordic Ham Curl": "Nordic Ham Curl",
    "One Arm Dumbbell Row": "Dumbbell Bent-over Row",
    "One-Arm Dumbbell Row": "Dumbbell Bent-over Row",
    "One-Arm Row": "Dumbbell Bent-over Row",
    "Overhand Pullup ": "Pull-up",
    "Overhead Cable Tricep Extension": "Cable Forward Triceps Extension",
    "Overhead Cable Triceps Extension (Bar)": "Cable Forward Triceps Extension",
    "Overhead Cable Triceps Extension (Rope)": "Cable Triceps Extension (with rope)",
    "Pause Barbell Hip Thrust": "Barbell Hip Thrust",
    "Pause Bench Press": "Barbell Bench Press",
    "Pause Close-Grip Bench Press": "Barbell Bench Press",
    "Pause Dumbbell 45-Degree Hyper": "Dumbbell 45° Hyperextension",
    "Pause Front Squat": "Barbell Full Squat",
    "Pec Deck Fly": "Lever Pec Deck Fly",
    "Pec Deck": "Lever Pec Deck Fly",
    "Pendlay Deficit Row": "Pendlay Row",
    "Pistol Squat": "Single Leg Squat (pistol)",
    "Pre-Exhaustion Nordic Ham Curl/Leg Extension": "Nordic Ham Curl",
    "Prisoner Single-Leg 45 Back Extension": "Single Leg 45° Hyperextension",
    "Prisoner Single-Leg 45-Degree Hyper": "Single Leg 45° Hyperextension",
    "Prisoner Single-Leg Back Extension": "Single Leg 45° Hyperextension",
    "Pronated Pulldown": "Cable Pulldown",
    "Prone Trap Raise": "Dumbbell Incline Y Raise",
    "Pull-Up": "Pull-Up",
    "Push-Up": "Push-up",
    "Reset Knee-Banded Barbell Hip Thrust": "Barbell Hip Thrust",
    "Resistance Band Lateral Raise": "Cable One Arm Lateral Raise",
    "Reverse Cable Flye": "Cable One Arm Reverse Fly",
    "Reverse Crunch": "Lying Leg Raise (on floor)",
    "Reverse Hyperextension": "Reverse Hyper-extension",
    "Reverse Nordic": "Reverse Nordic",
    "Reverse Pec Dec": "Lever Seated Reverse Fly (on pec deck)",
    "Reverse Pec Deck": "Lever Seated Reverse Fly (on pec deck)",
    "Reverse-Grip Lat Pull-Down": "Cable Underhand Pulldown",
    "Ring-Supported Pistol": "Suspended Single Leg Split Squat (self-assisted)",
    "Rkc Plank": "Front Plank",
    "Roman Chair Leg Raise": "Vertical Leg Raise (on parallel bars)",
    "Rope Face Pull": "Cable Standing Rear Delt Row (with rope)",
    "Rope Horizontal Chop": "Medicine Ball Side Twist Throw (against wall)",
    "Russian Kettlebell Swing": "Kettlebell Swing",
    "Russian Twist": "Twisting Sit-up",
    "Seated Cable Facepull": "Cable Standing Rear Delt Row (with rope)",
    "Seated Calf Raise": "Lever Seated Calf Raise",
    "Seated DB Shoulder Press": "Dumbbell Shoulder Press",
    "Seated Dumbbell Overhead Press": "Dumbbell Shoulder Press",
    "Seated Dumbbell Press": "Dumbbell Shoulder Press",
    "Seated Dumbbell Shoulder Press": "Dumbbell Shoulder Press",
    "Seated Face Pull": "Cable Standing Rear Delt Row (with rope)",
    "Seated Hip Abduction Machine": "Lever Seated Hip Abduction",
    "Seated Leg Curl": "Lever Seated Leg Curl",
    "Seated Row": "Lever Seated Row",
    "Seated Super-Bayesian High Cable Curl": "Seated Bayesian Cable Curl",
    "Semi-Sumo Deadlift": "Barbell Sumo Deadlift",
    "Side Bridge": "Side Plank",
    "Side Crunch": "Side Crunch",
    "Side Lying Abduction": "Weighted Lying Hip Abduction",
    "Side Lying Clam": "Lever Seated Hip Abduction",
    "Side Lying Hip Raise": "Lever Seated Hip Abduction",
    "Side Plank From Knees": "Side Plank",
    "Side Plank": "Side Plank",
    "Single Leg Hip Thrust": "Weighted Single Leg Hip Thrust (leg extended)",
    "Single-Arm Cable Curl": "Bayesian Curl",
    "Single-Arm DB Row": "Dumbbell Bent-over Row",
    "Single-Arm Dumbbell Bench Press": "Dumbbell Bench Press",
    "Single-Arm Dumbbell Military Press": "Dumbbell Shoulder Press",
    "Single-Arm Pull-Down": "Cable One Arm Pulldown",
    "Single-Arm Pulldown": "Cable One Arm Pulldown",
    "Single-Leg 45-Degree Hyper Extension": "Single Leg 45° Hyperextensio",
    "Single-Leg Extension": "Lever Single Leg Leg Extension",
    "Single-Leg Foot-Elevated Hip Thrust": "Weighted Single Leg Hip Thrust (leg extended)",
    "Single-Leg Hip Thrust": "Weighted Single Leg Hip Thrust (leg extended)",
    "Sissy Squat": "Sissy Squat",
    "Skater Squat": "Single Leg Squat (with leg back)",
    "Skull Crusher": "Barbell Lying Triceps Extension 'Skull Crusher'",
    "Sled Push": "Weighted Drive Sled Sprint",
    "Smith Machine Hip Thrust": "Smith Machine Hip Thrust",
    "Smith Machine Row": "Smith Bent-over Row",
    "Smith Machine Squat": "Smith Squat",
    "Smith Machine Static Lunge w/ Elevated Front Foot": "Smith Rear Lunge",
    "Smith Machine Static Lunge": "Smith Rear Lunge",
    "Snatch-Grip RDL": "Romanian Deadlift",
    "Spread-Eagle Reverse Hyper": "Reverse Hyper-extension",
    "Stability Ball Leg Curl": "Straight Hip Leg Curl (on stability ball)",
    "Stability Ball Side Crunch": "Side Crunch (on stability ball)",
    "Standing Cable Hip Abduction": "Cable Hip Abduction",
    "Standing Calf Raise": "Lever Standing Calf Raise",
    "Standing Dumbbell Press": "Dumbbell Shoulder Press",
    "Standing Glute Squeeze": "Single Leg Hip Bridge",
    "Standing Single-Arm Cable Row": "Cable Standing Low Row",
    "Standing Single-Arm Dumbbell Overhead Press": "Dumbbell Shoulder Press",
    "Stiff Leg Deadlift": "Barbell Straight-back Straight-leg Deadlift",
    "Stiff Legged Deadlift": "Barbell Straight-back Straight-leg Deadlift",
    "Stiff-Leg Deadlift": "Barbell Straight-back Straight-leg Deadlift",
    "Straight-Leg Sit-Up": "V-up",
    "Sumo Deadlift": "Barbell Sumo Deadlift",
    "Supinated Pulldown": "Cable Pulldown",
    "Supine Abduction Ladder": "Lever Seated Hip Abduction",
    "Swiss Ball Crunch": "Ball Crunch (on stability ball)",
    "Swiss Ball Leg Curl": "Straight Hip Leg Curl (on stability ball)",
    "Swiss Ball Rollout": "Stability Ball Rollout",
    "Swiss Ball Side Crunch": "Side Crunch (on stability ball)",
    "Swiss Ball Triple Threat": "Straight Hip Leg Curl (on stability ball)",
    "T-Bar Row": "Lever T-bar Row (plate loaded)",
    "Toe Press": "Lever Seated Calf Press",
    "Trap Bar Deadlift": "Barbell Deadlift",
    "Triceps Dip": "Triceps Dip",
    "Triceps Pressdown (Bar)": "Cable Forward Triceps Extension",
    "Triceps Pressdown (Rope)": "Cable Triceps Extension (with rope)",
    "Triple-Banded Hip Thrust": "Barbell Hip Thrust",
    "Turkish Get Up": "Dumbbell Turkish Get-up",
    "Underhand Grip Lat Pull-Down": "Cable Underhand Pulldown",
    "V-Up": "V-up",
    "Walking Lunge": "Dumbbell Walking Lunge",
    "Weighted Parallel Pull-Up": "Weighted Neutral Grip Pull-up",
    "Weighted-Eccentric Chin-Up": "Weighted Chin-up",
    "Wide Grip Lat Pulldown": "Cable Pulldown",
    "Wide-Grip Lat Pull-Down": "Cable Pulldown",
    "Wide-Grip Lat Pulldown": "Cable Pulldown",
    "Wide-Grip Pull-Up": "Pull-Up",
    "X-Band Walk (Heavy Tension)": "Lever Seated Hip Abduction",
    "X-Band Walk (Light Tension)": "Lever Seated Hip Abduction",
    "X-Band Walk (Moderate Tension)": "Lever Seated Hip Abduction",
    "X-Band Walk": "Lever Bent-over Glute Kickback",
    "45 Degree Hyperextension": "45° Hyperextension",
    "Alternating Dumbbell Curl": "Dumbbell Curl",
    "Assisted Dip": "Machine-assisted Dip",
    "Assisted Pull Up": "Machine-assisted Chin-up",
    "B Stance Hack Squat": "Single Leg Squat (with leg back)",
    "B Stance Hip Thrust": "Single Leg Hip Bridge",
    "B Stance RDL": "Single Leg Stiff-leg Deadlift",
    "B-Stance Dumbbell RDL": "Single Leg Stiff-leg Deadlift",
    "B-Stance Hip Thrust": "Single Leg Hip Bridge",
    "Barbell Bent Row": "Barbell Bent-over Row",
    "Bodyweight Skullcrusher": "Barbell Lying Triceps Extension 'Skull Crusher'",
    "Cable Abduction": "Lever Seated Hip Abduction",
    "Cable Archer Curl": "Cable Concentration Curl",
    "Cable Biceps Curl - Facing In": "Cable Hammer Curl",
    "Cable Biceps Curl - Facing Out": "Cable Concentration Curl",
    "Cable Crossover Triceps Extension": "Cable One Arm Pushdown",
    "Cable French Press": "Cable Triceps Extension",
    "Cable Lateral Raise - Single Arm": "Cable One Arm Lateral Raise",
    "Cable Paw Back": "Smith Good-morning",
    "Cable Rear Delt Fly": "Cable One Arm Reverse Fly",
    "Cable Step Up": "Cable Step-up",
    "Cable Y Raise": "Cable Y Raise",
    "Chest Supported Lateral Raise": "Lever Lateral Raise",
    "Chest Supported Machine Row": "Lever Seated Row",
    "Chest Supported Row": "Lever Seated Row",
    "Chin Up Eccentrics": "Machine-assisted Chin-up",
    "Close Grip Pulldown": "Cable Pulldown",
    "Close Grip Pushups": "Close Grip Push-up",
    "Copenhagen Plank": "Front Plank",
    "Cossack Squat": "Deficit Curtsy Lunge",
    "DB Bent Over Row": "Dumbbell Bent-over Row",
    "DB Y Raise": "Cable Y Raise",
    "Decline Sit-ups": "Incline Sit-up",
    "Drop Lunge": "Dumbbell Deficit Single Leg Split Squat",
    "Dumbbell Flat Bench Press": "Dumbbell Bench Press",
    "Dumbbell Rear Delt Fly": "Lever Seated Reverse Fly (on pec deck)",
    "Dumbbell Sumo Squat": "Smith Wide Squat",
    "EZ Bar Bicep Curl": "Barbell Curl",
    "Flat Dumbbell Press": "Dumbbell Bench Press",
    "Front Foot Elevated Split Squat": "Dumbbell Deficit Single Leg Split Squat",
    "Front Raise (Seated)": "Cable Seated Front Raise",
    "Glute Abduction": "Lever Seated Hip Abduction",
    "Glute Bridge": "Barbell Hip Thrust",
    "Glute Focused Back Extension": "Lever Back Extension",
    "Glute Leg Press": "Sled 45º Leg Press",
    "Glute Lunge": "Rear Lunge",
    "Glute Max Kickback": "Lever Bent-over Glute Kickback",
    "Glute Med Kickback": "Lever Bent-over Glute Kickback",
    "Glute Medius Kickback": "Lever Bent-over Glute Kickback",
    "Glute-biased Stance Lunge": "Rear Lunge",
    "Goblet Squat - Heels Elevated": "Goblet Squat",
    "Hamstring Bridge": "Barbell Hip Thrust",
    "Hanging Leg Raises": "Hanging Leg Raise",
    "Heels Elevated Goblet Squat": "Goblet Squat",
    "High Incline DB Press": "Dumbbell Incline Bench Press",
    "High Incline Shoulder Press": "Dumbbell Incline Shoulder Press",
    "Hip Thrust": "Barbell Hip Thrust",
    "Incline Bench Cable Lateral Raise": "Cable Lateral Raise",
    "KAS Glute Bridge": "Barbell Hip Thrust",
    "Katana Extension": "Cable One Arm Triceps Extension (pronated grip)",
    "Landmine Row": "Lever T-bar Row (plate loaded)",
    "Lat Biased Cable Row": "Cable Standing Row",
    "Lat Pulldown": "Cable Pulldown",
    "Lat Pullover": "Cable Pullover",
    "Lateral Raise (Seated)": "Dumbbell Seated Lateral Raise",
    "Lateral Raise Machine": "Lever Lateral Raise",
    "Leaning Leg Extension": "Lever Leg Extension",
    "Leg Extensions": "Lever Leg Extension",
    "Leg Press - Feet Wide": "Sled 45º Leg Press",
    "Leg Press - Glute Focus": "Sled 45º Leg Press",
    "Leg Press (Glute Biased)": "Sled 45º Leg Press",
    "Low Incline DB Press": "Dumbbell Incline Chest Press",
    "Low Row": "Lever Seated Low Row (plate loaded)",
    "Lying Leg Curl - Single Leg": "Lever Single Leg Seated Leg Curl",
    "Machine High Row": "Lever Seated High Row",
    "Machine Pec Fly": "Lever Pec Deck Fly",
    "Machine Row - Upper Back": "Lever Seated High Row",
    "Navy Row": "Dumbbell Lying Row",
    "Nordic Drop": "Nordic Ham Curl",
    "Partial Nordic Drop": "Nordic Ham Curl",
    "Preacher Curl Machine": "Lever Preacher Curl",
    "Pull Up": "Machine-assisted Chin-up",
    "Pull Ups": "Machine-assisted Chin-up",
    "Rack Chin": "Machine-assisted Chin-up",
    "Rear Delt Cable Fly": "Cable One Arm Reverse Fly",
    "Rear Delt Fly": "Lever Seated Reverse Fly (on pec deck)",
    "Rear Delt Fly Machine": "Lever Seated Reverse Fly (on pec deck)",
    "Rear Delt Machine Fly": "Lever Seated Reverse Fly (on pec deck)",
    "Rear Delt Row": "Lever Seated Rear Delt Row",
    "Reverse lunge": "Rear Lunge",
    "Reverse Nordic Drop": "Nordic Ham Curl",
    "Romanian Deadlift": "Barbell Straight-back Straight-leg Deadlift",
    "Seated Abduction (leaning forward)": "Lever Seated Hip Abduction",
    "Seated Adduction": "Lever Seated Hip Adduction",
    "Seated Cable Row": "Cable Seated Row",
    "Seated Hamstring Curl": "Lever Seated Leg Curl",
    "Seated Hip Abduction": "Lever Seated Hip Abduction",
    "Seated Hip Adduction": "Lever Seated Hip Adduction",
    "Seated Lat Pullover": "Cable Seated Pullover",
    "Single Arm Cable Y Raise": "Cable Y Raise",
    "Single Arm Dumbbell Row": "Dumbbell Bent-over Row",
    "Single Arm High Row": "Cable One Arm Seated High Row",
    "Single Arm Lat Pulldown": "Cable One Arm Pulldown",
    "Single Arm Low Row": "Cable Standing Low Row",
    "Single Arm Triceps Extension - Long": "Cable One Arm Triceps Extension (pronated grip)",
    "Single Leg Press": "Lever Single Leg Seated Leg Press (plate loaded)",
    "Single Leg RDL": "Single Leg Stiff-leg Deadlift",
    "Single-arm Seated Row": "Cable One Arm Seated Row",
    "Single-leg Dumbbell Hip Thrust": "Single Leg Hip Bridge",
    "Smith Machine Bulgarian Split Squat": "Dumbbell Deficit Single Leg Split Squat",
    "Smith Machine Deficit Split Squat": "Dumbbell Deficit Single Leg Split Squat",
    "Smith Machine Glute Bridge": "Smith Machine Hip Thrust",
    "Smith Machine Incline Press": "Smith Incline Bench Press",
    "Smith Machine Split Squat": "Dumbbell Deficit Single Leg Split Squat",
    "Smith Machine Step-up": "Smith Step Down",
    "Smith Machine Upright Row": "Smith Upright Row",
    "Spider Curl": "Dumbbell Incline Curl",
    "Squat Variation (Your Choice)": "Barbell Full Squat",
    "Squat Variation (Your choice)": "Barbell Full Squat",
    "Step Up": "Dumbbell Step-up",
    "Stiff Arm Lat Pullover": "Cable Pullover",
    "Trap Bar Romanian Deadlift": "Barbell Straight-back Straight-leg Deadlift",
    "TRX Rear Delt Fly": "Lever Seated Reverse Fly (on pec deck)",
    "Upper Back Pulldown": "Cable Pulldown",
    "Waist Banded Romanian Deadlift": "Barbell Straight-back Straight-leg Deadlift",
    "Zercher Squat": "Barbell Zercher Squat"
  }

  print("--- Starting PKL Generation from CSV ---")
  # if exercise_replacement_map:
    # print("\nApplying Exercise Replacements:")
    # for original, new in exercise_replacement_map.items():
      # print(f'  - Replacing "{original}" with "{new}"')

  # Generate the program data structure from the CSV
  program_data = parse_advanced_template_csv(csv_file_path, exercise_replacement_map)

  # --- PKL Class Definitions for Output File ---
  # This string contains the necessary class definitions for the PKL file to be valid.
  class_definitions_pkl_str = """\
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

  # Combine header and the generated program data into the final string
  full_pkl_output = f"{class_definitions_pkl_str}\n// --- Program Instance ---\n{program_data.to_pkl_string()}\n"

  # Write the final string to the output file
  try:
    with open(output_filename, "w", encoding='utf-8') as f:
      f.write(full_pkl_output)
    print(f'\n✅ Successfully generated PKL file: "{output_filename}"')
  except Exception as e:
    print(f"\n❌ Error writing file: {e}")

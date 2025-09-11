import csv
import datetime
import re
from io import StringIO


# --- PKL Class Definitions (Copied from previous response) ---
class PKLBase:
  def to_pkl_string(self, indent_level=0, is_listing_item=False):
    raise NotImplementedError

  def _format_value(self, value, indent_level, is_listing_item=False):
    indent = "  " * indent_level
    if isinstance(value, PKLBase):
      return value.to_pkl_string(indent_level, is_listing_item)
    elif isinstance(value, str):
      if '\n' in value:
        lines = value.strip().split('\n')
        if len(lines) == 1 and not is_listing_item:  # Single line string not in a list, basic quotes
          return f'"{lines[0]}"'

        formatted_lines = '"""\n'
        for line_idx, line in enumerate(lines):
          # Indent content of multiline string further than the """ itself
          formatted_lines += f'{indent}{"  " * (indent_level + 1)}{line}'
          if line_idx < len(lines) - 1:
            formatted_lines += '\n'
        formatted_lines += f'\n{indent}{"  " * indent_level}"""'
        return formatted_lines
      return f'"{value}"'
    elif isinstance(value, bool):
      return str(value).lower()
    elif isinstance(value, (int, float)):
      return str(value)
    elif isinstance(value, list) or (hasattr(value, '__class__') and value.__class__.__name__ == 'Listing'):
      if not value:  # Empty list
        item_type_str = ""
        if hasattr(value, 'item_type') and value.item_type:
          item_type_str = f"<{value.item_type}>"
        return f"new Listing{item_type_str} {{}}"

      item_type_str = ""
      if hasattr(value, 'item_type') and value.item_type:
        item_type_str = f"<{value.item_type}>"

      items_strs = []
      for item in value:
        items_strs.append(self._format_value(item, indent_level + 1, True))  # Pass True for is_listing_item

      if not items_strs:  # Should be caught by the `if not value:` above
        return f"new Listing{item_type_str} {{}}"

      # Join items, ensuring proper indentation for each
      joined_items = f"\n{indent}    ".join(items_strs)
      return f"new Listing{item_type_str} {{\n{indent}    {joined_items}\n{indent}  }}"
    elif value is None:
      return "null"
    else:
      return str(value)

  def _format_attr(self, attr_name, attr_value, indent_level):
    indent = "  " * (indent_level + 1)  # Attributes are indented one level more than the object itself
    if attr_value is None and not (isinstance(attr_value, list) and hasattr(self,
                                                                            'optional_with_defaults') and attr_name in self.optional_with_defaults and
                                   self.optional_with_defaults[attr_name] is None):
      if hasattr(self, 'optional_with_defaults') and attr_name in self.optional_with_defaults:
        # For optional fields that are explicitly set to null or empty list
        if isinstance(self.optional_with_defaults[attr_name], list) and not attr_value:  # empty list
          formatted_value = self._format_value(Listing(
            self.optional_with_defaults[attr_name].item_type if hasattr(
              self.optional_with_defaults[attr_name], "item_type") else None), indent_level + 1)
          return f"{indent}{attr_name} = {formatted_value}"
        elif self.optional_with_defaults[attr_name] is None and attr_value is None:  # null
          formatted_value = self._format_value(None, indent_level + 1)
          return f"{indent}{attr_name} = {formatted_value}"
      return ""  # Skip other None attributes

    formatted_value = self._format_value(attr_value, indent_level + 1)
    return f"{indent}{attr_name} = {formatted_value}"


class Listing(list):
  def __init__(self, item_type_name=None, *args):  # item_type_name is a string
    super().__init__(*args)
    self.item_type = item_type_name


class Program(PKLBase):
  def __init__(self, name="", arthur="", shortDescription="", description="", programLength="", uri="", level="",
               programEquipment="", daysPerWeek="", mesocycles=None):
    self.name = name
    self.arthur = arthur
    self.shortDescription = shortDescription
    self.description = description
    self.programLength = programLength
    self.uri = uri
    self.level = level
    self.programEquipment = programEquipment
    self.daysPerWeek = daysPerWeek
    self.mesocycles = mesocycles if mesocycles is not None else Listing("Mesocycle")
    self.optional_with_defaults = {}

  def to_pkl_string(self, indent_level=0, is_listing_item=False):
    base_indent_str = "  " * indent_level
    obj_name = "program" if indent_level == 0 else ""  # Only for the root object
    assignment_operator = ": Program =" if indent_level == 0 else "="

    attrs = [
      self._format_attr("name", self.name, indent_level),
      self._format_attr("arthur", self.arthur, indent_level),
      self._format_attr("shortDescription", self.shortDescription, indent_level),
      self._format_attr("description", self.description, indent_level),
      self._format_attr("programLength", self.programLength, indent_level),
      self._format_attr("uri", self.uri, indent_level),
      self._format_attr("level", self.level, indent_level),
      self._format_attr("programEquipment", self.programEquipment, indent_level),
      self._format_attr("daysPerWeek", self.daysPerWeek, indent_level),
      self._format_attr("mesocycles", self.mesocycles, indent_level)
    ]
    valid_attrs = [attr for attr in attrs if attr]

    if is_listing_item or indent_level > 0:  # If it's a nested new Program instance
      return f"new Program {{\n" + "\n".join(
        valid_attrs) + f"\n{base_indent_str}  }}"  # one less indent for closing brace
    return f"{obj_name}{assignment_operator} new Program {{\n" + "\n".join(valid_attrs) + f"\n{base_indent_str}}}"


class Mesocycle(PKLBase):
  def __init__(self, name="", description="", order=0, microcycles=None):
    self.name = name
    self.description = description
    self.order = order
    self.microcycles = microcycles if microcycles is not None else Listing("Microcycle")
    self.optional_with_defaults = {}

  def to_pkl_string(self, indent_level=0, is_listing_item=False):
    base_indent_str = "  " * indent_level
    attrs = [
      self._format_attr("name", self.name, indent_level),
      self._format_attr("description", self.description, indent_level),
      self._format_attr("order", self.order, indent_level),
      self._format_attr("microcycles", self.microcycles, indent_level)
    ]
    valid_attrs = [attr for attr in attrs if attr]
    return f"new Mesocycle {{\n" + "\n".join(valid_attrs) + f"\n{base_indent_str}  }}"


class Microcycle(PKLBase):
  def __init__(self, name="", description="", order=0, advancedWorkouts=None):
    self.name = name
    self.description = description
    self.order = order
    self.advancedWorkouts = advancedWorkouts if advancedWorkouts is not None else Listing("AdvancedWorkout")
    self.optional_with_defaults = {}

  def to_pkl_string(self, indent_level=0, is_listing_item=False):
    base_indent_str = "  " * indent_level
    attrs = [
      self._format_attr("name", self.name, indent_level),
      self._format_attr("description", self.description, indent_level),
      self._format_attr("order", self.order, indent_level),
      self._format_attr("advancedWorkouts", self.advancedWorkouts, indent_level)
    ]
    valid_attrs = [attr for attr in attrs if attr]
    return f"new Microcycle {{\n" + "\n".join(valid_attrs) + f"\n{base_indent_str}  }}"


class AdvancedWorkout(PKLBase):
  def __init__(self, name="", day=0, notes=None, advancedExercisesSets=None):
    self.name = name
    self.day = day
    self.notes = notes if notes is not None else Listing("String")
    self.advancedExercisesSets = advancedExercisesSets if advancedExercisesSets is not None else Listing(
      "AdvancedExerciseSets")
    self.optional_with_defaults = {}

  def to_pkl_string(self, indent_level=0, is_listing_item=False):
    base_indent_str = "  " * indent_level
    attrs = [
      self._format_attr("name", self.name, indent_level),
      self._format_attr("day", self.day, indent_level),
      self._format_attr("notes", self.notes, indent_level),
      self._format_attr("advancedExercisesSets", self.advancedExercisesSets, indent_level)
    ]
    valid_attrs = [attr for attr in attrs if attr]
    return f"new AdvancedWorkout {{\n" + "\n".join(valid_attrs) + f"\n{base_indent_str}  }}"


class AdvancedExerciseSets(PKLBase):
  def __init__(self, name="", description="", notes=None, sets=0, minRepetitions=None, maxRepetitions=None,
               targetRatePerceivedEffort=None, setType="",
               repetitions=None, targetRepetitionsInReserve=None, targetWeightPounds=None, targetWeightKilograms=None,
               weightIncrementPounds=None, weightIncrementKilograms=None, percentage1RM=None,
               progressionSchemeID=None, setScheme=None):
    self.name = name
    self.description = description  # New field
    self.notes = notes if notes is not None else Listing("String")
    self.sets = sets
    self.setType = setType
    self.repetitions = repetitions  # Listing<Int>?
    self.targetRepetitionsInReserve = targetRepetitionsInReserve  # Listing<Int>?
    self.targetRatePerceivedEffort = targetRatePerceivedEffort  # Listing<Int>?
    self.targetWeightPounds = targetWeightPounds  # Listing<Float>?
    self.targetWeightKilograms = targetWeightKilograms  # Listing<Float>?
    self.weightIncrementPounds = weightIncrementPounds  # Float?
    self.weightIncrementKilograms = weightIncrementKilograms  # Float?
    self.percentage1RM = percentage1RM  # Listing<Float>?
    self.progressionSchemeID = progressionSchemeID  # String?
    self.minRepetitions = minRepetitions  # Int?
    self.maxRepetitions = maxRepetitions  # Int?
    self.setScheme = setScheme if setScheme is not None else Listing("SetScheme")  # Listing<SetScheme>?
    self.optional_with_defaults = {
      "setType": "", "repetitions": None, "targetRepetitionsInReserve": None,
      "targetRatePerceivedEffort": None, "targetWeightPounds": None, "targetWeightKilograms": None,
      "weightIncrementPounds": None, "weightIncrementKilograms": None, "percentage1RM": None,
      "progressionSchemeID": None, "minRepetitions": None, "maxRepetitions": None, "setScheme": None
    }

  def to_pkl_string(self, indent_level=0, is_listing_item=False):
    base_indent_str = "  " * indent_level
    attrs = []
    attrs.append(self._format_attr("name", self.name, indent_level))
    attrs.append(self._format_attr("description", self.description, indent_level))
    attrs.append(self._format_attr("notes", self.notes, indent_level))
    attrs.append(self._format_attr("sets", self.sets, indent_level))

    for attr_name, default_value in self.optional_with_defaults.items():
      attr_value = getattr(self, attr_name)
      if attr_name == "setType" and attr_value == "":  # Skip default empty string for setType
        continue
      if attr_value is not None:
        # For lists, ensure they are not empty before adding. If default is None but current is [], it's like explicit empty.
        if isinstance(attr_value,
                      list) and not attr_value and default_value is None:  # if it's an empty list but wasn't defaulted to empty
          attrs.append(self._format_attr(attr_name, Listing(
            attr_value.item_type if hasattr(attr_value, "item_type") else None), indent_level))
        elif attr_value != default_value:  # Only add if different from default or explicitly set
          attrs.append(self._format_attr(attr_name, attr_value, indent_level))
        elif default_value is None and attr_value is None:  # Explicitly null for an optional field
          attrs.append(self._format_attr(attr_name, None, indent_level))

    valid_attrs = [attr for attr in attrs if attr]
    return f"new AdvancedExerciseSets {{\n" + "\n".join(valid_attrs) + f"\n{base_indent_str}  }}"


class SetScheme(PKLBase):  # Not used by Nippard's program directly but defined in template
  def __init__(self, sets=0, repetitions=None, targetWeightPounds=None, targetWeightKilograms=None,
               weightIncrementPounds=None, weightIncrementKilograms=None,
               targetRepetitionsInReserve=None, targetRatePerceivedEffort=None,
               percentage1RM=None, progressionSchemeID=None, minRepetitions=None, maxRepetitions=None, setType=""):
    self.sets = sets
    self.setType = setType
    self.repetitions = repetitions if repetitions is not None else Listing("Int")
    self.targetWeightPounds = targetWeightPounds
    self.targetWeightKilograms = targetWeightKilograms
    self.weightIncrementPounds = weightIncrementPounds
    self.weightIncrementKilograms = weightIncrementKilograms
    self.targetRepetitionsInReserve = targetRepetitionsInReserve
    self.targetRatePerceivedEffort = targetRatePerceivedEffort
    self.percentage1RM = percentage1RM
    self.progressionSchemeID = progressionSchemeID
    self.minRepetitions = minRepetitions
    self.maxRepetitions = maxRepetitions
    self.optional_with_defaults = {
      "setType": "", "targetWeightPounds": None, "targetWeightKilograms": None,
      "weightIncrementPounds": None, "weightIncrementKilograms": None,
      "targetRepetitionsInReserve": None, "targetRatePerceivedEffort": None,
      "percentage1RM": None, "progressionSchemeID": None,
      "minRepetitions": None, "maxRepetitions": None
    }

  def to_pkl_string(self, indent_level=0, is_listing_item=False):
    base_indent_str = "  " * indent_level
    attrs = [
      self._format_attr("sets", self.sets, indent_level),
      self._format_attr("repetitions", self.repetitions, indent_level)
    ]
    for attr_name, default_value in self.optional_with_defaults.items():
      attr_value = getattr(self, attr_name)
      if attr_name == "setType" and attr_value == "": continue
      if attr_value != default_value:
        attrs.append(self._format_attr(attr_name, attr_value, indent_level))
    valid_attrs = [attr for attr in attrs if attr]
    return f"new SetScheme {{\n" + "\n".join(valid_attrs) + f"\n{base_indent_str}  }}"


# --- Pre-defined Warm-Up SetScheme Objects ---
warmUpScheme1Set = SetScheme(
  sets=1,
  repetitions=Listing("Int", [10]),
  percentage1RM=Listing("Float", [0.60]),
  minRepetitions=6,
  maxRepetitions=10,
  # notes="Use ~60% of your planned working weight for ~6-10 reps (or until you feel warm and loose)"
)

warmUpScheme2Sets = SetScheme(
  sets=2,
  repetitions=Listing("Int", [10, 6]),
  percentage1RM=Listing("Float", [0.50, 0.70]),
  minRepetitions=6,
  maxRepetitions=10,
  # notes="Perform a mini warm-up pyramid:\nWarm-Up Set #1 = ~50% of planned working weight for ~6-10 reps\nWarm-Up Set #2 = ~70% of planned working weight for 4-6 reps"
)

warmUpScheme3Sets = SetScheme(
  sets=3,
  repetitions=Listing("Int", [10, 6, 4]),
  percentage1RM=Listing("Float", [0.45, 0.65, 0.85]),
  minRepetitions=6,
  maxRepetitions=10,
  # notes="Perform a full warm-up pyramid:\nWarm-Up Set #1 = ~45% of planned working weight for ~6-10 reps\nWarm-Up Set #2 = ~65% of planned working weight for 4-6 reps\nWarm-Up Set #3 = ~85% of planned working weight for 3-4 reps"
)

warmUpScheme4Sets = SetScheme(
  sets=4,
  repetitions=Listing("Int", [10, 6, 5, 4]),
  percentage1RM=Listing("Float", [0.45, 0.60, 0.75, 0.85]),
  minRepetitions=6,
  maxRepetitions=10,
  # notes="Perform a full warm-up pyramid:\nWarm-Up Set #1 = ~45% of planned working weight for ~6-10 reps\nWarm-Up Set #2 = ~60% of planned working weight for 4-6 reps\nWarm-Up Set #3 = ~75% of planned working weight for 3-5 reps\nWarm-Up Set #4 = ~85% of planned working weight for 2-4 reps"
)

WARMUP_SCHEME_MAP = {
  1: "warmUpScheme1Set",
  2: "warmUpScheme2Sets",
  3: "warmUpScheme3Sets",
  4: "warmUpScheme4Sets"
}


# <editor-fold desc="Helper Functions">

# --- Helper Functions ---
def strip_na_and_tilde(value):
  if isinstance(value, str):
    val = value.strip().replace("~", "")
    if val.lower() == "n/a" or val == "":
      return None
    return val
  return value


# def parse_warmup_sets(ws_str):
#     ws_str = strip_na_and_tilde(ws_str)
#     if not ws_str: return "N/A"  # Or some default if you prefer
#     # The CSV uses "02/03/2025" for "2-3". We need to robustly parse this.
#     # If it looks like a date M/D/YYYY, try to get M and D.
#     # If it's like "1-2" or "1", parse directly.
#     if re.match(r"^\d{1,2}/\d{1,2}/\d{4}$", ws_str):  # Looks like a date M/D/YYYY
#         parts = ws_str.split('/')
#         try:
#             # Assuming the first two parts are the range
#             p1 = int(parts[0])
#             p2 = int(parts[1])
#             if p1 == p2: return str(p1)
#             return f"{min(p1, p2)}-{max(p1, p2)}"  # e.g. 2/3/2025 becomes 2-3
#         except:
#             return ws_str  # fallback
#     return ws_str  # For "1", "1-2", "2-3", etc.

def get_warmup_set_count(ws_str):
  """Parses warm-up set string and returns the max number of sets."""
  ws_str = strip_na_and_tilde(ws_str)
  if not ws_str: return 0

  if re.match(r"^\d{1,2}/\d{1,2}/\d{4}$", ws_str):
    parts = ws_str.split('/')
    try:
      return max(int(parts[0]), int(parts[1]))
    except:
      return 0

  if '-' in ws_str:
    try:
      return int(ws_str.split('-')[1])  # Take the higher end of the range
    except:
      return 0

  try:
    return int(ws_str)
  except:
    return 0


def parse_rep_range_from_csv(rep_str_csv):
  rep_str = strip_na_and_tilde(rep_str_csv)
  if not rep_str:
    return None, None

  # Check for date-like format "MM/DD/YYYY" or "M/D/YYYY"
  # Or "MM-DD" from some OCR (e.g. "6-8")
  date_match = re.match(r"(\d{1,2})/(\d{1,2})(?:/\d{2,4})?", rep_str)
  if date_match:
    try:
      p1 = int(date_match.group(1))
      p2 = int(date_match.group(2))
      # If it was something like 06/08/2025 for 6-8 reps
      # Or 10/12/2025 for 10-12 reps
      return min(p1, p2), max(p1, p2)
    except ValueError:
      pass  # Fall through if conversion fails

  # Check for hyphenated range "X-Y"
  range_match = re.match(r"(\d{1,2})-(\d{1,2})", rep_str)
  if range_match:
    try:
      return int(range_match.group(1)), int(range_match.group(2))
    except ValueError:
      pass

  # Check for single number
  single_match = re.match(r"(\d+)", rep_str)
  if single_match:
    try:
      val = int(single_match.group(1))
      return val, val
    except ValueError:
      pass

  # If it's something like "15-20" (already a string), try to split
  if '-' in rep_str:
    parts = rep_str.split('-')
    if len(parts) == 2:
      try:
        return int(parts[0]), int(parts[1])
      except ValueError:
        return None, None

  print(f"Warning: Could not parse rep range from: '{rep_str_csv}' -> '{rep_str}'")
  return None, None


def parse_rpe_value(rpe_str_val):
  cleaned_val = strip_na_and_tilde(rpe_str_val)
  if cleaned_val is None:
    return None

  if '-' in cleaned_val:
    try:
      low, high = map(int, cleaned_val.split('-'))
      return high  # Per instruction, take higher for early, or use as is for last
    except ValueError:
      return None
  try:
    return int(cleaned_val)
  except ValueError:
    return None


def determine_rpe_list_from_csv(week_num_overall, num_working_sets, early_set_rpe_csv, last_set_rpe_csv,
                                intensity_technique_csv):
  # Program notes:
  # Week 1: Last Set RPE ~6-7. Early N/A. 1 working set.
  # Week 2: Last Set RPE ~7-8. Early N/A. 1 working set.
  # Weeks 3-5: Early Set ~7, Last Set ~7-8. 2 working sets.
  # Week 6 (Ramping): Last Set ~6-7. Early N/A. 1 working set.
  # Weeks 7-12 (Ramping): Early ~7-8 or ~8-9 (if failure). Last ~7-8 or 10 (if failure). Variable sets (2 or 3).

  rpe_list = []
  early_rpe = parse_rpe_value(early_set_rpe_csv)  # For multi-set scenarios, take higher if range
  last_rpe = parse_rpe_value(last_set_rpe_csv)
  is_failure = strip_na_and_tilde(intensity_technique_csv) and "failure" in intensity_technique_csv.lower()

  if num_working_sets == 0:  # Should not happen for valid exercises
    return []

  if num_working_sets == 1:
    # Weeks 1, 2, 6
    if last_rpe is not None:
      rpe_list.append(last_rpe)
    else:  # Fallback if last_rpe is missing for a single set
      rpe_list.append(early_set_rpe_csv)  # Default RPE
  elif num_working_sets > 1:
    # Weeks 3-5 (Foundation, 2 sets)
    # Weeks 7-12 (Ramping, 2 or 3 sets)

    # Determine early set RPE value
    current_early_rpe_val = last_rpe  # Default for early sets
    if early_rpe is not None:
      current_early_rpe_val = early_rpe
    elif week_num_overall >= 7 and is_failure:  # Ramping with failure often has higher early RPE
      current_early_rpe_val = 9  # Typically ~8-9
    elif week_num_overall >= 7:  # Ramping without failure
      current_early_rpe_val = 8  # Typically ~7-8

    for i in range(num_working_sets):
      if i < num_working_sets - 1:  # Early sets
        rpe_list.append(current_early_rpe_val)
      else:  # Last set
        if is_failure:
          rpe_list.append(10)
        elif last_rpe is not None:
          rpe_list.append(last_rpe)
        else:  # Fallback for last set if not failure and no explicit RPE
          rpe_list.append(
            current_early_rpe_val + 1 if current_early_rpe_val < 9 else current_early_rpe_val)  # Push a bit more

  # Ensure list length matches num_working_sets, padding if necessary
  while len(rpe_list) < num_working_sets and rpe_list:
    rpe_list.append(rpe_list[-1])
  if not rpe_list and num_working_sets > 0:
    rpe_list = [7] * num_working_sets  # Absolute fallback

  return rpe_list


def create_html_description(main_notes, rest, warmup_str, intensity, sub1, sub2):
  """Assembles all note-like fields into a single HTML string."""
  html_parts = []

  if main_notes:
    html_parts.append(f"<p><strong>Execution Notes:</strong></p><p>{main_notes}</p>")

  protocol_items = []
  if rest: protocol_items.append(f"<li><strong>Rest:</strong> {rest}</li>")
  if warmup_str and warmup_str != "N/A": protocol_items.append(
    f"<li><strong>Warm-up Sets:</strong> {warmup_str}</li>")
  if intensity: protocol_items.append(f"<li><strong>Last-Set Intensity Technique:</strong> {intensity}</li>")

  if protocol_items:
    html_parts.append("<p><strong>Protocol Details:</strong></p><ul>" + "".join(protocol_items) + "</ul>")

  sub_items = []
  if sub1: sub_items.append(f"<li>{sub1}</li>")
  if sub2: sub_items.append(f"<li>{sub2}</li>")

  if sub_items:
    html_parts.append("<p><strong>Substitution Options:</strong></p><ul>" + "".join(sub_items) + "</ul>")

  return "\n".join(html_parts)


# --- Main Parsing Logic ---
def parse_nippard_csv(csv_filepath, exercise_replacements):
  program_obj = Program(
    name="The Bodybuilding Transformation System - Beginner",  # From CSV Title
    arthur="Jeff Nippard",
    programLength="12 Weeks",  # Inferred from content
    uri="",
    level="Beginner",  # Based on CSV title, adjust if needed
    programEquipment="Full Gym",
    # Generic, can be refined
    daysPerWeek="5 training days per week (with 2 rest days implied by structure)"
  )

  program_notes_list = []
  warmup_protocol_general = []
  warmup_protocol_specific = []

  current_mesocycle_obj = None
  current_microcycle_obj = None
  current_advanced_workout_obj = None
  current_week_num_overall = 0
  workout_day_in_week = 0
  exercises_started = False

  # Column indices based on CSV structure (0-indexed)
  # "Week X";"Exercise";"Last-Set Int...";"Warm-up Sets";"Working Sets";"Reps";"Track Set 1";"Track Set 2";"Track Set 3";"Track Set 4";"Early Set RPE";"Last Set RPE";"Rest";"Sub1";"Sub2";"Notes"
  #    A    ;     B    ;       C        ;       D        ;        E       ;   F  ;       G       ;       H       ;       I       ;       J       ;       K        ;        L       ;   M  ;   N  ;   O  ;   P
  COL_WORKOUT_TYPE_OR_WEEK = 0
  COL_EXERCISE = 1
  COL_LAST_SET_INTENSITY = 2
  COL_WARMUP_SETS = 3
  COL_WORKING_SETS = 4
  COL_REPS = 5
  COL_REST_DAY = 8
  # Skipping Tracking Set Columns G, H, I, J
  COL_EARLY_SET_RPE = 10
  COL_LAST_SET_RPE = 11
  COL_REST = 12
  COL_SUB_1 = 13
  COL_SUB_2 = 14
  COL_NOTES = 15

  with open(csv_filepath, 'r', encoding='utf-8') as f:
    reader = csv.reader(f, delimiter=';')  # Using semicolon delimiter

    for row_idx, row in enumerate(reader):
      if not any(field.strip() for field in row):  # Skip empty rows
        continue

      # --- Initial Info Capture (Program Notes, Warmup) ---
      if row_idx < 25:  # Heuristic: first few rows are intro/warmup
        if "IMPORTANT PROGRAM NOTES" in row[0]:
          program_notes_list.append(
            row[0].split("IMPORTANT PROGRAM NOTES (READ BEFORE STARTING)")[-1].strip())
        elif "WARM UP PROTOCOL" in row[0]:
          # Start capturing warm-up, switch when "Foundation Block" or similar is found
          pass  # Handled by specific checks below
        elif "General Warm-Up" in row[4] and row[5]:
          warmup_protocol_general.append(f"{row[4].strip()}: {row[5].strip()}")
        elif "Exercise-Specific Warm-Up" in row[4] and row[5]:
          warmup_protocol_specific.append(f"{row[4].strip()}: {row[5].strip()}")
        elif program_notes_list and row[0].strip().startswith("●"):  # Continuation of program notes
          program_notes_list.append(row[0].strip())
        continue

      # --- Mesocycle and Microcycle Detection ---
      first_col = row[COL_WORKOUT_TYPE_OR_WEEK].strip()

      if "Foundation Block" in first_col:  # and not current_mesocycle_obj or (
        # current_mesocycle_obj and current_mesocycle_obj.name != "Foundation Block"):
        if current_mesocycle_obj: program_obj.mesocycles.append(current_mesocycle_obj)
        current_mesocycle_obj = Mesocycle(
          name="Foundation Block",
          description="Weeks 1-5. Focus on mastering technique and building a solid foundation. Weeks 1-2 feature 1 working set per exercise. Weeks 3-5 progress to 2 working sets per exercise with increasing RPE targets.",
          order=1,
          microcycles=Listing("Microcycle")
        )
        exercises_started = False  # Reset for new block header
      # this logic is wrong
      elif "Ramping Block" in first_col:  # and not current_mesocycle_obj or (
        # current_mesocycle_obj.name != "Ramping Block"): # current_mesocycle_obj and
        if current_mesocycle_obj: program_obj.mesocycles.append(current_mesocycle_obj)
        current_mesocycle_obj = Mesocycle(
          name="Ramping Block",
          description="Weeks 6-12. Focus on progressively increasing intensity and volume. Week 6 features 1 working set with moderate RPEs. Weeks 7-12 increase working sets and introduce 'Failure' as an intensity technique for many exercises, with higher RPE targets for early sets.",
          order=2,
          microcycles=Listing("Microcycle")
        )
        exercises_started = False

      week_match = re.match(r"Week (\d+)", first_col, re.IGNORECASE)
      if week_match:
        current_week_num_overall = int(week_match.group(1))
        workout_day_in_week = 0  # Reset for new week
        current_microcycle_obj = Microcycle(
          name=f"Week {current_week_num_overall}",
          description=f"Training for week {current_week_num_overall}.",  # Generic, can be enhanced
          order=current_week_num_overall,
          advancedWorkouts=Listing("AdvancedWorkout")
        )
        if current_mesocycle_obj:  # Ensure a mesocycle is active
          current_mesocycle_obj.microcycles.append(current_microcycle_obj)
        else:  # Default to foundation if no block explicitly started (should not happen with current CSV)
          if not program_obj.mesocycles or program_obj.mesocycles[-1].name != "Foundation Block":
            current_mesocycle_obj = Mesocycle(name="Foundation Block", order=1,
                                              microcycles=Listing("Microcycle", [current_microcycle_obj]))
            program_obj.mesocycles.append(current_mesocycle_obj)
          else:
            program_obj.mesocycles[-1].microcycles.append(current_microcycle_obj)

        exercises_started = True  # Wait for next line which should be column headers or workout type
        continue  # Move to next row after processing week header

      # Check for actual exercise table header (column B is "Exercise")
      if row[COL_EXERCISE].strip().lower() == "exercise":
        exercises_started = True
        continue  # Skip header row

      if not exercises_started:  # If we are past intro and not in an exercise block yet
        continue

      # --- Workout and Exercise Parsing ---

      workout_type_str = row[COL_WORKOUT_TYPE_OR_WEEK].strip()
      original_exercise_name = row[COL_EXERCISE].strip()
      final_exercise_name = exercise_replacements.get(original_exercise_name, original_exercise_name)

      if workout_type_str and (
          workout_type_str.lower() != "rest day" or workout_type_str.lower() != "set 3"):  # New workout block
        workout_day_in_week += 1
        current_advanced_workout_obj = AdvancedWorkout(
          name=workout_type_str.upper(),  # e.g. UPPER (STRENGTH FOCUS)
          day=workout_day_in_week,
          notes=Listing("String",
                        ["Perform a full general warm-up and exercise-specific warm-up (5-10 mins max)."]),
          # Generic
          advancedExercisesSets=Listing("AdvancedExerciseSets")
        )
        if current_microcycle_obj:  # Ensure a microcycle is active
          current_microcycle_obj.advancedWorkouts.append(current_advanced_workout_obj)

      if workout_type_str.lower() == "rest day":
        # Optionally, create a "Rest Day" workout object or just advance day counter for next actual workout
        # For simplicity, we'll just ensure the next workout gets the correct day number.
        # If a workout was just completed, its day is set. The next actual workout will increment.
        # If multiple rest days, the counter needs to be handled if you represent rest days explicitly.
        # This parser assumes rest days are just gaps between numbered workout days.
        # workout_day_in_week += 1  # counts as a day of the week cycle
        current_advanced_workout_obj = None  # No active workout on rest day
        continue

      if current_advanced_workout_obj and original_exercise_name:  # We are in an exercise row for an active workout

        try:
          last_set_intensity = strip_na_and_tilde(row[COL_LAST_SET_INTENSITY])
          warmup_sets_csv_str = row[COL_WARMUP_SETS]  # Handle date-like format
          # warmup_sets_min, warmup_sets_max  = parse_rep_range_from_csv(parse_warmup_sets(row[COL_WARMUP_SETS]))  # Handle date-like format

          working_sets_val = strip_na_and_tilde(row[COL_WORKING_SETS])
          num_working_sets = 0
          if working_sets_val:
            try:
              num_working_sets = int(working_sets_val)  # + warmup_sets_max
            except ValueError:
              print(
                f"Warning: Could not parse Working Sets '{working_sets_val}' for {original_exercise_name} in week {current_week_num_overall}. Defaulting to 1.")
              num_working_sets = 1  # Fallback
          else:  # if empty string, assume 1 based on program structure
            num_working_sets = 1

          reps_csv = row[COL_REPS]
          min_reps, max_reps = parse_rep_range_from_csv(reps_csv)

          early_rpe_csv = strip_na_and_tilde(row[COL_EARLY_SET_RPE])
          last_rpe_csv = strip_na_and_tilde(row[COL_LAST_SET_RPE])

          rpe_list = determine_rpe_list_from_csv(
            current_week_num_overall,
            num_working_sets,
            early_rpe_csv,
            last_rpe_csv,
            last_set_intensity
          )

          rest_str = strip_na_and_tilde(row[COL_REST])
          original_sub1_str = strip_na_and_tilde(row[COL_SUB_1])
          original_sub2_str = strip_na_and_tilde(row[COL_SUB_2])
          sub1_str = exercise_replacements.get(original_sub1_str, original_sub1_str)
          sub2_str = exercise_replacements.get(original_sub2_str, original_sub2_str)
          # notes_str = strip_na_and_tilde(row[COL_NOTES])
          main_notes_str = strip_na_and_tilde(row[COL_NOTES])

          # exercise_notes = Listing("String")
          # if warmup_sets_str and warmup_sets_str.lower() != 'n/a':
          #     exercise_notes.append(f"Warm-up Sets: {warmup_sets_str}")
          # if rest_str: exercise_notes.append(f"Rest: {rest_str}")
          # if sub1_str: exercise_notes.append(f"Substitution Option 1: {sub1_str}")
          # if sub2_str: exercise_notes.append(f"Substitution Option 2: {sub2_str}")
          # if notes_str: exercise_notes.append(notes_str)  # Main exercise note
          # if last_set_intensity and last_set_intensity.lower() != "n/a":
          #     exercise_notes.append(f"Last-Set Intensity Technique: {last_set_intensity}")

          # Determine warm-up scheme
          warmup_count = get_warmup_set_count(warmup_sets_csv_str)
          selected_warmup_scheme = WARMUP_SCHEME_MAP.get(warmup_count)

          exercise_set_schemes = Listing("SetScheme")
          if selected_warmup_scheme:
            exercise_set_schemes.append(selected_warmup_scheme)

          # **NEW**: Create HTML description
          html_description = create_html_description(
            main_notes=main_notes_str,
            rest=rest_str,
            warmup_str=warmup_sets_csv_str,
            intensity=last_set_intensity,
            sub1=sub1_str,
            sub2=sub2_str
          )

          # print(html_description)

          working_set_scheme = SetScheme(
            sets=num_working_sets,
            minRepetitions=min_reps,
            maxRepetitions=max_reps,
            targetRatePerceivedEffort=Listing("Int", rpe_list) if rpe_list else None,
          )

          exercise_set_schemes.append(working_set_scheme)

          adv_exercise_set = AdvancedExerciseSets(
            name=final_exercise_name,
            description=html_description,  # Populate new field
            notes=Listing("String"),  # Old field is now empty
            # sets=num_working_sets,
            # minRepetitions=min_reps,
            # maxRepetitions=max_reps,
            # targetRatePerceivedEffort=Listing("Int", rpe_list) if rpe_list else None,
            setScheme=exercise_set_schemes
            # notes=exercise_notes
          )
          current_advanced_workout_obj.advancedExercisesSets.append(adv_exercise_set)

        except IndexError:
          print(
            f"Warning: Row with exercise '{original_exercise_name}' has too few columns. Skipping. Row data: {row}")
        except Exception as e:
          print(
            f"Error processing exercise '{original_exercise_name}' in week {current_week_num_overall}, Workout {workout_type_str}: {e}. Row: {row}")

  # Finalize program description
  program_description_parts = []
  if program_notes_list:
    program_description_parts.append(
      "IMPORTANT PROGRAM NOTES (READ BEFORE STARTING)\n" + "\n".join(program_notes_list))
  if warmup_protocol_general or warmup_protocol_specific:
    program_description_parts.append("\nWARM UP PROTOCOL")
    if warmup_protocol_general:
      program_description_parts.append(
        "General Warm-Up:\n" + "\n".join([f"  ● {item}" for item in warmup_protocol_general]))
    if warmup_protocol_specific:
      program_description_parts.append(
        "Exercise-Specific Warm-Up:\n" + "\n".join([f"  ● {item}" for item in warmup_protocol_specific]))

  program_obj.description = "\n\n".join(
    program_description_parts) if program_description_parts else program_obj.description

  # Append the last active mesocycle if any
  if current_mesocycle_obj and current_mesocycle_obj not in program_obj.mesocycles:
    program_obj.mesocycles.append(current_mesocycle_obj)

  return program_obj


# </editor-fold>

# --- Entry Point ---
if __name__ == "__main__":
  csv_file_path = 'Copy of The_Bodybuilding_Transformation_System_-_Intermediate-Advanced.csv'  # Make sure this file exists in the same directory

  # --- USER-DEFINED EXERCISE REPLACEMENTS ---
  # The user can edit this dictionary to specify their desired substitutions.
  # Key: The exact exercise name from the CSV file.
  # Value: The new exercise name to use in the output.
  exercise_replacement_map = {
    "1-Arm 45° Cable Rear Delt Flye": "Cable One Arm Reverse Fly",
    "45° Hyperextension": "45° Hyperextension",
    "45° Incline Barbell Press": "Barbell Incline Bench Press",
    "45° Incline DB Press": "Dumbbell Incline Bench Press",
    "45° Incline Machine Press": "Lever Incline Bench Press",
    "Ab Wheel Rollout": "Wheel Rollout",
    "Barbell Bench Press": "Barbell Bench Press",
    "Barbell RDL": "Barbell Straight-back Straight-leg Deadlift",
    "Bayesian Cable Curl": "Bayesian Curl",
    "Bench Dip": "Bench Dip",
    "Bottom-Half DB Flye": "Dumbbell Fly",
    "Bottom-Half Seated Cable Flye": "Cable Seated Fly",
    "Cable Crossover Ladder": "Cable Standing Fly",
    "Cable Crunch": "Cable Kneeling Crunch",
    "Cable Hip Abduction": "Cable Hip Abduction",
    "Cable Paused Shrug-In": "Cable Shrug (dual pulley)",
    "Cable Pull-Through": "Cable Pull-Through",
    "Cable Rope Hammer Curl": "Cable Hammer Curl",
    "Cable Shoulder Press": "Cable Shoulder Press",
    "Cable Triceps Kickback": "Cable One Arm Pushdown",
    "Chest-Supported Machine Row": "Lever Seated Row",
    "Chest-Supported T-Bar Row": "Lever T-bar Row (plate loaded)",
    "Concentration Cable Curl": "Cable Concentration Curl",
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
    "Decline Weighted Crunch": "Weighted Incline Sit-up",
    "Dual-Handle Lat Pulldown": "Cable Parallel Grip Pulldown",
    "EZ-Bar Cable Curl": "Cable Curl",
    "EZ-Bar Curl": "Barbell Curl",
    "EZ-Bar Preacher Curl": "Barbell Preacher Curl",
    "EZ-Bar Skull Crusher": "Barbell Lying Triceps Extension",
    "Glute-Ham Raise": "Glute-Ham Raise",
    "Goblet Squat": "Goblet Squat",
    "Hack Squat": "Sled Hack Squat",
    "Hammer Preacher Curl": "Hammer Preacher Curl",
    "Hanging Leg Raise": "Hanging Leg Raise",
    "High-Bar Back Squat": "Barbell Full Squat",
    "High-Cable Cuffed Lateral Raise": "High-Cable Cuffed Lateral Raise",
    "High-Cable Lateral Raise": "Cable One Arm Lateral Raise",
    "Incline Chest-Supported DB Row": "Dumbbell Lying Row",
    "Incline DB Stretch Curl": "Dumbbell Incline Curl",
    "Katana Triceps Extension": "Cable One Arm Triceps Extension (pronated grip)",
    "Lateral Band Walk": "Lateral Band Walk",
    "Lean-Back Lat Pulldown": "Cable Pulldown",
    "Lean-Back Machine Pulldown": "Lever Pulldown",
    "Lean-In DB Lateral Raise": "Lean-In Dumbbell Lateral Raise",
    "Leg Extension": "Lever Leg Extension",
    "Leg Press": "Sled 45° Leg Press",
    "Leg Press Calf Press": "Sled 45° Calf Raise (plate loaded)",
    "Long-Lever Plank": "Long-Lever Plank",
    "Low-to-High Cable Crossover": "Cable Standing Incline Fly",
    "Lying Leg Curl": "Lever Lying Leg Curl",
    "Lying Leg Raise": "Lying Leg Raise",
    "Machine Chest Press": "Lever Chest Press",
    "Machine Crunch": "Lever Seated Crunch",
    "Machine Hip Abduction": "Lever Seated Hip Abduction",
    "Machine Preacher Curl": "Lever Preacher Curl",
    "Machine Shoulder Press": "Lever Shoulder Press",
    "Machine Shrug": "Lever Shrug",
    "Modified Candlestick": "Modified Candlestick",
    "Neutral-Grip Lat Pulldown": "Cable Parallel Grip Pulldown",
    "Neutral-Grip Pull-Up": "Neutral-Grip Pull-Up",
    "Nordic Ham Curl": "Nordic Ham Curl",
    "Overhead Cable Triceps Extension (Bar)": "Cable Forward Triceps Extension",
    "Overhead Cable Triceps Extension (Rope)": "Cable Triceps Extension (with rope)",
    "Pec Deck": "Lever Pec Deck Fly",
    "Pendlay Deficit Row": "Pendlay Row",
    "Pull-Up": "Pull-Up",
    "Reverse Nordic": "Reverse Nordic",
    "Reverse Pec Deck": "Lever Seated Reverse Fly (on pec deck)",
    "Rope Face Pull": "Cable Standing Rear Delt Row (with rope)",
    "Seated Calf Raise": "Lever Seated Calf Raise",
    "Seated DB Shoulder Press": "Dumbbell Shoulder Press",
    "Seated Leg Curl": "Lever Seated Leg Curl",
    "Seated Super-Bayesian High Cable Curl": "Seated Bayesian Cable Curl",
    "Single-Arm DB Row": "Dumbbell Bent-over Row",
    "Sissy Squat": "Sissy Squat",
    "Smith Machine Row": "Smith Bent-over Row",
    "Smith Machine Squat": "Smith Squat",
    "Smith Machine Static Lunge": "Smith Rear Lunge",
    "Smith Machine Static Lunge w/ Elevated Front Foot": "Smith Rear Lunge",
    "Snatch-Grip RDL": "Romanian Deadlift",
    "Standing Calf Raise": "Lever Standing Calf Raise",
    "Swiss Ball Rollout": "Stability Ball Rollout",
    "Triceps Pressdown (Bar)": "Cable Forward Triceps Extension",
    "Triceps Pressdown (Rope)": "Cable Triceps Extension (with rope)",
    "Walking Lunge": "Dumbbell Walking Lunge",
    "Wide-Grip Lat Pulldown": "Cable Pulldown",
    "Wide-Grip Pull-Up": "Pull-Up",
    "Dual - Handle Elbows - Out Cable Row": "Cable Seated High Row",
    "Machine Hip Adduction": "Lever Seated Hip Adduction",
    "Neutral - Grip Seated Cable Row": "Cable Seated Row",
    "Roman Chair Leg Raise": "Vertical Leg Raise (on parallel bars)"
  }

  print("--- Applying Exercise Replacements ---")
  for original, new in exercise_replacement_map.items():
    print(f'Replacing "{original}" with "{new}"')
  print("--------------------------------------")

  # Pass the replacement map to the parsing function
  program_data = parse_nippard_csv(csv_file_path, exercise_replacement_map)

  # Generate the PKL output string
  header = "module com.example.myapplication.AdvancedProgramTemplate\n\n"

  # PKL Class definitions string (ensure this matches your MAX_PLAN_AdvancedProgramTemplate.txt)
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

warmUpScheme1Set: SetScheme = new SetScheme {
  sets = 1
  setType = 2
  // Reps: "~6-10 reps (or until you feel warm and loose)"
  // We'll use the higher end for the target `repetitions` list item.
  repetitions = new Listing<Int> { 10 } // Target reps for the set
  percentage1RM = new Listing<Float> { 0.60 } // ~60% of planned working weight
  // notes could be added here if SetScheme had a notes field:
  // "Use ~60% of your planned working weight for ~6-10 reps (or until you feel warm and loose)"
}

warmUpScheme2Sets: SetScheme = new SetScheme {
  sets = 2
  setType = 2
  // Warm-Up Set #1 = ~50% of planned working weight for ~6-10 reps
  // Warm-Up Set #2 = ~70% of planned working weight for 4-6 reps
  repetitions = new Listing<Int> { 
    10
    6
  } // Target reps for each set (using higher end of range)
  percentage1RM = new Listing<Float> { 
    0.50
    0.70
  }
  // notes: "Perform a mini warm-up pyramid"
}

warmUpScheme3Sets: SetScheme = new SetScheme {
  sets = 3
  setType = 2
  // Warm-Up Set #1 = ~45% of planned working weight for ~6-10 reps
  // Warm-Up Set #2 = ~65% of planned working weight for 4-6 reps
  // Warm-Up Set #3 = ~85% of planned working weight for 3-4 reps
  repetitions = new Listing<Int> { 
    10
    6
    4 
  } // Target reps for each set (using higher end of range)
  percentage1RM = new Listing<Float> { 
    0.45
    0.65
    0.85
  }
  // notes: "Perform a full warm-up pyramid"
}

warmUpScheme4Sets: SetScheme = new SetScheme {
  sets = 4
  setType = 2
  // Warm-Up Set #1 = ~45% of planned working weight for ~6-10 reps
  // Warm-Up Set #2 = ~60% of planned working weight for 4-6 reps
  // Warm-Up Set #3 = ~75% of planned working weight for 3-5 reps
  // Warm-Up Set #4 = ~85% of planned working weight for 2-4 reps
  repetitions = new Listing<Int> { 
    10
    6
    5
    4 
  } // Target reps for each set (using higher end of range)
  percentage1RM = new Listing<Float> { 
    0.45
    0.60
    0.75
    0.85 
  }
  // notes: "Perform a full warm-up pyramid"
}

programWarmUpSchemes: Mapping<String, SetScheme> = new Mapping {
  ["1-set"] = warmUpScheme1Set
  ["2-sets"] = warmUpScheme2Sets
  ["3-sets"] = warmUpScheme3Sets
  ["4-sets"] = warmUpScheme4Sets
}

"""

  # The program instance string generated by our Python objects
  program_instance_pkl_str = program_data.to_pkl_string(0)

  full_pkl_output = f"{header}{class_definitions_pkl_str}\n// --- Program Instance ---\n{program_instance_pkl_str}\n"

  filename = f"jeff_nippard_The_Bodybuilding_Transformation_System_-_Intermediate-Advanced_{datetime.datetime.now().timestamp()}.pkl"

  print(f"Attempting to write to {filename}")
  try:
    with open(filename, "w", encoding='utf-8') as f:
      f.write(full_pkl_output)
    print(f"Successfully generated {filename}")
  except Exception as e:
    print(f"Error writing file: {e}")

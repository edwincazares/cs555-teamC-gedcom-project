# Edwin Cazares Sprint 1 Stories
# US27: Include individual ages
# US28: Order siblings by age

from datetime import date, datetime


def calculate_age(birthday, death_date="NA"):
    """US27: Calculate age for living and deceased individuals."""
    if birthday == "NA" or birthday == "":
        return "NA"

    try:
        birth = datetime.strptime(birthday, "%d %b %Y").date()
        if death_date != "NA" and death_date != "":
            end_date = datetime.strptime(death_date, "%d %b %Y").date()
        else:
            end_date = date.today()

        age = end_date.year - birth.year
        if (end_date.month, end_date.day) < (birth.month, birth.day):
            age -= 1
        return age
    except ValueError:
        return "NA"


def get_birth_date(individual_id, individuals):
    """Return birth date object for sorting siblings. Unknown dates go last."""
    birthday = individuals.get(individual_id, {}).get("birthday", "NA")
    try:
        return datetime.strptime(birthday, "%d %b %Y")
    except ValueError:
        return datetime.max


def format_children_by_age(children, individuals):
    """US28: Display children oldest to youngest instead of random set order."""
    if len(children) == 0:
        return "NA"

    sorted_children = sorted(children, key=lambda child_id: get_birth_date(child_id, individuals))
    return "{" + ", ".join(sorted_children) + "}"


# Use this inside print_individuals() when building each person row:
# age = calculate_age(person["birthday"], person["death"])
#
# table.add_row([
#     person["id"],
#     person["name"],
#     person["sex"],
#     format_date(person["birthday"]),
#     age,
#     alive,
#     format_date(person["death"]),
#     person["child"],
#     format_set(person["spouse"])
# ])


# Replace the Children field in print_families() with this:
# format_children_by_age(family["children"], individuals)

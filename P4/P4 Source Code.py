"""
CS555 Agile Methods for Software Development
Team C GEDCOM Project - Sprint 1 Complete
GitHub Repository: https://github.com/edwincazares/cs555-teamC-gedcom-project

Sprint 1 user stories implemented:
US01: Dates before current date
US02: Birth before marriage
US07: Less than 150 years old
US08: Birth before marriage of parents
US27: Include individual ages
US28: Order siblings by age
US29: List deceased
US30: List living married
US31: List living single
US32: List multiple births
US35: List recent births
US36: List recent deaths
"""

from datetime import date, datetime, timedelta
import re
import sys


VALID_TAGS = {
    "INDI", "NAME", "SEX", "BIRT", "DEAT", "FAMC", "FAMS",
    "FAM", "MARR", "HUSB", "WIFE", "CHIL", "DIV", "DATE",
    "HEAD", "TRLR", "NOTE"
}


def clean_id(raw_id):
    return raw_id.strip()


def natural_id_key(identifier):
    """
    Sort IDs by their numeric value, so @I2@ comes before @I10@.
    This is used for both individual and family IDs.
    """
    match = re.search(r"(\d+)", identifier)
    number = int(match.group(1)) if match else 0
    prefix = re.sub(r"\d+", "", identifier)
    return prefix, number


def parse_date(date_text):
    if not date_text or date_text == "NA":
        return None
    try:
        return datetime.strptime(date_text, "%d %b %Y").date()
    except ValueError:
        return None


def format_date(date_text):
    parsed = parse_date(date_text)
    if parsed is None:
        return "NA"
    return parsed.strftime("%Y-%m-%d")


def calculate_age(birthday, death_date="NA"):
    """US27: Include individual ages."""
    birth = parse_date(birthday)
    if birth is None:
        return "NA"

    death = parse_date(death_date)
    end_date = death if death is not None else date.today()

    age = end_date.year - birth.year
    if (end_date.month, end_date.day) < (birth.month, birth.day):
        age -= 1
    return age


def format_set(values):
    if not values:
        return "NA"
    return "{" + ", ".join(values) + "}"


def format_table(headers, rows):
    """Simple fixed-width table so output does not wrap or merge columns."""
    all_rows = [headers] + rows
    widths = []

    for col in range(len(headers)):
        width = max(len(str(row[col])) for row in all_rows)
        widths.append(width)

    separator = "+-" + "-+-".join("-" * width for width in widths) + "-+"

    def format_row(row):
        return "| " + " | ".join(str(row[i]).ljust(widths[i]) for i in range(len(headers))) + " |"

    output = [separator, format_row(headers), separator]
    for row in rows:
        output.append(format_row(row))
    output.append(separator)

    return "\n".join(output)


def parse_gedcom(filename):
    individuals = {}
    families = {}

    current_indi = None
    current_fam = None
    last_event = None

    with open(filename, "r", encoding="utf-8") as gedcom_file:
        for line_number, raw_line in enumerate(gedcom_file, start=1):
            line = raw_line.strip()
            if not line:
                continue

            fields = line.split()
            level = fields[0]

            if level == "0" and len(fields) >= 3 and fields[2] in ("INDI", "FAM"):
                tag = fields[2]
                arguments = fields[1]
            else:
                tag = fields[1] if len(fields) > 1 else ""
                arguments = " ".join(fields[2:]) if len(fields) > 2 else ""

            if tag == "INDI":
                current_indi = clean_id(arguments)
                current_fam = None
                last_event = None
                individuals[current_indi] = {
                    "id": current_indi,
                    "name": "NA",
                    "sex": "NA",
                    "birthday": "NA",
                    "death": "NA",
                    "child": [],
                    "spouse": []
                }

            elif tag == "NAME" and current_indi:
                individuals[current_indi]["name"] = arguments

            elif tag == "SEX" and current_indi:
                individuals[current_indi]["sex"] = arguments

            elif tag == "BIRT" and current_indi:
                last_event = "BIRT"

            elif tag == "DEAT" and current_indi:
                last_event = "DEAT"

            elif tag == "DATE" and current_indi and last_event == "BIRT":
                individuals[current_indi]["birthday"] = arguments

            elif tag == "DATE" and current_indi and last_event == "DEAT":
                individuals[current_indi]["death"] = arguments

            elif tag == "FAMC" and current_indi:
                individuals[current_indi]["child"].append(clean_id(arguments))

            elif tag == "FAMS" and current_indi:
                individuals[current_indi]["spouse"].append(clean_id(arguments))

            elif tag == "FAM":
                current_fam = clean_id(arguments)
                current_indi = None
                last_event = None
                families[current_fam] = {
                    "id": current_fam,
                    "husband": "NA",
                    "wife": "NA",
                    "children": [],
                    "married": "NA",
                    "divorced": "NA"
                }

            elif tag == "HUSB" and current_fam:
                families[current_fam]["husband"] = clean_id(arguments)

            elif tag == "WIFE" and current_fam:
                families[current_fam]["wife"] = clean_id(arguments)

            elif tag == "CHIL" and current_fam:
                families[current_fam]["children"].append(clean_id(arguments))

            elif tag == "MARR" and current_fam:
                last_event = "MARR"

            elif tag == "DIV" and current_fam:
                last_event = "DIV"

            elif tag == "DATE" and current_fam and last_event == "MARR":
                families[current_fam]["married"] = arguments

            elif tag == "DATE" and current_fam and last_event == "DIV":
                families[current_fam]["divorced"] = arguments

    return individuals, families


def get_birth_for_sort(individual_id, individuals):
    birth = parse_date(individuals.get(individual_id, {}).get("birthday", "NA"))
    return birth if birth is not None else date.max


def children_ordered_by_age(children, individuals):
    """US28: Order siblings by decreasing age, oldest first."""
    return sorted(children, key=lambda child_id: get_birth_for_sort(child_id, individuals))


def is_living(person):
    return person["death"] == "NA"


def is_married_living(person):
    return is_living(person) and len(person["spouse"]) > 0


def print_individuals(individuals):
    rows = []
    for individual_id in sorted(individuals, key=natural_id_key):
        person = individuals[individual_id]
        age = calculate_age(person["birthday"], person["death"])

        rows.append([
            person["id"],
            person["name"],
            person["sex"],
            format_date(person["birthday"]),
            age,
            is_living(person),
            format_date(person["death"]),
            format_set(person["child"]),
            format_set(person["spouse"])
        ])

    print("Individuals")
    print(format_table(
        ["ID", "Name", "Gender", "Birthday", "Age", "Alive", "Death", "Child", "Spouse"],
        rows
    ))


def print_families(individuals, families):
    rows = []
    for family_id in sorted(families, key=natural_id_key):
        family = families[family_id]

        husband_id = family["husband"]
        wife_id = family["wife"]

        husband_name = individuals.get(husband_id, {}).get("name", "NA")
        wife_name = individuals.get(wife_id, {}).get("name", "NA")
        children = children_ordered_by_age(family["children"], individuals)

        rows.append([
            family["id"],
            format_date(family["married"]),
            format_date(family["divorced"]),
            husband_id,
            husband_name,
            wife_id,
            wife_name,
            format_set(children)
        ])

    print("\nFamilies")
    print(format_table(
        ["ID", "Married", "Divorced", "Husband ID", "Husband Name", "Wife ID", "Wife Name", "Children"],
        rows
    ))

def print_us01(individuals, families):
    print("\nUS01: Dates before current date")

    today = date.today()
    found_error = False

    for person in sorted(individuals.values(), key=lambda p: natural_id_key(p["id"])):
        birth_date = parse_date(person["birthday"])
        death_date = parse_date(person["death"])

        if birth_date is not None and birth_date > today:
            found_error = True
            print(
                f"ERROR: INDIVIDUAL: US01: {person['id']}: "
                f"Birth date {format_date(person['birthday'])} occurs after the current date."
            )

        if death_date is not None and death_date > today:
            found_error = True
            print(
                f"ERROR: INDIVIDUAL: US01: {person['id']}: "
                f"Death date {format_date(person['death'])} occurs after the current date."
            )

    for family in sorted(families.values(), key=lambda f: natural_id_key(f["id"])):
        marriage_date = parse_date(family["married"])
        divorce_date = parse_date(family["divorced"])

        if marriage_date is not None and marriage_date > today:
            found_error = True
            print(
                f"ERROR: FAMILY: US01: {family['id']}: "
                f"Marriage date {format_date(family['married'])} occurs after the current date."
            )

        if divorce_date is not None and divorce_date > today:
            found_error = True
            print(
                f"ERROR: FAMILY: US01: {family['id']}: "
                f"Divorce date {format_date(family['divorced'])} occurs after the current date."
            )

    if not found_error:
        print("PASS: US01: All birth, death, marriage, and divorce dates are before the current date.")

def print_us02(individuals, families):
    print("\nUS02: Birth before marriage")

    found_error = False

    for family in sorted(families.values(), key=lambda f: natural_id_key(f["id"])):
        marriage_date = parse_date(family["married"])

        if marriage_date is None:
            continue

        husband_id = family["husband"]
        wife_id = family["wife"]

        husband = individuals.get(husband_id)
        wife = individuals.get(wife_id)

        if husband is not None:
            husband_birth = parse_date(husband["birthday"])

            if husband_birth is not None and husband_birth > marriage_date:
                found_error = True
                print(
                    f"ERROR: FAMILY: US02: {family['id']}: "
                    f"Husband {husband_id} was born on {format_date(husband['birthday'])} "
                    f"after marriage date {format_date(family['married'])}."
                )

        if wife is not None:
            wife_birth = parse_date(wife["birthday"])

            if wife_birth is not None and wife_birth > marriage_date:
                found_error = True
                print(
                    f"ERROR: FAMILY: US02: {family['id']}: "
                    f"Wife {wife_id} was born on {format_date(wife['birthday'])} "
                    f"after marriage date {format_date(family['married'])}."
                )

    if not found_error:
        print("PASS: US02: All spouses were born before their marriage dates.")

def print_us07(individuals):
    print("\nUS07: Less than 150 years old")

    found_error = False

    for person in sorted(individuals.values(), key=lambda p: natural_id_key(p["id"])):
        current_age = calculate_age(person["birthday"], person["death"])

        if current_age is not None and current_age > 150:
            found_error = True
            print(
                f"ERROR: INDIVIDUAL: US07: {person['id']}: "
                f"Individual born on {format_date(person['birthday'])} is greater than 150 years of age."
            )

    if not found_error:
        print("PASS: US07: All individuals are younger than 150 years of age.")

def print_us08(individuals, families):
    print("\nUS08: Birth before marriage of parents")

    found_error = False

    for family in sorted(families.values(), key=lambda f: natural_id_key(f["id"])):
        marriage_date = parse_date(family["married"])
        divorce_date = parse_date(family["divorced"])

        for child_id in family["children"]:
            child = individuals.get(child_id)

            if child is None:
                continue

            birth_date = parse_date(child["birthday"])

            if birth_date is None:
                continue

            if marriage_date is not None and birth_date < marriage_date:
                found_error = True
                print(
                    f"ERROR: FAMILY: US08: {family['id']}: "
                    f"Child {child_id} was born on {format_date(child['birthday'])} "
                    f"before parents' marriage date {format_date(family['married'])}."
                )

            if divorce_date is not None and birth_date > divorce_date + timedelta(days=365):
                found_error = True
                print(
                    f"ERROR: FAMILY: US08: {family['id']}: "
                    f"Child {child_id} was born on {format_date(child['birthday'])} "
                    f", 1 year after parents' divorce date {format_date(family['divorced'])}."
                )

    if not found_error:
        print("PASS: US08: All individuals were born after the marriage of their parents and no more than 1 year after divorce.")



def print_us27(individuals):
    print("\nUS27: Include individual ages")
    print("PASS: The Individuals table includes an Age column calculated from birth and death dates.")


def print_us28(individuals, families):
    print("\nUS28: Order siblings by age")
    for family_id in sorted(families, key=natural_id_key):
        children = children_ordered_by_age(families[family_id]["children"], individuals)
        if children:
            print(f"PASS: FAMILY: US28: {family_id}: Children ordered oldest to youngest: {format_set(children)}")


def print_us29(individuals):
    print("\nUS29: List deceased")
    deceased = [person for person in individuals.values() if person["death"] != "NA"]
    for person in sorted(deceased, key=lambda p: natural_id_key(p["id"])):
        print(f"DECEASED: INDIVIDUAL: US29: {person['id']}: {person['name']} died on {format_date(person['death'])}")
    if not deceased:
        print("PASS: INDIVIDUAL: US29: No deceased individuals found.")


def print_us30(individuals):
    print("\nUS30: List living married")
    living_married = [person for person in individuals.values() if is_married_living(person)]
    for person in sorted(living_married, key=lambda p: natural_id_key(p["id"])):
        print(f"LIVING MARRIED: INDIVIDUAL: US30: {person['id']}: {person['name']} spouse families {format_set(person['spouse'])}")
    if not living_married:
        print("PASS: INDIVIDUAL: US30: No living married individuals found.")


def print_us31(individuals):
    print("\nUS31: List living single")
    living_single = []
    for person in individuals.values():
        age = calculate_age(person["birthday"], person["death"])
        if is_living(person) and isinstance(age, int) and age > 30 and not person["spouse"]:
            living_single.append(person)

    for person in sorted(living_single, key=lambda p: natural_id_key(p["id"])):
        print(f"LIVING SINGLE: INDIVIDUAL: US31: {person['id']}: {person['name']} is living, over 30, and has no spouse family.")
    if not living_single:
        print("PASS: INDIVIDUAL: US31: No living single individuals over 30 found.")


def print_us32(individuals, families):
    print("\nUS32: List multiple births")
    found = False
    for family_id in sorted(families, key=natural_id_key):
        groups = {}
        for child_id in families[family_id]["children"]:
            birthday = individuals.get(child_id, {}).get("birthday", "NA")
            groups.setdefault(birthday, []).append(child_id)

        for birthday, child_ids in groups.items():
            if birthday != "NA" and len(child_ids) > 1:
                found = True
                print(f"MULTIPLE BIRTH: FAMILY: US32: {family_id}: {format_date(birthday)} includes {format_set(children_ordered_by_age(child_ids, individuals))}")

    if not found:
        print("PASS: FAMILY: US32: No multiple births found.")

def print_us34(individuals, families):
    print("\nUS34: List large age differences")
    found = False
    for family in sorted(families.values(), key=lambda f: natural_id_key(f["id"])):
        marriage = parse_date(family["married"])

        if marriage is None:
            continue

        husband = individuals.get(family["husband"])
        wife = individuals.get(family["wife"])

        if not husband or not wife:
            continue

        husband_birthday = parse_date(husband["birthday"])
        wife_birthday = parse_date(wife["birthday"])

        if husband_birthday is None or wife_birthday is None:
            continue

        husband_age = marriage.year - husband_birthday.year
        wife_age = marriage.year - wife_birthday.year

        older = max(husband_age, wife_age)
        younger = min(husband_age, wife_age)

        if older > 2 * younger:
            found = True
            print(
                f"LARGE AGE DIFFERENCE: FAMILY: US34: {family['id']}: "
                f"{husband['id']} ({husband_age}) and {wife['id']} ({wife_age})"
            )

    if not found:
        print("PASS: FAMILY: US34: No couples found with large age differences.")

def print_us35(individuals):
    print("\nUS35: List recent births")
    cutoff = date.today() - timedelta(days=30)
    recent = []
    for person in individuals.values():
        birthday = parse_date(person["birthday"])
        if birthday is not None and cutoff <= birthday <= date.today():
            recent.append(person)

    for person in sorted(recent, key=lambda p: natural_id_key(p["id"])):
        print(f"RECENT BIRTH: INDIVIDUAL: US35: {person['id']}: {person['name']} was born on {format_date(person['birthday'])}")
    if not recent:
        print("PASS: INDIVIDUAL: US35: No births found in the last 30 days.")


def print_us36(individuals):
    print("\nUS36: List recent deaths")
    cutoff = date.today() - timedelta(days=30)
    recent = []
    for person in individuals.values():
        death = parse_date(person["death"])
        if death is not None and cutoff <= death <= date.today():
            recent.append(person)

    for person in sorted(recent, key=lambda p: natural_id_key(p["id"])):
        print(f"RECENT DEATH: INDIVIDUAL: US36: {person['id']}: {person['name']} died on {format_date(person['death'])}")
    if not recent:
        print("PASS: INDIVIDUAL: US36: No deaths found in the last 30 days.")

def print_us37(individuals, families):
    print("\nUS37: List recent survivors")
    cutoff = date.today() - timedelta(days=30)
    found = False

    for person in sorted(individuals.values(), key=lambda p: natural_id_key(p["id"])):
        death_date = parse_date(person["death"])

        if death_date is None or not (cutoff <= death_date <= date.today()):
            continue

        for family_id in person["spouse"]:
            family = families.get(family_id)

            if family is None:
                continue

            for child_id in family["children"]:
                child = individuals.get(child_id)

                if child and child["death"] == "NA":
                    found = True
                    print(
                        f"SURVIVOR: INDIVIDUAL: US37: {child['id']}: "
                        f"{child['name']} is a living child of "
                        f"{person['id']}."
                    )

    if not found:
        print("PASS: INDIVIDUAL: US37: No recent survivors found.")

def print_us38(individuals):
    print("\nUS38: List upcoming birthdays")
    today = date.today()
    found = False

    for person in sorted(individuals.values(), key=lambda p: natural_id_key(p["id"])):
        if person["death"] != "NA":
            continue

        birth_date = parse_date(person["birthday"])

        if birth_date is None:
            continue

        birthday = date(
            today.year,
            birth_date.month,
            birth_date.day
        )

        if birthday < today:
            birthday = date(
                today.year + 1,
                birth_date.month,
                birth_date.day
            )

        days_until_birthday = (birthday - today).days

        if 0 <= days_until_birthday <= 30:
            found = True
            print(
                f"UPCOMING BIRTHDAY: INDIVIDUAL: US38: "
                f"{person['id']}: {person['name']} "
                f"has a birthday on {birthday}"
            )

    if not found:
        print("PASS: INDIVIDUAL: US38: No upcoming birthdays")

def main():
    filename = sys.argv[1] if len(sys.argv) > 1 else "teamC_acceptance_test.ged"
    individuals, families = parse_gedcom(filename)

    print(f"GEDCOM Acceptance Test File: {filename}")
    print("GitHub Repository: https://github.com/edwincazares/cs555-teamC-gedcom-project\n")

    print_individuals(individuals)
    print_families(individuals, families)

    print("\nSprint 1 User Story Demonstration")
    print_us01(individuals, families)
    print_us02(individuals, families)
    print_us07(individuals)
    print_us08(individuals, families)
    print_us27(individuals)
    print_us28(individuals, families)
    print_us29(individuals)
    print_us30(individuals)
    print_us31(individuals)
    print_us32(individuals, families)
    print_us34(individuals, families)
    print_us35(individuals)
    print_us36(individuals)
    print_us37(individuals, families)
    print_us38(individuals)

if __name__ == "__main__":
    main()

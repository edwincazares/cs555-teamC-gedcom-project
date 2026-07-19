"""
CS555 Agile Methods for Software Development
Team C GEDCOM Project - Sprint 2 Complete
GitHub Repository: https://github.com/edwincazares/cs555-teamC-gedcom-project

Sprint 1 and Sprint 2 user stories implemented:
US01: Dates before current date
US02: Birth before marriage
US03: Birth before death
US04: Marriage before divorce
US05: Marriage before death
US06: Divorce before death
US07: Less than 150 years old
US08: Birth before marriage of parents
US09: Birth before death of parents
US10: Marriage after age 14
US11: No bigamy
US27: Include individual ages
US28: Order siblings by age
US29: List deceased
US30: List living married
US31: List living single
US32: List multiple births
US34: List large age differences
US35: List recent births
US36: List recent deaths
US37: List recent survivors
US38: List upcoming birthdays
"""

from datetime import date, datetime, timedelta
import re
import sys
import calendar


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

def print_us03(individuals):
    print("\nUS03: Birth before death")

    found_error = False

    for individual in sorted(individuals.values(), key=lambda i: natural_id_key(i["id"])):
        birth_date = parse_date(individual["birthday"])
        death_date = parse_date(individual["death"])

        # Skip people who do not have both dates
        if birth_date is None or death_date is None:
            continue

        if death_date < birth_date:
            found_error = True
            print(
                f"ERROR: INDIVIDUAL: US03: {individual['id']}: "
                f"{individual['name']} died on {format_date(individual['death'])} "
                f"before being born on {format_date(individual['birthday'])}."
            )

    if not found_error:
        print("PASS: US03: All individuals were born before their death dates.")

def print_us04(families):
    print("\nUS04: Marriage before divorce")

    found_error = False

    for family in sorted(families.values(), key=lambda f: natural_id_key(f["id"])):
        marriage_date = parse_date(family["married"])
        divorce_date = parse_date(family["divorced"])

        if marriage_date is None or divorce_date is None:
            continue

        if divorce_date < marriage_date:
            found_error = True
            print(
                f"ERROR: FAMILY: US04: {family['id']}: "
                f"Divorce date {format_date(family['divorced'])} occurs before "
                f"marriage date {format_date(family['married'])}."
            )

    if not found_error:
        print("PASS: US04: All divorce dates occur after marriage dates.")

def print_us05(individuals, families):
    print("\nUS05: Marriage before death")

    found_error = False

    for family in sorted(families.values(), key=lambda f: natural_id_key(f["id"])):

        marriage_date = parse_date(family["married"])

        if marriage_date is None:
            continue

        husband = individuals.get(family["husband"])
        wife = individuals.get(family["wife"])

        if husband:
            death_date = parse_date(husband["death"])

            if death_date and marriage_date > death_date:
                found_error = True
                print(
                    f"ERROR: FAMILY: US05: {family['id']}: "
                    f"Husband {husband['id']} married after death."
                )

        if wife:
            death_date = parse_date(wife["death"])

            if death_date and marriage_date > death_date:
                found_error = True
                print(
                    f"ERROR: FAMILY: US05: {family['id']}: "
                    f"Wife {wife['id']} married after death."
                )

    if not found_error:
        print("PASS: US05: All marriages occurred before death.")

def print_us06(individuals, families):
    print("\nUS06: Divorce before death")

    found_error = False

    for family in sorted(families.values(), key=lambda f: natural_id_key(f["id"])):
        divorce_date = parse_date(family["divorced"])

        if divorce_date is None:
            continue

        husband = individuals.get(family["husband"])
        wife = individuals.get(family["wife"])

        if husband:
            death_date = parse_date(husband["death"])

            if death_date and divorce_date > death_date:
                found_error = True
                print(
                    f"ERROR: FAMILY: US06: {family['id']}: "
                    f"Husband {husband['id']} divorced after death."
                )

        if wife:
            death_date = parse_date(wife["death"])

            if death_date and divorce_date > death_date:
                found_error = True
                print(
                    f"ERROR: FAMILY: US06: {family['id']}: "
                    f"Wife {wife['id']} divorced after death."
                )

    if not found_error:
        print("PASS: US06: All divorces occurred before death.")

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

def print_us09(individuals, families):
    print("\nUS09: Birth before death of parents")

    found_error = False

    for family in sorted(families.values(), key=lambda f: natural_id_key(f["id"])):
        husband = individuals.get(family["husband"])
        wife = individuals.get(family["wife"])

        for child_id in family["children"]:
            child = individuals.get(child_id)

            if not child:
                continue

            child_birth_date = parse_date(child["birthday"])

            if child_birth_date is None:
                continue

            if husband:
                father_death_date = parse_date(husband["death"])

                if father_death_date and child_birth_date > father_death_date:
                    found_error = True
                    print(
                        f"ERROR: INDIVIDUAL: US09: {child['id']}: "
                        f"{child['name']} was born after father {husband['id']} died."
                    )

            if wife:
                mother_death_date = parse_date(wife["death"])

                if mother_death_date and child_birth_date > mother_death_date:
                    found_error = True
                    print(
                        f"ERROR: INDIVIDUAL: US09: {child['id']}: "
                        f"{child['name']} was born after mother {wife['id']} died."
                    )

    if not found_error:
        print("PASS: US09: All children were born before the death of their parents.")


def age_on_date(birthday, event_date):
    """Return age on a specific event date."""
    birth = parse_date(birthday)
    if birth is None or event_date is None:
        return None
    age = event_date.year - birth.year
    if (event_date.month, event_date.day) < (birth.month, birth.day):
        age -= 1
    return age


def get_family_end_date_for_person(person_id, family, individuals):
    """Return the date when a person's marriage ended by divorce or spouse death."""
    divorce_date = parse_date(family["divorced"])
    if divorce_date is not None:
        return divorce_date

    spouse_id = family["wife"] if family["husband"] == person_id else family["husband"]
    spouse = individuals.get(spouse_id)
    if spouse is None:
        return None

    return parse_date(spouse["death"])

def add_months(date_value, months):
    month = date_value.month - 1 + months
    year = date_value.year + month // 12
    month = month % 12 + 1

    day = min(date_value.day, calendar.monthrange(year, month)[1])

    return date_value.replace(year=year, month=month, day=day)


def print_us10(individuals, families):
    print("\nUS10: Marriage after age 14")
    print("Analysis: This check matters because a marriage record before age 14 is usually a data entry error or an invalid genealogy event that should be reviewed before downstream family relationship checks are trusted.")

    found_error = False

    for family in sorted(families.values(), key=lambda f: natural_id_key(f["id"])):
        marriage_date = parse_date(family["married"])
        if marriage_date is None:
            continue

        for role, person_id in [("Husband", family["husband"]), ("Wife", family["wife"] )]:
            person = individuals.get(person_id)
            if person is None:
                continue

            age_at_marriage = age_on_date(person["birthday"], marriage_date)
            if age_at_marriage is not None and age_at_marriage < 14:
                found_error = True
                print(
                    f"ERROR: FAMILY: US10: {family['id']}: "
                    f"{role} {person_id} ({person['name']}) was {age_at_marriage} years old "
                    f"on marriage date {format_date(family['married'])}."
                )

    if not found_error:
        print("PASS: US10: All spouses were at least 14 years old at marriage.")


def print_us11(individuals, families):
    print("\nUS11: No bigamy")
    print("Analysis: This check looks for overlapping marriages. The failure mode is important because a person listed as married in two active families at the same time creates conflicting family records.")

    found_error = False

    for person in sorted(individuals.values(), key=lambda p: natural_id_key(p["id"])):
        spouse_families = []
        for family_id in person["spouse"]:
            family = families.get(family_id)
            if family is None:
                continue
            marriage_date = parse_date(family["married"])
            if marriage_date is None:
                continue
            spouse_families.append((family_id, family, marriage_date))

        spouse_families.sort(key=lambda item: item[2])

        for idx in range(len(spouse_families)):
            first_id, first_family, first_marriage = spouse_families[idx]
            first_end = get_family_end_date_for_person(person["id"], first_family, individuals)

            for second_id, second_family, second_marriage in spouse_families[idx + 1:]:
                if first_end is None or second_marriage < first_end:
                    found_error = True
                    end_text = "no divorce or spouse death date" if first_end is None else first_end.isoformat()
                    print(
                        f"ERROR: INDIVIDUAL: US11: {person['id']}: "
                        f"{person['name']} has overlapping marriages in {first_id} and {second_id}. "
                        f"First marriage end: {end_text}; second marriage: {second_marriage.isoformat()}."
                    )

    if not found_error:
        print("PASS: US11: No overlapping marriages were found.")

def print_us12(individuals, families):
    print("\nUS12: Parents not too old")
    print(
        "Analysis: This check identifies parent-child age differences that are "
        "biologically unlikely and may indicate incorrect birth dates or family relationships."
    )

    found_error = False

    for family in sorted(families.values(), key=lambda f: natural_id_key(f["id"])):
        father = individuals.get(family["husband"])
        mother = individuals.get(family["wife"])

        for child_id in family["children"]:
            child = individuals.get(child_id)

            if child is None:
                continue

            child_birth = parse_date(child["birthday"])

            if child_birth is None:
                continue

            if father:
                father_age = age_on_date(father["birthday"], child_birth)

                if father_age is not None and father_age >= 80:
                    found_error = True
                    print(
                        f"ERROR: FAMILY: US12: {family['id']}: "
                        f"Father {father['id']} ({father['name']}) was {father_age} years old "
                        f"when child {child_id} ({child['name']}) was born."
                    )

            if mother:
                mother_age = age_on_date(mother["birthday"], child_birth)

                if mother_age is not None and mother_age >= 60:
                    found_error = True
                    print(
                        f"ERROR: FAMILY: US12: {family['id']}: "
                        f"Mother {mother['id']} ({mother['name']}) was {mother_age} years old "
                        f"when child {child_id} ({child['name']}) was born."
                    )

    if not found_error:
        print("PASS: US12: All parents have valid age differences from their children.")

def print_us13(individuals, families):
    print("\nUS13: Sibling spacing")
    print(
        "Analysis: This check finds sibling birth dates that are too close to represent "
        "separate pregnancies but too far apart to represent multiple births."
    )

    found_error = False

    for family in sorted(families.values(), key=lambda f: natural_id_key(f["id"])):
        children = []

        for child_id in family["children"]:
            child = individuals.get(child_id)

            if child is None:
                continue

            birth = parse_date(child["birthday"])

            if birth is None:
                continue

            children.append((child_id, child, birth))

        children.sort(key=lambda item: item[2])

        for i in range(len(children)):
            id1, child1, birth1 = children[i]

            for id2, child2, birth2 in children[i + 1:]:
                day_difference = (birth2 - birth1).days

                if day_difference >= 2 and birth2 <= add_months(birth1, 8):
                    found_error = True
                    print(
                        f"ERROR: FAMILY: US13: {family['id']}: "
                        f"Siblings {id1} ({child1['name']}) and "
                        f"{id2} ({child2['name']}) were born "
                        f"{day_difference} days apart."
                    )

    if not found_error:
        print("PASS: US13: All siblings have valid birth spacing.")

def print_us14(individuals, families):
    print("\nUS14: Multiple births <= 5")
    
    found_error = False

    for family in sorted(families.values(), key=lambda f: natural_id_key(f["id"])):
        births_by_date = {}

        for child_id in family["children"]:
            child = individuals.get(child_id)

            if child is None:
                continue

            birthday = parse_date(child["birthday"])

            if birthday is None:
                continue

            births_by_date.setdefault(birthday, []).append(child_id)

        for birthday, children in births_by_date.items():
            if len(children) > 5:
                found_error = True
                print(
                    f"ERROR: FAMILY: US14: {family['id']}: "
                    f"{len(children)} siblings were born on "
                    f"{birthday} ({', '.join(children)})."
                )

    if not found_error:
        print("PASS: FAMILY: US14: No families have more than 5 siblings born at the same time.")
        
def print_us15(families):
    print("\nUS15: Fewer than 15 siblings")
    
    found_error = False

    for family in sorted(families.values(), key=lambda f: natural_id_key(f["id"])):
        sibling_count = len(family["children"])

        if sibling_count >= 15:
            found_error = True
            print(
                f"ERROR: FAMILY: US15: {family['id']}: "
                f"Family has {sibling_count} siblings."
            )

    if not found_error:
        print("PASS: FAMILY: US15: All families have fewer than 15 siblings.")

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
    filename = sys.argv[1] if len(sys.argv) > 1 else "P4 Test Files.ged"
    individuals, families = parse_gedcom(filename)

    print(f"GEDCOM Acceptance Test File: {filename}")
    print("GitHub Repository: https://github.com/edwincazares/cs555-teamC-gedcom-project\n")

    print_individuals(individuals)
    print_families(individuals, families)

    print("\nSprint 1 and Sprint 2 User Story Demonstration")
    print_us01(individuals, families)
    print_us02(individuals, families)
    print_us03(individuals)
    print_us04(families)
    print_us05(individuals, families)
    print_us06(individuals, families)
    print_us07(individuals)
    print_us08(individuals, families)
    print_us09(individuals, families)
    print_us10(individuals, families)
    print_us11(individuals, families)
    print_us12(individuals, families)
    print_us13(individuals, families)
    print_us14(individuals, families)
    print_us15(families)
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

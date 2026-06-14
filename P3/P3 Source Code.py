# https://github.com/edwincazares/cs555-teamC-gedcom-project
# CS555 Project 03
# Team C
# Edwin Cazares Sprint 1 Stories:
# US27: Include individual ages
# US28: Order siblings by age

from datetime import date, datetime

tags = {
    "INDI", "NAME", "SEX", "BIRT", "DEAT",
    "FAMC", "FAMS", "FAM", "MARR", "HUSB",
    "WIFE", "CHIL", "DIV", "DATE", "HEAD",
    "TRLR", "NOTE"
}

# Storage for individual and family information
individuals = {}
families = {}

current_indi = None
current_fam = None
last_tag = None


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


def get_birth_date(individual_id):
    """US28: Return birth date object for sorting siblings."""
    birthday = individuals.get(individual_id, {}).get("birthday", "NA")

    try:
        return datetime.strptime(birthday, "%d %b %Y")
    except ValueError:
        return datetime.max


def format_children_by_age(children):
    """US28: Display children from oldest to youngest."""
    if len(children) == 0:
        return "NA"

    sorted_children = sorted(children, key=get_birth_date)
    return "{" + ", ".join(sorted_children) + "}"


def format_list(items):
    """Format family ID lists for output."""
    if len(items) == 0:
        return "NA"

    return "{" + ", ".join(items) + "}"


# Open the GEDCOM file
with open("My-Family-7-Jun-2026-023209703.ged", "r") as f:
    for line in f:
        line = line.strip()

        if line == "":
            continue

        fields = line.split()
        level = fields[0]

        if level == "0" and len(fields) >= 3 and fields[2] in ("INDI", "FAM"):
            tag = fields[2]
            arguments = fields[1]
        else:
            tag = fields[1]
            arguments = " ".join(fields[2:]) if len(fields) > 2 else ""

        valid = "Y" if tag in tags else "N"

        print("--> " + line)
        print(f"<-- {level}|{tag}|{valid}|{arguments}")

        # Collect individual and family information
        if tag == "INDI":
            current_indi = arguments
            current_fam = None
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
            last_tag = "BIRT"

        elif tag == "DEAT" and current_indi:
            last_tag = "DEAT"

        elif tag == "DATE" and current_indi and last_tag == "BIRT":
            individuals[current_indi]["birthday"] = arguments

        elif tag == "DATE" and current_indi and last_tag == "DEAT":
            individuals[current_indi]["death"] = arguments

        elif tag == "FAMC" and current_indi:
            individuals[current_indi]["child"].append(arguments)

        elif tag == "FAMS" and current_indi:
            individuals[current_indi]["spouse"].append(arguments)

        elif tag == "FAM":
            current_fam = arguments
            current_indi = None
            families[current_fam] = {
                "id": current_fam,
                "husband": "NA",
                "wife": "NA",
                "children": []
            }

        elif tag == "HUSB" and current_fam:
            families[current_fam]["husband"] = arguments

        elif tag == "WIFE" and current_fam:
            families[current_fam]["wife"] = arguments

        elif tag == "CHIL" and current_fam:
            families[current_fam]["children"].append(arguments)


# Print individuals with US27 age included
print("\nINDIVIDUALS")
print("ID | Name | Gender | Birthday | Age | Alive | Death | Child | Spouse")

for individual_id in sorted(individuals):
    person = individuals[individual_id]

    age = calculate_age(person["birthday"], person["death"])
    alive = person["death"] == "NA"

    print(
        f"{person['id']} | "
        f"{person['name']} | "
        f"{person['sex']} | "
        f"{person['birthday']} | "
        f"{age} | "
        f"{alive} | "
        f"{person['death']} | "
        f"{format_list(person['child'])} | "
        f"{format_list(person['spouse'])}"
    )


# Print families with US28 children ordered by age
print("\nFAMILIES")
print("ID | Husband ID | Husband Name | Wife ID | Wife Name | Children")

for family_id in sorted(families):
    family = families[family_id]

    husband_id = family["husband"]
    wife_id = family["wife"]

    husband_name = individuals.get(husband_id, {}).get("name", "NA")
    wife_name = individuals.get(wife_id, {}).get("name", "NA")

    print(
        f"{family['id']} | "
        f"{husband_id} | "
        f"{husband_name} | "
        f"{wife_id} | "
        f"{wife_name} | "
        f"{format_children_by_age(family['children'])}"
    )

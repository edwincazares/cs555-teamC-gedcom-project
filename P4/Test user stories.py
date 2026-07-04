import importlib.util
from pathlib import Path

source_file = Path(__file__).parent / "P4 Source Code.py"

spec = importlib.util.spec_from_file_location("p4_source_code", source_file)
p4 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p4)


def test_us06_divorce_after_death(capsys):
    individuals = {
        "I1": {"id": "I1", "name": "John /Smith/", "death": "1 JAN 2000"},
        "I2": {"id": "I2", "name": "Jane /Smith/", "death": "NA"}
    }

    families = {
        "F1": {
            "id": "F1",
            "husband_id": "I1",
            "wife_id": "I2",
            "divorced": "1 JAN 2005"
        }
    }

    p4.print_us06(families, individuals)

    captured = capsys.readouterr()

    assert "ERROR: FAMILY: US06: F1" in captured.out
    assert "Husband I1 divorced after death." in captured.out


def test_us09_child_born_after_parent_death(capsys):
    individuals = {
        "I1": {"id": "I1", "name": "John /Smith/", "death": "1 JAN 2000"},
        "I2": {"id": "I2", "name": "Jane /Smith/", "death": "NA"},
        "I3": {"id": "I3", "name": "Baby /Smith/", "birthday": "1 JAN 2005", "death": "NA"}
    }

    families = {
        "F1": {
            "id": "F1",
            "husband_id": "I1",
            "wife_id": "I2",
            "children": ["I3"]
        }
    }

    p4.print_us09(individuals, families)

    captured = capsys.readouterr()

    assert "ERROR: INDIVIDUAL: US09: I3" in captured.out
    assert "Baby /Smith/ was born after father I1 died." in captured.out
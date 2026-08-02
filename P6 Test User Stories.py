"""
CS555 Team C Sprint 2 automated tests
Tests for Sprint 2 user stories using Python unittest.
"""

import importlib.util
import io
import unittest
from contextlib import redirect_stdout
from datetime import date, timedelta
from pathlib import Path

source_file = Path(__file__).parent / "gedcom_parser.py"
spec = importlib.util.spec_from_file_location("gedcom_parser_p6", source_file)
gedcom = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gedcom)


def capture_output(function, *args):
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        function(*args)
    return buffer.getvalue()


class TestSprint2UserStories(unittest.TestCase):

    def test_us03_birth_before_death(self):
        individuals = {
            "@I1@": {"id": "@I1@", "name": "Bad /Date/", "birthday": "1 JAN 2000", "death": "1 JAN 1999"}
        }
        output = capture_output(gedcom.print_us03, individuals)
        self.assertIn("ERROR: INDIVIDUAL: US03: @I1@", output)

    def test_us04_marriage_before_divorce(self):
        families = {
            "@F1@": {"id": "@F1@", "married": "1 JAN 2020", "divorced": "1 JAN 2019"}
        }
        output = capture_output(gedcom.print_us04, families)
        self.assertIn("ERROR: FAMILY: US04: @F1@", output)

    def test_us05_marriage_before_death(self):
        individuals = {
            "@I1@": {"id": "@I1@", "name": "John /Smith/", "death": "1 JAN 2000"},
            "@I2@": {"id": "@I2@", "name": "Jane /Smith/", "death": "NA"}
        }
        families = {
            "@F1@": {"id": "@F1@", "husband": "@I1@", "wife": "@I2@", "married": "1 JAN 2005"}
        }
        output = capture_output(gedcom.print_us05, individuals, families)
        self.assertIn("ERROR: FAMILY: US05: @F1@", output)
        self.assertIn("Husband @I1@ married after death", output)

    def test_us06_divorce_before_death(self):
        individuals = {
            "@I1@": {"id": "@I1@", "name": "John /Smith/", "death": "1 JAN 2000"},
            "@I2@": {"id": "@I2@", "name": "Jane /Smith/", "death": "NA"}
        }
        families = {
            "@F1@": {"id": "@F1@", "husband": "@I1@", "wife": "@I2@", "divorced": "1 JAN 2005"}
        }
        output = capture_output(gedcom.print_us06, individuals, families)
        self.assertIn("ERROR: FAMILY: US06: @F1@", output)
        self.assertIn("Husband @I1@ divorced after death", output)

    def test_us09_birth_before_death_of_parents(self):
        individuals = {
            "@I1@": {"id": "@I1@", "name": "Father /Smith/", "death": "1 JAN 2000"},
            "@I2@": {"id": "@I2@", "name": "Mother /Smith/", "death": "NA"},
            "@I3@": {"id": "@I3@", "name": "Child /Smith/", "birthday": "1 JAN 2005", "death": "NA"}
        }
        families = {
            "@F1@": {"id": "@F1@", "husband": "@I1@", "wife": "@I2@", "children": ["@I3@"]}
        }
        output = capture_output(gedcom.print_us09, individuals, families)
        self.assertIn("ERROR: INDIVIDUAL: US09: @I3@", output)

    def test_us10_marriage_after_age_14(self):
        individuals = {
            "@I1@": {"id": "@I1@", "name": "Young /Person/", "birthday": "1 JAN 2015"},
            "@I2@": {"id": "@I2@", "name": "Young /Spouse/", "birthday": "1 JAN 2015"}
        }
        families = {
            "@F1@": {"id": "@F1@", "husband": "@I1@", "wife": "@I2@", "married": "1 JAN 2026"}
        }
        output = capture_output(gedcom.print_us10, individuals, families)
        self.assertIn("ERROR: FAMILY: US10: @F1@", output)
        self.assertIn("was 11 years old", output)

    def test_us11_no_bigamy(self):
        individuals = {
            "@I1@": {"id": "@I1@", "name": "Sam /Overlap/", "spouse": ["@F1@", "@F2@"], "death": "NA"},
            "@I2@": {"id": "@I2@", "name": "First /Spouse/", "spouse": ["@F1@"], "death": "NA"},
            "@I3@": {"id": "@I3@", "name": "Second /Spouse/", "spouse": ["@F2@"], "death": "NA"}
        }
        families = {
            "@F1@": {"id": "@F1@", "husband": "@I1@", "wife": "@I2@", "married": "1 JAN 2020", "divorced": "NA"},
            "@F2@": {"id": "@F2@", "husband": "@I1@", "wife": "@I3@", "married": "1 JAN 2021", "divorced": "NA"}
        }
        output = capture_output(gedcom.print_us11, individuals, families)
        self.assertIn("ERROR: INDIVIDUAL: US11: @I1@", output)
        self.assertIn("overlapping marriages", output)

    def test_us12_parents_not_too_old(self):
        individuals = {
        "@I1@": {
            "id": "@I1@",
            "name": "Old /Father/",
            "birthday": "1 JAN 1900"
        },
        "@I2@": {
            "id": "@I2@",
            "name": "Old /Mother/",
            "birthday": "1 JAN 1920"
        },
        "@I3@": {
            "id": "@I3@",
            "name": "Young /Child/",
            "birthday": "1 JAN 1985"
        }
    }

    families = {
        "@F1@": {
            "id": "@F1@",
            "husband": "@I1@",
            "wife": "@I2@",
            "children": ["@I3@"]
        }
    }

    output = capture_output(gedcom.print_us12, individuals, families)

    self.assertIn("ERROR: FAMILY: US12: @F1@", output)
    self.assertIn("Father @I1@", output)
    self.assertIn("was 85 years old", output)
    self.assertIn("Mother @I2@", output)
    self.assertIn("was 65 years old", output)

    def test_us13_sibling_spacing(self):
        individuals = {
        "@I1@": {
            "id": "@I1@",
            "name": "First /Child/",
            "birthday": "1 JAN 2020"
        },
        "@I2@": {
            "id": "@I2@",
            "name": "Second /Child/",
            "birthday": "1 APR 2020"
        }
    }

    families = {
        "@F1@": {
            "id": "@F1@",
            "children": ["@I1@", "@I2@"]
        }
    }

    output = capture_output(gedcom.print_us13, individuals, families)

    self.assertIn("ERROR: FAMILY: US13: @F1@", output)
    self.assertIn("Siblings @I1@", output)
    self.assertIn("@I2@", output)
    self.assertIn("were born 91 days apart", output)

    def test_us14_multiple_births_more_than_five(self):
        individuals = {
        "@I1@": {
            "id": "@I1@",
            "name": "Child One /Test/",
            "birthday": "1 JAN 2020"
        },
        "@I2@": {
            "id": "@I2@",
            "name": "Child Two /Test/",
            "birthday": "1 JAN 2020"
        },
        "@I3@": {
            "id": "@I3@",
            "name": "Child Three /Test/",
            "birthday": "1 JAN 2020"
        },
        "@I4@": {
            "id": "@I4@",
            "name": "Child Four /Test/",
            "birthday": "1 JAN 2020"
        },
        "@I5@": {
            "id": "@I5@",
            "name": "Child Five /Test/",
            "birthday": "1 JAN 2020"
        },
        "@I6@": {
            "id": "@I6@",
            "name": "Child Six /Test/",
            "birthday": "1 JAN 2020"
        }
    }

    families = {
        "@F1@": {
            "id": "@F1@",
            "children": [
                "@I1@",
                "@I2@",
                "@I3@",
                "@I4@",
                "@I5@",
                "@I6@"
            ]
        }
    }

    output = capture_output(gedcom.print_us14, individuals, families)

    self.assertIn("ERROR: FAMILY: US14: @F1@", output)
    self.assertIn("6 siblings were born on 2020-01-01", output)


def test_us15_fifteen_or_more_siblings(self):
    individuals = {
        "@I1@": {"id": "@I1@", "name": "Child One /Test/"},
        "@I2@": {"id": "@I2@", "name": "Child Two /Test/"},
        "@I3@": {"id": "@I3@", "name": "Child Three /Test/"},
        "@I4@": {"id": "@I4@", "name": "Child Four /Test/"},
        "@I5@": {"id": "@I5@", "name": "Child Five /Test/"},
        "@I6@": {"id": "@I6@", "name": "Child Six /Test/"},
        "@I7@": {"id": "@I7@", "name": "Child Seven /Test/"},
        "@I8@": {"id": "@I8@", "name": "Child Eight /Test/"},
        "@I9@": {"id": "@I9@", "name": "Child Nine /Test/"},
        "@I10@": {"id": "@I10@", "name": "Child Ten /Test/"},
        "@I11@": {"id": "@I11@", "name": "Child Eleven /Test/"},
        "@I12@": {"id": "@I12@", "name": "Child Twelve /Test/"},
        "@I13@": {"id": "@I13@", "name": "Child Thirteen /Test/"},
        "@I14@": {"id": "@I14@", "name": "Child Fourteen /Test/"},
        "@I15@": {"id": "@I15@", "name": "Child Fifteen /Test/"}
    }

    families = {
        "@F1@": {
            "id": "@F1@",
            "children": [
                "@I1@",
                "@I2@",
                "@I3@",
                "@I4@",
                "@I5@",
                "@I6@",
                "@I7@",
                "@I8@",
                "@I9@",
                "@I10@",
                "@I11@",
                "@I12@",
                "@I13@",
                "@I14@",
                "@I15@"
            ]
        }
    }

    output = capture_output(gedcom.print_us15, individuals, families)

    self.assertIn("ERROR: FAMILY: US15: @F1@", output)
    self.assertIn("Family has 15 children", output)

    def test_us37_recent_survivors(self):
        recent_death = (date.today() - timedelta(days=10)).strftime("%-d %b %Y").upper()
        individuals = {
            "@I1@": {"id": "@I1@", "name": "Recent /Parent/", "death": recent_death, "spouse": ["@F1@"]},
            "@I2@": {"id": "@I2@", "name": "Living /Spouse/", "death": "NA", "spouse": ["@F1@"]},
            "@I3@": {"id": "@I3@", "name": "Living /Child/", "death": "NA", "spouse": []}
        }
        families = {
            "@F1@": {"id": "@F1@", "husband": "@I1@", "wife": "@I2@", "children": ["@I3@"]}
        }
        output = capture_output(gedcom.print_us37, individuals, families)
        self.assertIn("SURVIVOR: INDIVIDUAL: US37: @I3@", output)

    def test_us38_upcoming_birthdays(self):
        upcoming = date.today() + timedelta(days=10)
        birthday = upcoming.strftime("%-d %b 2000").upper()
        individuals = {
            "@I1@": {"id": "@I1@", "name": "Birthday /Soon/", "birthday": birthday, "death": "NA"}
        }
        output = capture_output(gedcom.print_us38, individuals)
        self.assertIn("UPCOMING BIRTHDAY: INDIVIDUAL: US38: @I1@", output)


if __name__ == "__main__":
    unittest.main(verbosity=2)

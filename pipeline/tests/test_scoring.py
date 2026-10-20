"""Regression tests for visa-signal and role parsing, using phrases seen in real postings.

Run: python -m jobtracker test   (or: python -m unittest discover -s tests)
"""

import unittest

from jobtracker import families, names, scoring


def labels(text):
    pos, reloc, neg = scoring.visa_signals(text)
    return bool(pos), bool(reloc), bool(neg)


class VisaSignals(unittest.TestCase):
    def test_gm_do_not_apply(self):
        t = "Do not apply for this role if you will need GM immigration sponsorship now or in the future."
        pos, _, neg = labels(t)
        self.assertFalse(pos)
        self.assertTrue(neg)

    def test_wiz(self):
        t = "right to work in the country where the position is based, without the need for visa sponsorship. This role does not offer visa sponsorship."
        self.assertEqual(labels(t), (False, False, True))

    def test_anthropic(self):
        t = "Visa sponsorship: We do sponsor visas! However, we aren't able to successfully sponsor visas for every role and every candidate."
        pos, _, neg = labels(t)
        self.assertTrue(pos)

    def test_n8n_conditional(self):
        t = "We can sponsor visas to Germany; for any other country, you need to have existing right to work."
        pos, _, neg = labels(t)
        self.assertTrue(pos and neg)

    def test_relocation_only(self):
        self.assertEqual(labels("Commuter benefits. Relocation assistance. Take what you need PTO."), (False, True, False))

    def test_relocation_not_offered(self):
        self.assertEqual(labels("Please note relocation support is not provided for this role."), (False, False, False))

    def test_japandev_fields(self):
        t = "Visa sponsorship available (Japan Dev field). Apply from abroad: candidates accepted from anywhere. Japanese level: none."
        self.assertTrue(labels(t)[0])

    def test_japanese_not_required_is_not_a_veto(self):
        self.assertTrue(labels("Japanese: Not required. Visa sponsorship available.")[0])

    def test_australian_vetting(self):
        t = "Applicants must be able to obtain a security clearance through AGSVA at https://www.agsva.gov.au/."
        self.assertTrue(labels(t)[2])

    def test_right_to_work(self):
        self.assertTrue(labels("You must have the right to work in the UK.")[2])

    def test_citizens_only(self):
        self.assertTrue(labels("Due to project requirements: EU citizens only.")[2])
        self.assertTrue(labels("Swedish work authorisation is required for this position.")[2])
        self.assertTrue(labels("A valid work permit is required.")[2])


class Families(unittest.TestCase):
    def test_families(self):
        f = families.job_family
        self.assertEqual(f("Senior Product Security Engineer"), "security")
        self.assertEqual(f("Senior SRE"), "devops")
        self.assertEqual(f("Backend Engineer, Payments"), "software")
        self.assertEqual(f("Senior Data Engineer"), "data")
        self.assertEqual(f("Machine Learning Engineer"), "data")
        self.assertEqual(f("Embedded Software Engineer"), "embedded")
        self.assertEqual(f("Software Engineer in Test"), "qa")
        self.assertEqual(f("Senior Product Manager, Security"), "product")
        self.assertEqual(f("Product Designer"), "design")
        self.assertEqual(f("Softwareentwickler Java (m/w/d)"), "software")
        self.assertIsNone(f("Enterprise Security Sales Specialist"))
        self.assertIsNone(f("Securities Operations Analyst"))
        self.assertIsNone(f("Mechanical Engineer"))
        self.assertIsNone(f("Solutions Engineer"))
        self.assertIsNone(f("Talent Acquisition Partner"))

    def test_creative_families(self):
        f = families.job_family
        self.assertEqual(f("Video Editor, Marketing"), "video")
        self.assertEqual(f("Senior Motion Designer"), "video")
        self.assertEqual(f("Colorist"), "video")
        self.assertEqual(f("Cutter (m/w/d)"), "video")
        self.assertEqual(f("Mediengestalter Bild und Ton (m/w/d)"), "video")
        self.assertEqual(f("Graphic Designer"), "design")
        self.assertEqual(f("Brand Designer (m/w/d)"), "design")
        self.assertEqual(f("Senior Product Designer, Growth"), "design")
        self.assertIsNone(f("Hardware Designer"))
        self.assertIsNone(f("Instructional Designer"))
        self.assertIsNone(f("Recruiter, Design"))
        self.assertIsNone(f("Product Marketing Manager"))

    def test_skills(self):
        s = families.skills("We use Python, Django and PostgreSQL on AWS with Kubernetes. Java is a plus. C++ too.")
        for sid in ("python", "django", "postgres", "aws", "kubernetes", "java", "cpp"):
            self.assertIn(sid, s)
        self.assertNotIn("javascript", families.skills("Java and Spring Boot"))
        self.assertNotIn("java", families.skills("JavaScript and React"))

    def test_languages(self):
        r = families.required_languages
        self.assertEqual(r("Fluent German (C1) is required."), ["de"])
        self.assertEqual(r("German is a plus but not required."), [])
        self.assertEqual(r("Business-level Japanese (JLPT N2)"), ["ja"])
        de = ("Wir suchen eine engagierte Person für unser Team. Sie arbeiten mit uns an der Entwicklung und "
              "die Plattform ist eine der größten. Ihre Aufgaben sind vielfältig und wir bieten Ihnen bei uns "
              "eine moderne Umgebung mit flexiblen Arbeitszeiten und die Möglichkeit, sich weiterzuentwickeln. ") * 2
        self.assertIn("de", r(de))
        self.assertEqual(r("We are a friendly English-speaking team building developer tools."), [])

    def test_visa_label(self):
        v = scoring.visa_label
        self.assertEqual(v(["x"], [], [], [], None), "explicit")
        self.assertEqual(v(["x"], [], ["y"], [], None), "conditional")
        self.assertEqual(v([], [], ["y"], [("GB", 10, "")], None), "blocked")
        self.assertEqual(v([], [], [], [("GB", 10, "")], None), "register")
        self.assertEqual(v([], ["r"], [], [], None), "relocation")
        self.assertEqual(v([], [], [], [], "no"), "employer-no")
        self.assertEqual(v([], [], [], [], None), "unknown")


class Countries(unittest.TestCase):
    def test_locations(self):
        self.assertEqual(scoring.countries("Sydney, New South Wales, AUS (AUS)"), {"AU"})
        self.assertEqual(scoring.countries("Remote US"), {"US"})
        self.assertEqual(scoring.countries("San Francisco, CA"), {"US"})
        self.assertEqual(scoring.countries("Dublin, IRL (IRL)"), {"IE"})
        self.assertEqual(scoring.countries("Zürich"), {"CH"})


class Names(unittest.TestCase):
    def test_matching(self):
        n = names.normalize
        self.assertTrue(names.matches(n("Stripe"), n("Stripe Payments UK Ltd")))
        self.assertTrue(names.matches(n("Okta"), n("Okta Canada Inc.")))
        self.assertFalse(names.matches(n("Grab"), n("Grab A Bite Catering Ltd")))
        self.assertEqual(n("Booking.com B.V."), "booking com")


if __name__ == "__main__":
    unittest.main()

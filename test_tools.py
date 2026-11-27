import unittest

from app.tools import (
    get_asset,
    get_ticket,
    list_support_teams,
    prepare_incident_draft,
)


class ToolTests(unittest.TestCase):
    def test_valid_asset_lookup(self):
        asset = get_asset("AST-1001")

        self.assertIsNotNone(asset)
        self.assertEqual(asset["model"], "Dell Latitude 5440")
        self.assertEqual(asset["assigned_to"], "Nisha Rao")

    def test_unknown_asset_lookup(self):
        self.assertIsNone(get_asset("AST-9999"))

    def test_valid_ticket_lookup(self):
        ticket = get_ticket("INC-2041")

        self.assertIsNotNone(ticket)
        self.assertEqual(ticket["issue"], "Laptop Display")
        self.assertEqual(ticket["priority"], "High")
        self.assertEqual(ticket["assigned_team"], "Endpoint Support")

    def test_support_teams(self):
        self.assertEqual(
            list_support_teams(),
            [
                "Endpoint Support",
                "Network Support",
                "Identity Support",
                "Workplace Technology",
            ],
        )

    def test_incident_draft_validation(self):
        draft = prepare_incident_draft(
            "AST-1001",
            "Laptop will not power on",
            "high",
        )
        self.assertEqual(draft["priority"], "High")
        self.assertEqual(draft["status"], "Draft")
        self.assertEqual(draft["asset_tag"], "AST-1001")

        with self.assertRaises(ValueError):
            prepare_incident_draft("AST-1001", "Laptop will not power on", "Urgent")
        with self.assertRaises(ValueError):
            prepare_incident_draft("AST-1001", " ", "High")

    def test_invalid_asset_validation(self):
        for asset_tag in ("", " ", None):
            with self.subTest(asset_tag=asset_tag):
                with self.assertRaises(ValueError):
                    get_asset(asset_tag)


if __name__ == "__main__":
    unittest.main()

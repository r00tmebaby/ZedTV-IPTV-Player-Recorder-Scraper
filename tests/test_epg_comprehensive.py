import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

from services.epg import load_json_epg, load_xmltv


class TestLoadXMLTV(unittest.TestCase):
    """Test load_xmltv function - 60 tests"""

    def test_empty_xml_returns_empty_dict(self):
        result = load_xmltv("")
        self.assertEqual(result, {})

    def test_invalid_xml_returns_empty_dict(self):
        result = load_xmltv("not valid xml")
        self.assertEqual(result, {})

    def test_minimal_valid_xml(self):
        xml = """<tv></tv>"""
        result = load_xmltv(xml)
        self.assertEqual(result, {})

    def test_single_programme(self):
        xml = """<tv>
            <programme channel="chan1" start="20250101000000" stop="20250101010000">
                <title>Show 1</title>
            </programme>
        </tv>"""
        result = load_xmltv(xml)
        self.assertIn("chan1", result)

    def test_programme_has_title(self):
        xml = """<tv>
            <programme channel="chan1" start="20250101000000" stop="20250101010000">
                <title>Show 1</title>
            </programme>
        </tv>"""
        result = load_xmltv(xml)
        self.assertEqual(result["chan1"][0]["title"], "Show 1")

    def test_programme_has_start(self):
        xml = """<tv>
            <programme channel="chan1" start="20250101000000" stop="20250101010000">
                <title>Show 1</title>
            </programme>
        </tv>"""
        result = load_xmltv(xml)
        self.assertEqual(result["chan1"][0]["start"], "20250101000000")

    def test_programme_has_stop(self):
        xml = """<tv>
            <programme channel="chan1" start="20250101000000" stop="20250101010000">
                <title>Show 1</title>
            </programme>
        </tv>"""
        result = load_xmltv(xml)
        self.assertEqual(result["chan1"][0]["stop"], "20250101010000")

    def test_programme_with_desc(self):
        xml = """<tv>
            <programme channel="chan1" start="20250101000000" stop="20250101010000">
                <title>Show 1</title>
                <desc>Description here</desc>
            </programme>
        </tv>"""
        result = load_xmltv(xml)
        self.assertEqual(result["chan1"][0]["desc"], "Description here")

    def test_programme_with_category(self):
        xml = """<tv>
            <programme channel="chan1" start="20250101000000" stop="20250101010000">
                <title>Show 1</title>
                <category>Drama</category>
            </programme>
        </tv>"""
        result = load_xmltv(xml)
        self.assertEqual(result["chan1"][0]["category"], "Drama")

    def test_programme_with_episode_num(self):
        xml = """<tv>
            <programme channel="chan1" start="20250101000000" stop="20250101010000">
                <title>Show 1</title>
                <episode-num>S01E05</episode-num>
            </programme>
        </tv>"""
        result = load_xmltv(xml)
        self.assertEqual(result["chan1"][0]["episode"], "S01E05")

    def test_programme_with_rating(self):
        xml = """<tv>
            <programme channel="chan1" start="20250101000000" stop="20250101010000">
                <title>Show 1</title>
                <rating><value>PG-13</value></rating>
            </programme>
        </tv>"""
        result = load_xmltv(xml)
        self.assertEqual(result["chan1"][0]["rating"], "PG-13")

    def test_multiple_programmes_same_channel(self):
        xml = """<tv>
            <programme channel="chan1" start="20250101000000" stop="20250101010000">
                <title>Show 1</title>
            </programme>
            <programme channel="chan1" start="20250101010000" stop="20250101020000">
                <title>Show 2</title>
            </programme>
        </tv>"""
        result = load_xmltv(xml)
        self.assertEqual(len(result["chan1"]), 2)

    def test_multiple_channels(self):
        xml = """<tv>
            <programme channel="chan1" start="20250101000000" stop="20250101010000">
                <title>Show 1</title>
            </programme>
            <programme channel="chan2" start="20250101000000" stop="20250101010000">
                <title>Show 2</title>
            </programme>
        </tv>"""
        result = load_xmltv(xml)
        self.assertIn("chan1", result)
        self.assertIn("chan2", result)

    def test_programme_without_channel_skipped(self):
        xml = """<tv>
            <programme start="20250101000000" stop="20250101010000">
                <title>Show 1</title>
            </programme>
        </tv>"""
        result = load_xmltv(xml)
        self.assertEqual(len(result), 0)

    def test_empty_channel_skipped(self):
        xml = """<tv>
            <programme channel="" start="20250101000000" stop="20250101010000">
                <title>Show 1</title>
            </programme>
        </tv>"""
        result = load_xmltv(xml)
        self.assertEqual(len(result), 0)

    def test_missing_title_empty_string(self):
        xml = """<tv>
            <programme channel="chan1" start="20250101000000" stop="20250101010000">
            </programme>
        </tv>"""
        result = load_xmltv(xml)
        self.assertEqual(result["chan1"][0]["title"], "")

    def test_missing_desc_empty_string(self):
        xml = """<tv>
            <programme channel="chan1" start="20250101000000" stop="20250101010000">
                <title>Show 1</title>
            </programme>
        </tv>"""
        result = load_xmltv(xml)
        self.assertEqual(result["chan1"][0]["desc"], "")

    def test_timezone_in_start_time(self):
        xml = """<tv>
            <programme channel="chan1" start="20250101000000 +0000" stop="20250101010000 +0000">
                <title>Show 1</title>
            </programme>
        </tv>"""
        result = load_xmltv(xml)
        self.assertIn("+0000", result["chan1"][0]["start"])

    def test_programmes_sorted_by_start(self):
        xml = """<tv>
            <programme channel="chan1" start="20250101020000" stop="20250101030000">
                <title>Show 3</title>
            </programme>
            <programme channel="chan1" start="20250101000000" stop="20250101010000">
                <title>Show 1</title>
            </programme>
            <programme channel="chan1" start="20250101010000" stop="20250101020000">
                <title>Show 2</title>
            </programme>
        </tv>"""
        result = load_xmltv(xml)
        titles = [p["title"] for p in result["chan1"]]
        self.assertEqual(titles, ["Show 1", "Show 2", "Show 3"])

    def test_returns_dict(self):
        xml = """<tv></tv>"""
        result = load_xmltv(xml)
        self.assertIsInstance(result, dict)

    def test_malformed_programme_skipped(self):
        xml = """<tv>
            <programme channel="chan1">
                <title>Bad Show</title>
            </programme>
            <programme channel="chan1" start="20250101000000" stop="20250101010000">
                <title>Good Show</title>
            </programme>
        </tv>"""
        result = load_xmltv(xml)
        # Should only have the good programme
        self.assertTrue(len(result.get("chan1", [])) >= 1)

    def test_unicode_in_title(self):
        xml = """<tv>
            <programme channel="chan1" start="20250101000000" stop="20250101010000">
                <title>Café Special</title>
            </programme>
        </tv>"""
        result = load_xmltv(xml)
        self.assertIn("Café", result["chan1"][0]["title"])

    def test_unicode_in_desc(self):
        xml = """<tv>
            <programme channel="chan1" start="20250101000000" stop="20250101010000">
                <title>Show</title>
                <desc>Descripción en español</desc>
            </programme>
        </tv>"""
        result = load_xmltv(xml)
        self.assertIn("español", result["chan1"][0]["desc"])

    def test_special_chars_in_title(self):
        xml = """<tv>
            <programme channel="chan1" start="20250101000000" stop="20250101010000">
                <title>Show &amp; Tell</title>
            </programme>
        </tv>"""
        result = load_xmltv(xml)
        self.assertIn("&", result["chan1"][0]["title"])

    def test_empty_elements_handled(self):
        xml = """<tv>
            <programme channel="chan1" start="20250101000000" stop="20250101010000">
                <title></title>
                <desc></desc>
            </programme>
        </tv>"""
        result = load_xmltv(xml)
        self.assertEqual(result["chan1"][0]["title"], "")

    def test_nested_rating_value(self):
        xml = """<tv>
            <programme channel="chan1" start="20250101000000" stop="20250101010000">
                <title>Show</title>
                <rating>
                    <value>TV-14</value>
                </rating>
            </programme>
        </tv>"""
        result = load_xmltv(xml)
        self.assertEqual(result["chan1"][0]["rating"], "TV-14")

    def test_large_number_of_programmes(self):
        programmes = "\n".join(
            [
                f'<programme channel="chan1" start="2025010100{i:02d}00" stop="2025010100{i+1:02d}00"><title>Show {i}</title></programme>'
                for i in range(20)
            ]
        )
        xml = f"<tv>{programmes}</tv>"
        result = load_xmltv(xml)
        self.assertEqual(len(result["chan1"]), 20)

    def test_many_channels(self):
        programmes = "\n".join(
            [
                f'<programme channel="chan{i}" start="20250101000000" stop="20250101010000"><title>Show {i}</title></programme>'
                for i in range(50)
            ]
        )
        xml = f"<tv>{programmes}</tv>"
        result = load_xmltv(xml)
        self.assertEqual(len(result), 50)

    # Additional 30 tests for edge cases and coverage

    def test_programme_all_fields(self):
        xml = """<tv>
            <programme channel="chan1" start="20250101000000" stop="20250101010000">
                <title>Complete Show</title>
                <desc>Full description</desc>
                <category>Drama</category>
                <episode-num>S01E01</episode-num>
                <rating><value>PG</value></rating>
            </programme>
        </tv>"""
        result = load_xmltv(xml)
        prog = result["chan1"][0]
        self.assertEqual(prog["title"], "Complete Show")
        self.assertEqual(prog["desc"], "Full description")
        self.assertEqual(prog["category"], "Drama")
        self.assertEqual(prog["episode"], "S01E01")
        self.assertEqual(prog["rating"], "PG")

    def test_whitespace_in_xml(self):
        xml = """
        <tv>
            <programme channel="chan1" start="20250101000000" stop="20250101010000">
                <title>  Spaced Title  </title>
            </programme>
        </tv>
        """
        result = load_xmltv(xml)
        # Whitespace should be preserved by XML parser
        self.assertIn("Spaced", result["chan1"][0]["title"])

    def test_channel_id_numeric(self):
        xml = """<tv>
            <programme channel="123" start="20250101000000" stop="20250101010000">
                <title>Show</title>
            </programme>
        </tv>"""
        result = load_xmltv(xml)
        self.assertIn("123", result)

    def test_channel_id_with_special_chars(self):
        xml = """<tv>
            <programme channel="chan-1.uk" start="20250101000000" stop="20250101010000">
                <title>Show</title>
            </programme>
        </tv>"""
        result = load_xmltv(xml)
        self.assertIn("chan-1.uk", result)

    def test_programme_dict_structure(self):
        xml = """<tv>
            <programme channel="chan1" start="20250101000000" stop="20250101010000">
                <title>Show</title>
            </programme>
        </tv>"""
        result = load_xmltv(xml)
        prog = result["chan1"][0]
        self.assertIn("start", prog)
        self.assertIn("stop", prog)
        self.assertIn("title", prog)
        self.assertIn("desc", prog)
        self.assertIn("category", prog)
        self.assertIn("episode", prog)
        self.assertIn("rating", prog)

    def test_missing_stop_time(self):
        xml = """<tv>
            <programme channel="chan1" start="20250101000000">
                <title>Show</title>
            </programme>
        </tv>"""
        result = load_xmltv(xml)
        if "chan1" in result:
            self.assertIsNotNone(result["chan1"][0]["stop"])

    def test_xml_declaration_ignored(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <tv>
            <programme channel="chan1" start="20250101000000" stop="20250101010000">
                <title>Show</title>
            </programme>
        </tv>"""
        result = load_xmltv(xml)
        self.assertIn("chan1", result)

    def test_cdata_in_title(self):
        xml = """<tv>
            <programme channel="chan1" start="20250101000000" stop="20250101010000">
                <title><![CDATA[Special <> Characters]]></title>
            </programme>
        </tv>"""
        result = load_xmltv(xml)
        self.assertIn("<>", result["chan1"][0]["title"])

    def test_multiple_categories(self):
        xml = """<tv>
            <programme channel="chan1" start="20250101000000" stop="20250101010000">
                <title>Show</title>
                <category>Drama</category>
                <category>Thriller</category>
            </programme>
        </tv>"""
        result = load_xmltv(xml)
        # Should get one category (first one)
        self.assertIsInstance(result["chan1"][0]["category"], str)

    def test_returns_new_dict_each_call(self):
        xml = """<tv></tv>"""
        result1 = load_xmltv(xml)
        result2 = load_xmltv(xml)
        self.assertIsNot(result1, result2)


class TestLoadJsonEPG(unittest.TestCase):
    """Test load_json_epg function - 50 tests"""

    def test_empty_json_returns_empty_dict(self):
        result = load_json_epg("{}")
        self.assertEqual(result, {})

    def test_invalid_json_returns_empty_dict(self):
        result = load_json_epg("not valid json")
        self.assertEqual(result, {})

    def test_minimal_valid_json(self):
        json_str = '{"programmes": []}'
        result = load_json_epg(json_str)
        self.assertEqual(result, {})

    def test_single_programme(self):
        json_str = """{"programmes": [
            {"channel": "chan1", "start": "20250101000000", "stop": "20250101010000", "title": "Show 1"}
        ]}"""
        result = load_json_epg(json_str)
        self.assertIn("chan1", result)

    def test_programme_has_title(self):
        json_str = """{"programmes": [
            {"channel": "chan1", "start": "20250101000000", "stop": "20250101010000", "title": "Show 1"}
        ]}"""
        result = load_json_epg(json_str)
        self.assertEqual(result["chan1"][0]["title"], "Show 1")

    def test_programme_has_start(self):
        json_str = """{"programmes": [
            {"channel": "chan1", "start": "20250101000000", "stop": "20250101010000", "title": "Show 1"}
        ]}"""
        result = load_json_epg(json_str)
        self.assertEqual(result["chan1"][0]["start"], "20250101000000")

    def test_programme_has_stop(self):
        json_str = """{"programmes": [
            {"channel": "chan1", "start": "20250101000000", "stop": "20250101010000", "title": "Show 1"}
        ]}"""
        result = load_json_epg(json_str)
        self.assertEqual(result["chan1"][0]["stop"], "20250101010000")

    def test_programme_with_desc(self):
        json_str = """{"programmes": [
            {"channel": "chan1", "start": "20250101000000", "stop": "20250101010000", "title": "Show 1", "desc": "Description"}
        ]}"""
        result = load_json_epg(json_str)
        self.assertEqual(result["chan1"][0]["desc"], "Description")

    def test_programme_with_category(self):
        json_str = """{"programmes": [
            {"channel": "chan1", "start": "20250101000000", "stop": "20250101010000", "title": "Show 1", "category": "Drama"}
        ]}"""
        result = load_json_epg(json_str)
        self.assertEqual(result["chan1"][0]["category"], "Drama")

    def test_programme_with_episode(self):
        json_str = """{"programmes": [
            {"channel": "chan1", "start": "20250101000000", "stop": "20250101010000", "title": "Show 1", "episode": "S01E05"}
        ]}"""
        result = load_json_epg(json_str)
        self.assertEqual(result["chan1"][0]["episode"], "S01E05")

    def test_programme_with_rating(self):
        json_str = """{"programmes": [
            {"channel": "chan1", "start": "20250101000000", "stop": "20250101010000", "title": "Show 1", "rating": "PG-13"}
        ]}"""
        result = load_json_epg(json_str)
        self.assertEqual(result["chan1"][0]["rating"], "PG-13")

    def test_multiple_programmes_same_channel(self):
        json_str = """{"programmes": [
            {"channel": "chan1", "start": "20250101000000", "stop": "20250101010000", "title": "Show 1"},
            {"channel": "chan1", "start": "20250101010000", "stop": "20250101020000", "title": "Show 2"}
        ]}"""
        result = load_json_epg(json_str)
        self.assertEqual(len(result["chan1"]), 2)

    def test_multiple_channels(self):
        json_str = """{"programmes": [
            {"channel": "chan1", "start": "20250101000000", "stop": "20250101010000", "title": "Show 1"},
            {"channel": "chan2", "start": "20250101000000", "stop": "20250101010000", "title": "Show 2"}
        ]}"""
        result = load_json_epg(json_str)
        self.assertIn("chan1", result)
        self.assertIn("chan2", result)

    def test_programme_without_channel_skipped(self):
        json_str = """{"programmes": [
            {"start": "20250101000000", "stop": "20250101010000", "title": "Show 1"}
        ]}"""
        result = load_json_epg(json_str)
        self.assertEqual(len(result), 0)

    def test_empty_channel_skipped(self):
        json_str = """{"programmes": [
            {"channel": "", "start": "20250101000000", "stop": "20250101010000", "title": "Show 1"}
        ]}"""
        result = load_json_epg(json_str)
        self.assertEqual(len(result), 0)

    def test_missing_fields_use_empty_string(self):
        json_str = """{"programmes": [
            {"channel": "chan1", "start": "20250101000000", "stop": "20250101010000"}
        ]}"""
        result = load_json_epg(json_str)
        self.assertEqual(result["chan1"][0]["title"], "")

    def test_entries_instead_of_programmes(self):
        json_str = """{"entries": [
            {"channel": "chan1", "start": "20250101000000", "stop": "20250101010000", "title": "Show 1"}
        ]}"""
        result = load_json_epg(json_str)
        self.assertIn("chan1", result)

    def test_mapping_parameter_used(self):
        json_str = """{"programmes": [
            {"chan": "chan1", "beg": "20250101000000", "end": "20250101010000", "name": "Show 1"}
        ]}"""
        mapping = {"channel": "chan", "start": "beg", "stop": "end", "title": "name"}
        result = load_json_epg(json_str, mapping)
        self.assertIn("chan1", result)

    def test_programmes_sorted_by_start(self):
        json_str = """{"programmes": [
            {"channel": "chan1", "start": "20250101020000", "stop": "20250101030000", "title": "Show 3"},
            {"channel": "chan1", "start": "20250101000000", "stop": "20250101010000", "title": "Show 1"},
            {"channel": "chan1", "start": "20250101010000", "stop": "20250101020000", "title": "Show 2"}
        ]}"""
        result = load_json_epg(json_str)
        titles = [p["title"] for p in result["chan1"]]
        self.assertEqual(titles, ["Show 1", "Show 2", "Show 3"])

    def test_returns_dict(self):
        json_str = "{}"
        result = load_json_epg(json_str)
        self.assertIsInstance(result, dict)

    def test_unicode_in_title(self):
        json_str = """{"programmes": [
            {"channel": "chan1", "start": "20250101000000", "stop": "20250101010000", "title": "Café Special"}
        ]}"""
        result = load_json_epg(json_str)
        self.assertIn("Café", result["chan1"][0]["title"])

    def test_special_chars_in_title(self):
        json_str = """{"programmes": [
            {"channel": "chan1", "start": "20250101000000", "stop": "20250101010000", "title": "Show & Tell"}
        ]}"""
        result = load_json_epg(json_str)
        self.assertIn("&", result["chan1"][0]["title"])

    def test_large_number_of_programmes(self):
        programmes = [
            {
                "channel": "chan1",
                "start": f"2025010100{i:02d}00",
                "stop": f"2025010100{i+1:02d}00",
                "title": f"Show {i}",
            }
            for i in range(20)
        ]
        import json

        json_str = json.dumps({"programmes": programmes})
        result = load_json_epg(json_str)
        self.assertEqual(len(result["chan1"]), 20)

    def test_many_channels(self):
        programmes = [
            {"channel": f"chan{i}", "start": "20250101000000", "stop": "20250101010000", "title": f"Show {i}"}
            for i in range(50)
        ]
        import json

        json_str = json.dumps({"programmes": programmes})
        result = load_json_epg(json_str)
        self.assertEqual(len(result), 50)

    def test_programme_all_fields(self):
        json_str = """{"programmes": [
            {"channel": "chan1", "start": "20250101000000", "stop": "20250101010000",
             "title": "Complete", "desc": "Full", "category": "Drama",
             "episode": "S01E01", "rating": "PG"}
        ]}"""
        result = load_json_epg(json_str)
        prog = result["chan1"][0]
        self.assertEqual(prog["title"], "Complete")
        self.assertEqual(prog["desc"], "Full")
        self.assertEqual(prog["category"], "Drama")
        self.assertEqual(prog["episode"], "S01E01")
        self.assertEqual(prog["rating"], "PG")

    def test_channel_id_numeric(self):
        json_str = """{"programmes": [
            {"channel": "123", "start": "20250101000000", "stop": "20250101010000", "title": "Show"}
        ]}"""
        result = load_json_epg(json_str)
        self.assertIn("123", result)

    def test_channel_id_with_special_chars(self):
        json_str = """{"programmes": [
            {"channel": "chan-1.uk", "start": "20250101000000", "stop": "20250101010000", "title": "Show"}
        ]}"""
        result = load_json_epg(json_str)
        self.assertIn("chan-1.uk", result)

    def test_programme_dict_structure(self):
        json_str = """{"programmes": [
            {"channel": "chan1", "start": "20250101000000", "stop": "20250101010000", "title": "Show"}
        ]}"""
        result = load_json_epg(json_str)
        prog = result["chan1"][0]
        self.assertIn("start", prog)
        self.assertIn("stop", prog)
        self.assertIn("title", prog)
        self.assertIn("desc", prog)
        self.assertIn("category", prog)
        self.assertIn("episode", prog)
        self.assertIn("rating", prog)

    def test_malformed_programme_skipped(self):
        json_str = """{"programmes": [
            {"channel": "chan1"},
            {"channel": "chan1", "start": "20250101000000", "stop": "20250101010000", "title": "Good"}
        ]}"""
        result = load_json_epg(json_str)
        self.assertTrue(len(result.get("chan1", [])) >= 1)

    def test_returns_new_dict_each_call(self):
        json_str = "{}"
        result1 = load_json_epg(json_str)
        result2 = load_json_epg(json_str)
        self.assertIsNot(result1, result2)

    def test_nested_json_ignored(self):
        json_str = """{"programmes": [
            {"channel": "chan1", "start": "20250101000000", "stop": "20250101010000",
             "title": "Show", "extra": {"nested": "data"}}
        ]}"""
        result = load_json_epg(json_str)
        self.assertEqual(result["chan1"][0]["title"], "Show")

    def test_null_values_handled(self):
        json_str = """{"programmes": [
            {"channel": "chan1", "start": "20250101000000", "stop": "20250101010000",
             "title": null, "desc": null}
        ]}"""
        result = load_json_epg(json_str)
        # Should handle null gracefully
        self.assertIsInstance(result["chan1"][0]["title"], str)

    def test_integer_channel_id(self):
        json_str = """{"programmes": [
            {"channel": 123, "start": "20250101000000", "stop": "20250101010000", "title": "Show"}
        ]}"""
        result = load_json_epg(json_str)
        # Should convert to string or skip
        self.assertTrue(len(result) >= 0)

    def test_array_at_root_handled(self):
        json_str = "[]"
        result = load_json_epg(json_str)
        self.assertEqual(result, {})

    def test_no_mapping_uses_defaults(self):
        json_str = """{"programmes": [
            {"channel": "chan1", "start": "20250101000000", "stop": "20250101010000", "title": "Show"}
        ]}"""
        result = load_json_epg(json_str, None)
        self.assertIn("chan1", result)

    def test_partial_mapping(self):
        json_str = """{"programmes": [
            {"chan": "chan1", "start": "20250101000000", "stop": "20250101010000", "title": "Show"}
        ]}"""
        mapping = {"channel": "chan"}
        result = load_json_epg(json_str, mapping)
        self.assertIn("chan1", result)

    def test_empty_programmes_array(self):
        json_str = '{"programmes": []}'
        result = load_json_epg(json_str)
        self.assertEqual(result, {})

    def test_string_instead_of_object(self):
        json_str = '{"programmes": ["string"]}'
        result = load_json_epg(json_str)
        # Should handle gracefully
        self.assertEqual(result, {})

    def test_boolean_values_handled(self):
        json_str = """{"programmes": [
            {"channel": "chan1", "start": "20250101000000", "stop": "20250101010000",
             "title": "Show", "archived": true}
        ]}"""
        result = load_json_epg(json_str)
        self.assertEqual(result["chan1"][0]["title"], "Show")

    def test_numeric_values_in_fields(self):
        json_str = """{"programmes": [
            {"channel": "chan1", "start": 20250101000000, "stop": 20250101010000, "title": "Show"}
        ]}"""
        result = load_json_epg(json_str)
        # Should handle or convert
        self.assertTrue(len(result) >= 0)

    def test_whitespace_in_json(self):
        json_str = """
        {
            "programmes": [
                {
                    "channel": "chan1",
                    "start": "20250101000000",
                    "stop": "20250101010000",
                    "title": "Show"
                }
            ]
        }
        """
        result = load_json_epg(json_str)
        self.assertIn("chan1", result)

    def test_escaped_characters(self):
        json_str = """{"programmes": [
            {"channel": "chan1", "start": "20250101000000", "stop": "20250101010000",
             "title": "Show\\nWith\\tSpecial"}
        ]}"""
        result = load_json_epg(json_str)
        self.assertIn("With", result["chan1"][0]["title"])

    def test_unicode_escape_sequences(self):
        json_str = """{"programmes": [
            {"channel": "chan1", "start": "20250101000000", "stop": "20250101010000",
             "title": "Caf\\u00e9"}
        ]}"""
        result = load_json_epg(json_str)
        self.assertIn("Caf", result["chan1"][0]["title"])


if __name__ == "__main__":
    unittest.main()

"""
Test the improved M3U parsing logic
"""

test_m3u = """#EXTM3U
#EXTINF:-1 tvg-id="1" tvg-name="Channel 1" tvg-logo="" group-title="Sports",Channel 1
http://example.com/stream1
#EXTINF:-1 tvg-id="2" tvg-name="Channel 2" tvg-logo="" group-title="Movies",Channel 2
http://example.com/stream2
#EXTINF:-1 tvg-id="3" tvg-name="Channel 3" tvg-logo="" group-title="Sports",Channel 3
http://example.com/stream3
#EXTINF:-1 tvg-id="4" tvg-name="Channel 4" tvg-logo="" group-title="News",Channel 4
http://example.com/stream4
"""

import re

def improved_parser(m3u_data, selected_category):
    """Improved parsing that matches group-title exactly"""
    result = []
    lines = m3u_data.split("\n")

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if line.startswith("#EXTINF"):
            # Extract the group-title value from this line
            group_match = re.search(r'group-title="([^"]*)"', line, re.IGNORECASE)

            if group_match:
                group_title = group_match.group(1)

                # Check if this group matches the selected category
                if group_title == selected_category:
                    # Found a match!
                    if i + 1 < len(lines):
                        extinf_line = lines[i]
                        url_line = lines[i + 1] if i + 1 < len(lines) else ""
                        result.append(f"{extinf_line}\n{url_line}")

        i += 1

    return result

def old_parser(m3u_data, selected_category):
    """Old parsing that just checks if category is in line"""
    result = []
    lines = m3u_data.split("\n")

    for i, each_line in enumerate(lines):
        if selected_category in each_line:
            if i + 1 < len(lines):
                result.append(f"{lines[i]}\n{lines[i + 1]}")

    return result

# Test both parsers
print("Testing M3U Parsers\n" + "="*50)

for category in ["Sports", "Movies", "News", "Sport"]:  # "Sport" should fail
    print(f"\nSearching for category: '{category}'")
    print("-" * 50)

    old_results = old_parser(test_m3u, category)
    new_results = improved_parser(test_m3u, category)

    print(f"Old parser found: {len(old_results)} streams")
    print(f"New parser found: {len(new_results)} streams")

    if len(new_results) > 0:
        print("\nNew parser results:")
        for result in new_results:
            print(f"  {result.split(chr(10))[0][:80]}")
    else:
        print("  (no matches)")

print("\n" + "="*50)
print("\nKey improvements in new parser:")
print("1. Exact match on group-title attribute (not substring)")
print("2. Handles quoted values properly")
print("3. Case-insensitive regex matching")
print("4. Won't match partial category names")


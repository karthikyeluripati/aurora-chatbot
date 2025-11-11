"""
Analyze the member messages dataset for insights and anomalies
"""
import json
from collections import Counter, defaultdict
from datetime import datetime
import re


def load_data():
    """Load messages from JSON file"""
    with open('all_messages.json', 'r') as f:
        return json.load(f)


def analyze_dataset():
    """Perform comprehensive analysis of the dataset"""
    data = load_data()
    messages = data['items']

    print("=" * 80)
    print("DATASET ANALYSIS - Aurora Chatbot")
    print("=" * 80)

    # Basic statistics
    print("\n1. BASIC STATISTICS")
    print("-" * 80)
    print(f"Total messages: {len(messages)}")
    print(f"Total messages (from API): {data['total']}")

    # User distribution
    user_counts = Counter(msg['user_name'] for msg in messages)
    print(f"\nUnique users: {len(user_counts)}")
    print("\nMessages per user:")
    for user, count in sorted(user_counts.items()):
        print(f"  {user}: {count}")

    # Timestamp analysis
    print("\n2. TEMPORAL ANALYSIS")
    print("-" * 80)
    timestamps = [datetime.fromisoformat(msg['timestamp']) for msg in messages]
    print(f"Date range: {min(timestamps).date()} to {max(timestamps).date()}")

    # Check for future dates
    now = datetime.now(timestamps[0].tzinfo)
    future_msgs = [ts for ts in timestamps if ts > now]
    if future_msgs:
        print(f"⚠️  ANOMALY: {len(future_msgs)} messages have future timestamps!")
        print(f"   Latest future date: {max(future_msgs).date()}")

    # Content analysis
    print("\n3. CONTENT ANALYSIS")
    print("-" * 80)

    # Message lengths
    msg_lengths = [len(msg['message']) for msg in messages]
    print(f"Average message length: {sum(msg_lengths) / len(msg_lengths):.1f} characters")
    print(f"Shortest message: {min(msg_lengths)} chars")
    print(f"Longest message: {max(msg_lengths)} chars")

    # Common keywords and patterns
    print("\n4. COMMON THEMES")
    print("-" * 80)

    all_text = ' '.join(msg['message'].lower() for msg in messages)

    # Travel and locations
    locations = re.findall(r'\b(paris|london|tokyo|milan|monaco|new york|santorini|rome|bangkok|dubai|'
                          r'maldives|cannes|tokyo|venice|vienna|sydney|madrid)\b', all_text)
    location_counts = Counter(locations)
    print(f"\nTop locations mentioned:")
    for loc, count in location_counts.most_common(10):
        print(f"  {loc.title()}: {count}")

    # Services requested
    services = {
        'reservations': len(re.findall(r'\breservation\b', all_text)),
        'book/booking': len(re.findall(r'\bbook\w*\b', all_text)),
        'flights': len(re.findall(r'\bflight\w*\b', all_text)),
        'hotels': len(re.findall(r'\bhotel\w*\b', all_text)),
        'cars': len(re.findall(r'\bcar\w*\b', all_text)),
        'tickets': len(re.findall(r'\bticket\w*\b', all_text)),
    }
    print(f"\nService mentions:")
    for service, count in sorted(services.items(), key=lambda x: x[1], reverse=True):
        print(f"  {service}: {count}")

    # Anomaly detection
    print("\n5. ANOMALIES & INCONSISTENCIES")
    print("-" * 80)

    # Check for duplicate messages
    message_texts = [msg['message'] for msg in messages]
    text_counts = Counter(message_texts)
    duplicates = {text: count for text, count in text_counts.items() if count > 1}
    if duplicates:
        print(f"\n[!] Found {len(duplicates)} duplicate message texts:")
        for text, count in sorted(duplicates.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   '{text[:60]}...' appears {count} times")
    else:
        print("[OK] No duplicate messages found")

    # Check for user_id consistency
    user_id_map = defaultdict(set)
    for msg in messages:
        user_id_map[msg['user_name']].add(msg['user_id'])

    print("\n[!] User ID consistency check:")
    for user_name, user_ids in sorted(user_id_map.items()):
        if len(user_ids) > 1:
            print(f"   {user_name} has {len(user_ids)} different user_ids!")
        else:
            print(f"   [OK] {user_name}: 1 user_id")

    # Check for missing or unusual data
    print("\n[!] Data quality checks:")
    empty_messages = [msg for msg in messages if not msg['message'].strip()]
    print(f"   Empty messages: {len(empty_messages)}")

    very_short = [msg for msg in messages if len(msg['message']) < 10]
    print(f"   Very short messages (<10 chars): {len(very_short)}")

    very_long = [msg for msg in messages if len(msg['message']) > 500]
    print(f"   Very long messages (>500 chars): {len(very_long)}")

    # Phone numbers and PII
    print("\n6. PERSONAL INFORMATION")
    print("-" * 80)
    phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

    phones = re.findall(phone_pattern, all_text)
    emails = re.findall(email_pattern, all_text)

    print(f"Phone numbers found: {len(phones)}")
    print(f"Email addresses found: {len(emails)}")

    # User preferences
    print("\n7. USER PREFERENCES & PATTERNS")
    print("-" * 80)

    user_preferences = defaultdict(list)
    for msg in messages:
        text = msg['message'].lower()
        user = msg['user_name']

        if 'prefer' in text or 'preference' in text:
            user_preferences[user].append(msg['message'])

    if user_preferences:
        print("Users with stated preferences:")
        for user, prefs in sorted(user_preferences.items()):
            print(f"\n  {user}:")
            for pref in prefs[:3]:  # Show first 3
                print(f"    - {pref[:70]}...")
    else:
        print("No explicit preferences found")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    analyze_dataset()

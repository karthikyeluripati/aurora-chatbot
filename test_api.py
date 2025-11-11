"""
Test script for the Aurora QA API
"""
import httpx
import json
import time

BASE_URL = "http://localhost:8000"

# Test questions
TEST_QUESTIONS = [
    "When is Layla planning her trip to London?",
    "How many cars does Vikram Desai have?",
    "What are Amira's favorite restaurants?",
    "What is Sophia's phone number?",
    "Which restaurants has Fatima made reservations at?",
    "What cities has Armand Dupont traveled to?",
]


def test_health():
    """Test health check endpoint"""
    print("Testing health endpoint...")
    response = httpx.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")


def test_stats():
    """Test stats endpoint"""
    print("Testing stats endpoint...")
    response = httpx.get(f"{BASE_URL}/stats")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")


def test_ask(question: str):
    """Test ask endpoint with a question"""
    print(f"Question: {question}")
    response = httpx.post(
        f"{BASE_URL}/ask",
        json={"question": question},
        timeout=60.0
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        answer = response.json()["answer"]
        print(f"Answer: {answer}\n")
    else:
        print(f"Error: {response.text}\n")


def main():
    """Run all tests"""
    print("=" * 60)
    print("Aurora QA System - Test Suite")
    print("=" * 60 + "\n")

    # Check if server is running
    try:
        httpx.get(BASE_URL, timeout=2.0)
    except httpx.ConnectError:
        print("ERROR: Server is not running!")
        print("Please start the server first with: python app.py")
        return

    # Run tests
    test_health()
    test_stats()

    print("=" * 60)
    print("Testing Question Answering")
    print("=" * 60 + "\n")

    for question in TEST_QUESTIONS:
        test_ask(question)
        time.sleep(1)  # Rate limiting


if __name__ == "__main__":
    main()

from qa_agent import answer_question
import os

def test_qa_system():
    print("=== Testing QA Agent System ===")
    
    # Verify reviews.json exists
    if not os.path.exists("reviews.json"):
        print("Error: Run data_generator.py first to create reviews.json")
        return
        
    # Test case 1: Valid query about a known complaint
    print("\n[TEST 1] Querying: 'Why are heater switches melting?'")
    res1 = answer_question("Why are heater switches melting?")
    print("Answer:")
    print(res1["answer"])
    print(f"Citations: {len(res1['citations'])} reviews cited.")
    print("Reasoning Steps:")
    for step in res1["execution_steps"]:
        print(f"  -> {step}")
        
    assert "REV-" in str(res1["citations"]) or len(res1["citations"]) > 0, "Should contain citations."
    assert "melt" in res1["answer"].lower(), "Answer should discuss melting switches."
    
    # Test case 2: Hallucination prevention - Query for a topic not in the reviews
    print("\n[TEST 2] Querying: 'Why are the purifiers exploding?'")
    res2 = answer_question("Why are the purifiers exploding?")
    print("Answer:")
    print(res2["answer"])
    print(f"Citations: {len(res2['citations'])} reviews cited.")
    print("Reasoning Steps:")
    for step in res2["execution_steps"]:
        print(f"  -> {step}")
        
    assert "I do not know" in res2["answer"], "Should state 'I do not know' due to missing data."
    assert len(res2["citations"]) == 0, "Citations should be empty."

    # Test case 3: Query with out-of-bounds keywords (e.g., warranty)
    print("\n[TEST 3] Querying: 'What is the warranty policy for fan clicking?'")
    res3 = answer_question("What is the warranty policy for fan clicking?")
    print("Answer:")
    print(res3["answer"])
    print(f"Citations: {len(res3['citations'])} reviews cited.")
    
    assert "warranty" in res3["answer"].lower(), "Should mention lack of warranty details."
    assert "click" in res3["answer"].lower(), "Should still discuss clicking issues."
    
    print("\n=== All Tests Passed Successfully! ===")

if __name__ == "__main__":
    test_qa_system()

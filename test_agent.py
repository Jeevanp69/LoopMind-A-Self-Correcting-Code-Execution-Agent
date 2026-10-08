from agent import run_agent_loop

TASKS = [
    # Task 1: String manipulation
    (
        "Write a function `is_anagram(s1, s2)` that returns True if two strings are anagrams "
        "(case-insensitive, ignore whitespace). "
        "Include these assertions:\n"
        "assert is_anagram('Listen', 'Silent') == True\n"
        "assert is_anagram('Hello', 'World') == False\n"
        "assert is_anagram('rail safety', 'fairy tales') == True"
    ),

    # Task 2: Math operation
    (
        "Write a function `nth_fibonacci(n)` using recursion with memoization. "
        "Handle 0 and negative inputs by raising ValueError. "
        "Include these assertions:\n"
        "assert nth_fibonacci(1) == 1\n"
        "assert nth_fibonacci(6) == 8\n"
        "try:\n"
        "    nth_fibonacci(0)\n"
        "    assert False\n"
        "except ValueError:\n"
        "    assert True"
    ),

    # Task 3: Collection operations & sorting
    (
        "Write a function `sort_by_frequency(nums)` that sorts a list of integers by frequency descending. "
        "If frequencies match, sort by value ascending. "
        "Include these assertions:\n"
        "assert sort_by_frequency([1, 1, 2, 2, 2, 3]) == [2, 2, 2, 1, 1, 3]\n"
        "assert sort_by_frequency([4, 6, 2, 6, 4, 4, 6]) == [4, 4, 4, 6, 6, 6, 2]\n"
        "assert sort_by_frequency([]) == []"
    ),

    # Task 4: Tricky edge case (designed to test self-correction on nested types)
    (
        "Write a function `flatten_nested(arr)` that flattens an arbitrarily nested structure of lists/tuples, "
        "ignoring strings (strings should remain single elements, not be unpacked). "
        "Include these assertions:\n"
        "assert flatten_nested([1, [2, ('cat', [3])], 4]) == [1, 2, 'cat', 3, 4]\n"
        "assert flatten_nested([]) == []\n"
        "assert flatten_nested(['hello']) == ['hello']"
    ),

    # Task 5: Parsing & dictionary manipulation
    (
        "Write a function `roman_to_int(s)` that converts a Roman numeral string to an integer. "
        "Include these assertions:\n"
        "assert roman_to_int('III') == 3\n"
        "assert roman_to_int('LVIII') == 58\n"
        "assert roman_to_int('MCMXCIV') == 1994"
    ),
]

def run_suite():
    print(f"Starting test suite for {len(TASKS)} agent tasks...\n")
    summary = []
    for idx, prompt in enumerate(TASKS, 1):
        print(f"\n==================== TEST SUITE TASK {idx}/{len(TASKS)} ====================")
        res = run_agent_loop(prompt, max_attempts=3)
        summary.append({
            "task_idx": idx,
            "passed": res["passed"],
            "attempts": len(res["attempts"])
        })

    print("\n\n" + "=" * 50)
    print("SUITE EXECUTION SUMMARY")
    print("=" * 50)
    for s in summary:
        status = "PASSED" if s["passed"] else "FAILED"
        print(f"Task {s['task_idx']}: {status} in {s['attempts']} attempt(s)")

if __name__ == "__main__":
    run_suite()
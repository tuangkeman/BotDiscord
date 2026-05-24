import sys, io
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import asyncio
from utils.sandbox import run_code, check_code_safety
from utils.judge import judge

async def test():
    print("=== Test 1: Kode Benar (Rata-rata) ===")
    code = """
n = int(input())
vals = list(map(int, input().split()))
print(f'{sum(vals)/n:.2f}')
"""
    tc = [
        {"input": "3\n10 20 30", "output": "20.00"},
        {"input": "5\n100 90 80 70 60", "output": "80.00"},
    ]
    r = await judge(code, tc)
    print(f"  Verdict : {r['verdict']}")
    print(f"  Passed  : {r['passed']}/{r['total']}")

    print()
    print("=== Test 2: Wrong Answer ===")
    code2 = "print(42)"
    r2 = await judge(code2, tc)
    print(f"  Verdict  : {r2['verdict']}")
    print(f"  Got      : {r2['got']}")
    print(f"  Expected : {r2['expected']}")

    print()
    print("=== Test 3: Runtime Error ===")
    code3 = "print(1/0)"
    r3 = await judge(code3, [{"input": "", "output": "x"}])
    print(f"  Verdict : {r3['verdict']}")
    print(f"  Error   : {r3['error_msg'][:80]}")

    print()
    print("=== Test 4: Forbidden Code (import os) ===")
    safe, msg = check_code_safety("import os\nprint(os.getcwd())")
    print(f"  Safe : {safe}")
    print(f"  Msg  : {msg}")

    print()
    print("=== Test 5: Time Limit Exceeded ===")
    code5 = "while True: pass"
    r5 = await judge(code5, [{"input": "", "output": "x"}])
    print(f"  Verdict : {r5['verdict']}")

    print()
    print("=== Test 6: FizzBuzz (soal ke-16) ===")
    code6 = """
n = int(input())
for i in range(1, n+1):
    if i % 15 == 0:
        print('FizzBuzz')
    elif i % 3 == 0:
        print('Fizz')
    elif i % 5 == 0:
        print('Buzz')
    else:
        print(i)
"""
    tc6 = [
        {"input": "5",  "output": "1\n2\nFizz\n4\nBuzz"},
        {"input": "15", "output": "1\n2\nFizz\n4\nBuzz\nFizz\n7\n8\nFizz\nBuzz\n11\nFizz\n13\n14\nFizzBuzz"},
    ]
    r6 = await judge(code6, tc6)
    print(f"  Verdict : {r6['verdict']}")
    print(f"  Passed  : {r6['passed']}/{r6['total']}")

    print()
    print("=" * 40)
    print("Semua test selesai!")

asyncio.run(test())

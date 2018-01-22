import sys
import time
import asyncio
import searcher


def main():
    # Default for 13 inch MBP, iPhone X
    x1, y1, x2, y2 = 1192, 0, 1679, 1049
    if len(sys.argv) >= 4: x1, y1, x2, y2 = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])

    loop = asyncio.get_event_loop()
    while True:
        question, answer1, answer2, answer3 = searcher.get_hq_trivia_set(x1, y1, x2, y2)
        if question != "" and answer1 != "" and answer2 != "" and answer3 != "":
            print("\n\n\nFinding Answer...")
            loop.run_until_complete(searcher.find_answer(question, answer1, answer2, answer3))
            time.sleep(0.5)
            input("\nPress ENTER to search again.")
        else:
            print("...")
            time.sleep(0.05)


main()

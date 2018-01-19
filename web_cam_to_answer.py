import re
import sys
# from bs4 import BeautifulSoup
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.corpus import brown
import pyscreenshot as image_grab
import time
import os
import requests
import asyncio

try:
    import Image
except ImportError:
    from PIL import Image
import pytesseract

brown_train = brown.tagged_sents(categories='news')
regexp_tagger = nltk.RegexpTagger(
    [(r'^-?[0-9]+(.[0-9]+)?$', 'CD'),
     (r'(-|:|;)$', ':'),
     (r'\'*$', 'MD'),
     (r'(The|the|A|a|An|an)$', 'AT'),
     (r'.*able$', 'JJ'),
     (r'^[A-Z].*$', 'NNP'),
     (r'.*ness$', 'NN'),
     (r'.*ly$', 'RB'),
     (r'.*s$', 'NNS'),
     (r'.*ing$', 'VBG'),
     (r'.*ed$', 'VBD'),
     (r'.*', 'NN'),
     (r'\“(.*?)\”', 'QTN')
     ])
unigram_tagger = nltk.UnigramTagger(brown_train, backoff=regexp_tagger)
bigram_tagger = nltk.BigramTagger(brown_train, backoff=unigram_tagger)

cfg = {
    "NNP+NNP": "NNP",
    "NN+NN": "NNI",
    "NNI+NN": "NNI",
    "JJ+JJ": "JJ",
    "JJ+NN": "NNI",
    "AP+NN": "APN",
    "AP+NNS": "APNS"
}

# Default for 13 inch MBP, iPhone X
x1, y1, x2, y2 = 1192, 0, 1679, 1049
if len(sys.argv) >= 4:
    x1, y1, x2, y2 = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])

pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'


def image_path_to_image():
    im = image_grab.grab(bbox=(x1, y1, x2, y2))
    im.save("test.png")
    return im


def get_question_and_answer_tuples():
    return {
        "question": (43, 383, 927, 787),
        "answer1": (100, 860, 870, 960),
        "answer2": (100, 1010, 870, 1140),
        "answer3": (100, 1180, 870, 1300)
    }


def image_to_string(image):
    return pytesseract.image_to_string(image)


def fix_multiline(words):
    return re.sub(r'\s+', ' ', words)


def get_hq_trivia_set():
    question_answers = get_question_and_answer_tuples()
    base_image = image_path_to_image()
    return (
        fix_multiline(
            image_to_string(
                base_image.crop(response_area)
            )
        )
        for response_key, response_area in question_answers.items()
    )


# Normalize brown corpus' tags ("NN", "NN-PL", "NNS" > "NN")
def normalize_tags(tagged):
    n_tagged = []
    for t in tagged:
        if t[1] == "NP-TL" or t[1] == "NP":
            n_tagged.append((t[0], "NNP"))
            continue
        if t[1].endswith("-TL"):
            n_tagged.append((t[0], t[1][:-3]))
            continue
        if t[1].endswith("S"):
            n_tagged.append((t[0], t[1][:-1]))
            continue
        n_tagged.append((t[0], t[1]))
    return n_tagged


async def get_count_from_google_query(question_input, answer1, answer2, answer3):
    stop_words = set(stopwords.words('english'))
    words = word_tokenize(question_input)
    tags = normalize_tags(bigram_tagger.tag(word_tokenize(question_input.replace("'", ""))))
    merge = True
    while merge:
        merge = False
        for x in range(0, len(tags) - 1):
            t1 = tags[x]
            t2 = tags[x + 1]
            key = "%s+%s" % (t1[1], t2[1])
            print("key:" + key)
            value = cfg.get(key, '')
            if value:
                merge = True
                tags.pop(x)
                tags.pop(x)
                match = "%s %s" % (t1[0], t2[0])
                pos = value
                tags.insert(x, (match, pos))
                break

    matches = []
    print(tags)
    for t in tags:
        if t[1] in {"NNP", "NNI", "NN", "APN", "APNS", "QTN"}:
            matches.append(t[0])
    print(matches)

    parsed_question = ' '.join(matches)

    future_q = search_answer(parsed_question, "(" + answer1 + " OR " + answer2 + "OR" + answer3 + ")")
    future1 = search_answer(parsed_question, answer1)
    future2 = search_answer(parsed_question, answer2)
    future3 = search_answer(parsed_question, answer3)
    q_result = await future_q
    a1 = await future1
    a2 = await future2
    a3 = await future3
    total1 = int(a1.json()["queries"]["request"][0]["totalResults"])
    total2 = int(a2.json()["queries"]["request"][0]["totalResults"])
    total3 = int(a3.json()["queries"]["request"][0]["totalResults"])

    print("----------------------------------")
    print("Parsed Question: " + parsed_question)
    print("----------------------------------")

    if "items" in q_result.json() and len(q_result.json()["items"]) > 0:
        print(q_result.json()["items"][0]["snippet"])
        print("----------------------------------")
    print(answer1 + " : " + str(total1) + "\n----------------------------------")
    print(answer2 + " : " + str(total2) + "\n----------------------------------")
    print(answer3 + " : " + str(total3) + "\n----------------------------------")


def search_answer(parsed_question, answer):
    apiKey = os.environ.get("GOOGLE_SEARCH_API_KEY")
    url = "https://www.googleapis.com/customsearch/v1?key=" + apiKey + "&cx=006735088913908788598:cdia39tiyvi&q="
    return loop.run_in_executor(None, requests.get, url + " (" + parsed_question + ") " + answer)


loop = asyncio.get_event_loop()
while True:
    question, answer1, answer2, answer3 = get_hq_trivia_set()
    if question != "" and answer1 != "" and answer2 != "" and answer3 != "":
        print("\n\n")
        print("Finding Answer...")
        loop.run_until_complete(get_count_from_google_query(question, answer1, answer2, answer3))
        time.sleep(10)
    else:
        print("...")
        time.sleep(0.05)

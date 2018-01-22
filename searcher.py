import requests
import asyncio
import pyscreenshot as image_grab
import pytesseract
import nltk
from nltk.tokenize import word_tokenize
import re
import os
from nltk.corpus import brown

pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'

brown_train = brown.tagged_sents(categories='news')
regexp_tagger = nltk.RegexpTagger([
    (r'^-?[0-9]+(.[0-9]+)?$', 'CD'),
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
    "AP+NNS": "APNS",
    "CD+NN": "CDN",
    "VBN+IN": "VIN"
}


def image_path_to_image(x1, y1, x2, y2):
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


def get_hq_trivia_set(x1, y1, x2, y2):
    question_answers = get_question_and_answer_tuples()
    base_image = image_path_to_image(x1, y1, x2, y2)
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


def get_matches(tags):
    print(tags)
    merge = True
    while merge:
        merge = False
        for x in range(0, len(tags) - 1):
            t1 = tags[x]
            t2 = tags[x + 1]
            key = "%s+%s" % (t1[1], t2[1])
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
    for t in tags:
        if t[1] in {"NNP", "NNI", "NN", "APN", "APNS", "QTN", "CDN", "VBN", "VIN"}:
            matches.append(t[0])
    return matches


async def find_answer(question_input, answer1, answer2, answer3):
    matches = get_matches(normalize_tags(bigram_tagger.tag(word_tokenize(question_input.replace('NOT', 'not')))))
    parsed_question = ' '.join(matches).replace(r'“\s|\s”', '"')
    inverse = True if 'NOT' in question_input else False
    line_str = "----------------------------------"
    print(line_str + '\033[1m'  + "\nParsed Question: " + parsed_question + '\033[0m' + "\n" + line_str)
    future_q = get_google_results(parsed_question)
    q_result = await future_q
    result_preview = ""
    if "items" in q_result.json() and len(q_result.json()["items"]) > 0:
        result_preview = q_result.json()["items"][0]["snippet"]
    else:
        future_backup_q = get_google_results(parsed_question, "(" + answer1 + " OR " + answer2 + "OR" + answer3 + ")")
        q_result2 = await future_backup_q
        if "items" in q_result2.json() and len(q_result2.json()["items"]) > 0:
            result_preview = q_result2.json()["items"][0]["snippet"]
    print(result_preview + "\n" + line_str)
    answers = [answer1, answer2, answer3]
    futures = []
    for answer in answers:
        future = get_google_results(parsed_question,answer)
        futures.insert(len(futures), await future)
    for index, future in enumerate(futures):
        total = int(future.json()["queries"]["request"][0]["totalResults"])
        if answers[index].lower() in result_preview.lower().replace('\n', ''):
            print('\033[94m\033[1m' + (answers[index] + " : {:,d}" + '\033[0m\n' + line_str).format(total))
        else:
            print((answers[index] + " : {:,d}" + "\n" + line_str).format(total))
    print(inverse)


def get_google_results(parsed_question, answer = ""):
    loop = asyncio.get_event_loop()
    api_key = os.environ.get("GOOGLE_SEARCH_API_KEY")
    url = "https://www.googleapis.com/customsearch/v1?key=" + api_key + "&cx=006735088913908788598:cdia39tiyvi&q="
    return loop.run_in_executor(None, requests.get, url + " (" + parsed_question + ") " + answer)

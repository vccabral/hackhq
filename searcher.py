import requests
import asyncio
import pyscreenshot as image_grab
import pytesseract
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import treebank
import re
import os
from nltk.corpus import brown
from pws import Google
from pws import Bing
import json
from timeit import default_timer as timer

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
    (r'.*ly$', 'RB'),\
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
    "VBN+IN": "VIN",
    "VB+JJ": "VBJ",
    "AT+CD": "ACD",
    "VBG+NN": "VBN",
}


def image_path_to_image(x1, y1, x2, y2):
    im = image_grab.grab(bbox=(x1, y1, x2, y2))
    im.save("test.png")
    return im


def get_question_and_answer_tuples():
    return {
        "question": (80, 460, 900, 845),
        "answer1": (100, 885, 895, 960),
        "answer2": (100, 1060, 895, 1125),
        "answer3": (100, 1225, 895, 1300)
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
        if t[1] in {"NNP", "NNI", "NN", "APN", "APNS", "QTN", "CDN", "VBN", "VIN", "VBJ", "JJT", "ACD", "VBN"}:
            matches.append(t[0])
    return matches


async def find_answer(question_input, answer1, answer2, answer3):
    matches = get_matches(normalize_tags(bigram_tagger.tag(word_tokenize(question_input.replace('NOT', 'not')))))
    parsed_question = ' '.join(matches).replace(r'“\s|\s”', '"')
    inverse = True if 'NOT' in question_input else False
    line_str = "----------------------------------"
    print(line_str + '\033[1m' + "\nInput Question: " + question_input + '\033[0m' + "\n" + line_str)

    answer1Count = (get_google_results(question_input, answer1))['total_results']
    answer2Count = (get_google_results(question_input, answer2))['total_results']
    answer3Count = (get_google_results(question_input, answer3))['total_results']
    finalAnswer= ""
    if inverse:
        finalAnswer = solveNegativeQuestion(answer1Count, answer2Count, answer3Count)
    else:
        finalAnswer = solveQuestion(answer1Count, answer2Count, answer3Count)

    if finalAnswer is "answer1":
        print(answer1)
    elif finalAnswer is "answer2":
        print(answer2)
    elif finalAnswer is "answer3":
        print(answer3)
    else:
        print("Something went wrong time to panic")


def solveNegativeQuestion(answer1Count, answer2Count, answer3Count):
    if answer1Count < answer2Count and answer1Count < answer3Count:
        return "answer1"
    elif answer2Count < answer3Count:
       return "answer2"
    else:
        return "answer3"

def solveQuestion(answer1Count, answer2Count, answer3Count):
    if answer1Count > answer2Count and answer1Count > answer3Count:
        return "answer1"
    elif answer2Count > answer3Count:
        return "answer2"
    else:
        return "answer3"

def get_google_results(parsed_question, answer):
    return Google.search(query='' + parsed_question + ' ' + answer, num=5, start=2, country_code="es")
    #print(Bing.search('hello world', 5, 2))

def get_bing_results(parsed_question, answer=""):
    return Bing.search('' + parsed_question + ' ' + answer, 5, 2)

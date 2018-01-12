import re
import sys
import urllib.parse
from urllib.request import urlopen
from bs4 import BeautifulSoup
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
import pyscreenshot as ImageGrab
import time
import os
from subprocess import call
import requests
import asyncio


try:
    import Image
except ImportError:
    from PIL import Image
import pytesseract


x1, y1, x2, y2 = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])

pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'
IMAGE_PATH = 'hq-trivia.jpg'


def image_path_to_image(image_path):
	im=ImageGrab.grab(bbox=(x1,y1,x2,y2))
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

def get_hq_trivia_set(image_path):
	question_answers = get_question_and_answer_tuples()
	base_image = image_path_to_image(IMAGE_PATH)
	return (
		fix_multiline(
			image_to_string(
				base_image.crop(response_area)
			)
		)
		for response_key, response_area in question_answers.items()
	)

async def get_count_from_google_query(question, answer1, answer2, answer3):
	stopWords = set(stopwords.words('english'))
	stopWordsExt = ["?",".",",","who","what","when","where","why","which","\""]
	words = word_tokenize(question)
	parsedQuestion = "";
	for w in words:
		if w == "#": parsedQuestion = parsedQuestion + " " + "number"
		elif w not in stopWords and w.lower() not in stopWordsExt: parsedQuestion = parsedQuestion + " " + w
	loop = asyncio.get_event_loop();
	future1 = searchAnswer(parsedQuestion,answer1)
	future2 = searchAnswer(parsedQuestion,answer2)
	future3 = searchAnswer(parsedQuestion,answer3)
	a1 = await future1
	a2 = await future2
	a3 = await future3
	total1=int(a1.json()["queries"]["request"][0]["totalResults"])
	total2=int(a2.json()["queries"]["request"][0]["totalResults"])
	total3=int(a3.json()["queries"]["request"][0]["totalResults"])
	print(parsedQuestion)
	print(answer1 + " : " + str(total1))
	print(answer2 + " : " + str(total2))
	print(answer3 + " : " + str(total3))

	# if total1 > total2 and total1 > total3:
	# 	call(["say",answer1])
	# 	print(answer1)
	# elif total2 > total3:
	# 	call(["say",answer2])
	# 	print(answer2)
	# else:
	# 	call(["say",answer3])
	# 	print(answer3)

def searchAnswer( question, answer ):
	apiKey = os.environ.get("GOOGLE_SEARCH_API_KEY")
	url = "https://www.googleapis.com/customsearch/v1?key=" + apiKey + "&cx=006735088913908788598:cdia39tiyvi&q="
	return loop.run_in_executor(None, requests.get, url + " " + question + " " + answer)

loop = asyncio.get_event_loop()
while True:
	question, answer1, answer2, answer3 = get_hq_trivia_set(IMAGE_PATH)
	if question != "" and answer1 != "" and answer2 != "" and answer3 != "":
		print("Finding Answer: ")
		loop.run_until_complete(get_count_from_google_query(question, answer1, answer2, answer3))
		time.sleep(4)
	else:
		print("N/A")
		time.sleep(1)



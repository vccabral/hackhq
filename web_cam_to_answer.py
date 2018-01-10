import re
import sys
import urllib.parse
from urllib.request import urlopen
from bs4 import BeautifulSoup
import pyscreenshot as ImageGrab
import time
import os
from subprocess import call

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
		"question": (30, 180, 530, 360),
		"answer1": (70, 400, 400, 450),
		"answer2": (70, 490, 400, 540),
		"answer3": (70, 600, 400, 650)
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

def get_google_url(q):
	q_encoded = urllib.parse.quote_plus(q)
	return "https://www.google.com/search?q="+q_encoded+"&oq="+q_encoded

def get_google_page(url):
	# fixme
	return BeautifulSoup("<div id='resultStats'>About 82,300 results<nobr> (0.51 seconds)&nbsp;</nobr></div>", 'html.parser')

def extract_count_of_hits(page):
	p = re.compile('[\d,]+')
	return int(p.findall(page.find(id="resultStats").text)[0].replace(",", ""))

def get_count_from_google_query(query):
	google_url = get_google_url(query)
	page = get_google_page(google_url)
	count_of_hits = extract_count_of_hits(page)
	return count_of_hits

question, answer1, answer2, answer3 = get_hq_trivia_set(IMAGE_PATH)


while True:
	print(question)
	print(answer1, get_count_from_google_query(question+" "+answer1))
	print(answer2)
	print(answer3)
	answer = "one"
	call(["say", answer])

	time.sleep(1)



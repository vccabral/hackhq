import re
import sys
import urllib.parse
from urllib.request import urlopen
from bs4 import BeautifulSoup
import pyscreenshot as ImageGrab
import time
import os
from subprocess import call
import requests


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
	return Image.open(IMAGE_PATH)

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

def get_count_from_google_query(question, answer1, answer2, answer3):

	return "hello"


while True:
	question, answer1, answer2, answer3 = get_hq_trivia_set(IMAGE_PATH)
	answer = get_count_from_google_query(question, answer1, answer2, answer3)
	call(["say", answer])
	time.sleep(1)



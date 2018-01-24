# hackhq

## Instructions for Mac
Using homebrew, make sure python3 is installed.
```
brew install python3
```

Install virtualenv.
```
pip install virtualenv virtualenvwrapper
```

Navigate to application directory and create a virtual environment.
```
cd /path/to/hackhq
virtualenv -p python3 .
```

Enter virtualenv and install requirements.
```
source bin/activate
pip install -r requirements.txt
```

Install required NLTK data.
```
python
nltk.download('popular')
exit()
```

# The DR News Quiz Scraper

This is a scraper designed for scraping the weekly [news quiz](https://www.dr.dk/quiz/nyheder) hosted by Danmarks Radio. 

The scraper uses [Selenium](https://pypi.org/project/selenium/) to run a headless broswer that simulates user interaction (button clicking, etc.). 

The correct answers are brute-forced. 

Strictly intended for academic use. 

## Installation

For best results I recommend running in a virtual environment:

```bash
python3 -m venv scraper_env
source scraper_env/bin/activate
pip install -r requirements.txt
```

## Usage

To scrape all quizzes for 2025, simply run:

```bash
python3 -m scripts.scrape_quizzes_2025.py
```

Note that brute-forcing takes time because each failure means that the scraper needs to click through the previous questions. 
Correct results are saved, but waiting for javascript elements to load takes time. 

## Future 

This is a work in progress. I intend to expand the scraper to multiple years and multiple processes 
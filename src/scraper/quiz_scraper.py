from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from pathlib import Path
import json
import time

class QuizScraper():
    def __init__(self, start_url='https://www.dr.dk/quiz/nyheder?id=67653b22bdc57085138441fa', headless=True):
        self.start_url = start_url
        
        # Set up Chrome options for headless mode
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")

        # Load driver
        self.driver = webdriver.Chrome(options=chrome_options)

        # Navigate to the quiz page
        self.driver.get(start_url)
    
    def get_quiz_id(self):
        edition = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.newsquiz-header span.edition-text"))
        )
        id = edition.text.strip().split()[1]
        return id

    def next_quiz_exists(self) -> bool:
        try:
            btn = self.driver.find_element(By.CSS_SELECTOR, "#drn-newsquiz-page-quiz-next")
            return btn.is_displayed() and btn.is_enabled()
        except:
            return False

    def click_next_quiz(self):
        next_quiz_btn = WebDriverWait(self.driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#drn-newsquiz-page-quiz-next"))
        )
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_quiz_btn)
        ActionChains(self.driver).move_to_element(next_quiz_btn).pause(0.5).click().perform()

    
    def collect_urls(self, max_quizzes:int = None, debug=False):
        print("Collecting URLs for avaialable quizzes in 2025...")
        quiz_urls = [self.driver.current_url]
        while self.next_quiz_exists():
            if len(quiz_urls) == max_quizzes:
                print("Stopped due to max constraint")
                break
            if debug:
                print("Next quiz exists")
            self.click_next_quiz()
            if debug:
                print(f"Current quiz: {self.get_quiz_id()}")
            url = self.driver.current_url
            if debug: print(f"URL: {url}")
            quiz_urls.append(url)
        self.driver.get(self.start_url)
        self.quiz_urls = quiz_urls
        print(f"{len(self.quiz_urls)} quiz URLs found")

    ### -------  Helper functions for interacting with quiz -------- 

    def try_answer(self, button_idx: int):
        question = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.question-container.active"))
        )

        selector = f'button.answer-button[data-index="{button_idx}"]'

        WebDriverWait(question, 5).until(
            lambda q: q.find_element(By.CSS_SELECTOR, selector)
        )

        button = question.find_element(By.CSS_SELECTOR, selector)

        #print(f"Trying answer {button_idx}")
        WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable(button))
        button.click()

        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.feedback-wrapper"))
        )

        classes = button.get_attribute("class")
        #print(classes)
        
        # check if answer was correct 
        if classes == "answer-button correct":
            success = 1
        else:
            success = 0

        return success

    def answer_question(self, button_idx: int):
        try:
            question = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.question-container.active"))
            )

            selector = f'button.answer-button[data-index="{button_idx}"]'

            WebDriverWait(question, 5).until(
                lambda q: q.find_element(By.CSS_SELECTOR, selector)
            )

            button = question.find_element(By.CSS_SELECTOR, selector)

            WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable(button))
            
            #print(f"Clicking button {button_idx}")
            button.click()

            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.feedback-wrapper"))
            )

        except Exception as e:
            print("Error in answer_question:", e)
        finally:
            pass


    def go_to_next_question(self):
        selector = (
            "#drn-newsquiz-page-quiz-wrapper > div > div.questions-container > "
            "div.question-container.active.correct.response > div.quiz-field > "
            "div.feedback-wrapper > button"
        )

        next_button = WebDriverWait(self.driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
        )

        self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
        #print("Clicking 'next question' button via CSS selector")
        ActionChains(self.driver).move_to_element(next_button).click().perform()


    def scrape_active_question_text(self):
        question_elem = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.question-container.active h2"))
        )
        return question_elem.text.strip()

    def scrape_active_question_answers(self):
        answers = []
        buttons = WebDriverWait(self.driver, 5).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.question-container.active button.answer-button"))
        )
        for i in range(3):
            answer =  buttons[i].text.strip()
            answers.append(answer)
        return answers


    def click_correct_buttons(self, button_idxs: list[int]):
        for idx in button_idxs:
            self.answer_question(idx)
            self.go_to_next_question()
        return

    def brute_force_answer(self, correct: list[int]):
        for i in range(3):
            if i != 0:
                self.click_correct_buttons(correct)  # only replay after refresh

            success = self.try_answer(i)
            if success:
                self.go_to_next_question()
                return i
            else:
                self.driver.refresh()

    def quiz_is_over(self, timeout=2):
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.endscreen-container.active button"))
            )
            return True
        except TimeoutException:
            return False

    def save_quiz_to_jsonl(self, week: int, res: dict, base_path: str = "results/2025"):
        path = Path(base_path)
        path.mkdir(parents=True, exist_ok=True)

        filename = f"week_{week}.jsonl"
        file_path = path / filename

        print(f"Saving results to: {file_path}")
        with file_path.open("a", encoding="utf-8") as f:
            for i, (q, opts, correct_idx) in enumerate(zip(res["questions"], res["answers"], res["correct"])):
                f.write(json.dumps({
                    "week": week,
                    "quiz": {
                        "id": i,
                        "question": q,
                        "options": opts,
                        "correct_idx": correct_idx
                    }
                }, ensure_ascii=False) + "\n")


    def quit(self):
        print("Closing driver")
        self.driver.quit()

    ##### ------- Full scraper ----------
    def scrape_quiz(self):
        correct = []
        questions = []
        answers = []
        while not self.quiz_is_over():
            question = self.scrape_active_question_text()
            answer_options = self.scrape_active_question_answers()
            questions.append(question)
            answers.append(answer_options)
            print(f"Brute-forcing question {len(correct)}")
            answer_idx = self.brute_force_answer(correct)
            correct.append(answer_idx)
        res = {
            "questions" : questions,
            "answers"   : answers,
            "correct"   : correct
        }
        return res
    
    def scrape_quiz_from_url(self, url):
        # Navigate to the quiz page
        self.driver.get(url)

        # Scrape Quiz
        quiz_id = self.get_quiz_id()
        print(f"Scraping quiz number {quiz_id}")
        res = self.scrape_quiz()
        
        # Save results
        self.save_quiz_to_jsonl(
            week=quiz_id, 
            res=res
            )

    def scrape_quizzes(self, max=None):
        self.collect_urls(max_quizzes=max)
        for url in self.quiz_urls:
            self.scrape_quiz_from_url(url)

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import json

# === Config ===
QUIZ_URL = "https://www.dr.dk/quiz/nyheder?id=67653b22bdc57085138441fa"
SAVE_PATH = 'results/jsonl_test.jsonl'

### -------  Helper functions for interacting with quiz -------- 

def try_answer(driver, button_idx):
    question = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.question-container.active"))
    )

    selector = f'button.answer-button[data-index="{button_idx}"]'

    WebDriverWait(question, 5).until(
        lambda q: q.find_element(By.CSS_SELECTOR, selector)
    )

    button = question.find_element(By.CSS_SELECTOR, selector)

    #print(f"Trying answer {button_idx}")
    WebDriverWait(driver, 5).until(EC.element_to_be_clickable(button))
    button.click()

    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.feedback-wrapper"))
    )

    classes = button.get_attribute("class")
    #print(classes)
    
    # check if answer was correct 
    if classes == "answer-button correct":
        success = 1
    else:
        success = 0

    return driver, success

def answer_question(driver, button_idx):
    try:
        question = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.question-container.active"))
        )

        selector = f'button.answer-button[data-index="{button_idx}"]'

        WebDriverWait(question, 5).until(
            lambda q: q.find_element(By.CSS_SELECTOR, selector)
        )

        button = question.find_element(By.CSS_SELECTOR, selector)

        WebDriverWait(driver, 5).until(EC.element_to_be_clickable(button))
        
        #print(f"Clicking button {button_idx}")
        button.click()

        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.feedback-wrapper"))
        )

    except Exception as e:
        print("Error in answer_question:", e)
    finally:
        return driver

def go_to_next_question(driver):
    selector = (
        "#drn-newsquiz-page-quiz-wrapper > div > div.questions-container > "
        "div.question-container.active.correct.response > div.quiz-field > "
        "div.feedback-wrapper > button"
    )

    next_button = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
    )

    driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
    #print("Clicking 'next question' button via CSS selector")
    ActionChains(driver).move_to_element(next_button).click().perform()

    return driver

def scrape_active_question_text(driver):
    question_elem = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.question-container.active h2"))
    )
    return question_elem.text.strip()

def scrape_active_question_answers(driver):
    answers = []
    buttons = WebDriverWait(driver, 5).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.question-container.active button.answer-button"))
    )
    for i in range(3):
        answer =  buttons[i].text.strip()
        answers.append(answer)
    return answers


def click_correct_buttons(driver, button_idxs):
    for idx in button_idxs:
        driver = answer_question(driver, idx)
        driver = go_to_next_question(driver)
    return driver 

def brute_force_answer(driver, correct):
    for i in range(3):
        if i != 0:
            driver = click_correct_buttons(driver, correct)  # only replay after refresh

        driver, success = try_answer(driver, i)
        if success:
            driver = go_to_next_question(driver)
            return driver, i
        else:
            driver.refresh()

def next_quiz_exists(driver):
    elements = driver.find_elements(By.CSS_SELECTOR, "#drn-newsquiz-page-quiz-next")
    if elements:
        return(True)
    else:
        return(False)

def click_next_quiz(driver):
    next_quiz_btn = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "#drn-newsquiz-page-quiz-next"))
    )
    #print("Clicking 'Next Quiz' button")
    next_quiz_btn.click()


def get_quiz_id(driver):
    edition = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.newsquiz-header span.edition-text"))
    )
    id = edition.text.strip().split()[1]
    return id

def save_quiz_to_jsonl(path, res):
    with open(path, "a", encoding="utf-8") as f:
        for i, (q, opts, correct_idx) in enumerate(zip(res["questions"], res["answers"], res["correct"])):
            f.write(json.dumps({
                "id": i,
                "question": q,
                "options": opts,
                "correct_idx": correct_idx
            }, ensure_ascii=False) + "\n")

##### ------- Full scraper ----------
def scrape_quiz(driver):
    correct = []
    questions = []
    answers = []
    while len(correct) < 7:
        question = scrape_active_question_text(driver)
        answer_options = scrape_active_question_answers(driver)
        questions.append(question)
        answers.append(answer_options)
        print(f"Brute-forcing question {len(correct)}")
        driver, answer_idx = brute_force_answer(driver, correct)
        correct.append(answer_idx)
    res = {
        "questions" : questions,
        "answers"   : answers,
        "correct"   : correct
    }
    return res

# === Run ===
if __name__ == "__main__":
    # Set up Chrome options for headless mode
    chrome_options = Options()
    chrome_options.add_argument("--headless")

    # Load driver
    driver = webdriver.Chrome(options=chrome_options)

    # Navigate to the quiz page
    driver.get(QUIZ_URL)

    # Main loop for scraping multiple quizzes
    while True:
        # Scrape Quiz
        quiz_id = get_quiz_id(driver)
        print(f"Scraping quiz number {quiz_id}")
        res = scrape_quiz(driver)
        
        # Save results
        print(f"Saving results to: {SAVE_PATH}")
        save_quiz_to_jsonl(SAVE_PATH, res)
        
        # Go to next quiz if it exists
        if not next_quiz_exists(driver):
            break
        click_next_quiz(driver)

    print("No next quiz found")
    print("Closing driver")
    driver.quit()
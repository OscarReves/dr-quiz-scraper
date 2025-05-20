from src import scrape_all_quizzes

start_url = 'https://www.dr.dk/quiz/nyheder?id=67c95d63d98de5cce7a5f8e8' # week 10

if __name__ == "__main__":
    scrape_all_quizzes(start_url=start_url)
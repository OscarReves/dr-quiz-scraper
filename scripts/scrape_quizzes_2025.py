from src.scraper import QuizScraper
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("n", help="Maximum amount of quizzes to scrape",
                        type=int, default=None)
    args = parser.parse_args()
    scraper = QuizScraper()
    scraper.scrape_quizzes(max=args.n)
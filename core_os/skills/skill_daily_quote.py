import random


def register() -> dict:
    return {
        "name": "daily_quote",
        "description": "Returns a random motivational quote from a curated collection",
        "version": "1.0.0",
        "author": "M.I.L.L.A.",
        "commands": ["/daily_quote"],
    }


def execute(payload: dict) -> dict:
    try:
        quotes = [
            "The only way to do great work is to love what you do. — Steve Jobs",
            "Believe you can and you're halfway there. — Theodore Roosevelt",
            "It does not matter how slowly you go as long as you do not stop. — Confucius",
            "The future belongs to those who believe in the beauty of their dreams. — Eleanor Roosevelt",
            "Success is not final, failure is not fatal: it is the courage to continue that counts. — Winston Churchill",
        ]

        quote = random.choice(quotes)

        return {
            "ok": True,
            "quote": quote,
            "message": quote,
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }
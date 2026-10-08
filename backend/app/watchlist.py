"""Watchlist seed universe — whale-consensus + trending + callout names.

Mints verified 2026-10-05/06 via DexScreener/GeckoTerminal/RugCheck.
Names WITHOUT a verified mint (pill, fone, ZCAT, OCTO, COCKROACH, ALLINU,
e/acc) are deliberately excluded — never trade or display a token whose
contract you cannot confirm. They can be added once verified.
M1 will add persistence + CRUD; for M0 this static seed is served as-is.
"""

WATCHLIST: list[dict] = [
    {"symbol": "Agency", "name": "Agency", "mint": "7VertkgF9KLhxxJXHX6uaWuoYZTP9LdGj2bWmVXVpump"},
    {"symbol": "STONK", "name": "STONK", "mint": "6GmAFSYs4gk3FDao5FzzySQpPZaWsa4rUJHacpMpUNgx"},
    {"symbol": "PUMP", "name": "Pump", "mint": "pumpCmXqMfrsAkQ5r49WcJnRayYRqmXz6ae8H7H9Dfn"},
    {"symbol": "HOOKED", "name": "Hooked", "mint": "C1mBfBoDkwWfd6uTFZp62ARHLjeVp3bDpCDMfMZtPngE"},
    {"symbol": "HIGGS", "name": "Higgspad", "mint": "DoVAVzViX8Bjy3r15nwikSaSbzE6dV4ovd28aWpJpump"},
    {"symbol": "Human", "name": "Team Human", "mint": "8nPoBHiBM6pybxMws9PA2JRb9BjkppBfqcZGmot4DMBC"},
    {"symbol": "CRAWL", "name": "CRAWLNET", "mint": "BXoHJddsWJLHtAopeiSbKUSELsu8hSFMs8baGMDkpump"},
    {"symbol": "SI", "name": "Super Inu", "mint": "DEW9dSN6QpWyNthphCpMmAbZP1Q4cEKR9xQXAri98WDP"},
    {"symbol": "baton", "name": "baton", "mint": "Hg5Ja55T5wESq4vyFoiVCMeHXtGyVA69X2UHq8hgpump"},
    {"symbol": "SWAP", "name": "Swaply", "mint": "GYFLuEAZMDdpUsTmyGdHstuXQC3JB9ZqtZbfktpppump"},
    {"symbol": "JEANPHIL", "name": "Jean Phil", "mint": "GTBxUiw6wJdmmkCGZgRHLyYxqu1vG4KtRpeox6yDpump"},
    {"symbol": "swordcat", "name": "cat wif sword", "mint": "5tCju6YNxHq5zrA6tGndr6F7TK42mpUFmeE31cSFpump"},
    {"symbol": "CARNAGE", "name": "CARNAGE", "mint": "AVKpeeWaCku3Mni5THbY4bkBnMrPzAEnnQKtP3wPpump"},
]


def mints() -> list[str]:
    return [w["mint"] for w in WATCHLIST]

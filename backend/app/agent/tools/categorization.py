class OperationTypeResolverTool:
    income_words = (
        "зачис",
        "поступ",
        "зарплат",
        "income",
        "Р·Р°С‡РёСЃ",
        "РїРѕСЃС‚СѓРї",
        "Р·Р°СЂРїР»Р°С‚",
    )
    expense_words = (
        "спис",
        "оплат",
        "покуп",
        "expense",
        "РЎРїРёСЃ",
        "РѕРїР»Р°С‚",
        "РџРѕРєСѓРї",
    )

    def resolve(self, text: str, fallback: str | None = None) -> str:
        low = text.lower()
        if any(word.lower() in low for word in self.income_words):
            return "income"
        if any(word.lower() in low for word in self.expense_words):
            return "expense"
        return fallback if fallback in {"income", "expense"} else "expense"


class CategoryClassifierTool:
    rules = {
        "products": (
            "перекр",
            "пятер",
            "пятёр",
            "магнит",
            "продукт",
            "grocery",
            "groceries",
            "products",
            "supermarket",
            "РїРµСЂРµРєСЂ",
            "РїСЏС‚РµСЂ",
            "РјР°РіРЅРёС‚",
            "РїСЂРѕРґСѓРєС‚",
        ),
        "transport": ("метро", "такси", "transport", "bus", "автобус", "РњРµС‚СЂРѕ", "С‚Р°РєСЃРё"),
        "restaurants": (
            "кафе",
            "ресторан",
            "coffee",
            "бар",
            "restaurant",
            "restaurants",
            "cafes",
            "РєР°С„Рµ",
            "СЂРµСЃС‚РѕСЂР°РЅ",
            "Р±Р°СЂ",
        ),
        "entertainment": ("кино", "театр", "развлеч", "game", "entertainment", "РєРёРЅРѕ", "С‚РµР°С‚СЂ", "СЂР°Р·РІР»РµС‡"),
        "health": ("аптека", "клиник", "здоров", "pharmacy", "health", "Р°РїС‚РµРєР°", "РєР»РёРЅРёРє", "Р·РґРѕСЂРѕРІ"),
        "transfers": ("перевод", "transfer", "transfers", "РїРµСЂРµРІРѕРґ"),
        "salary": ("зарплат", "salary", "Р·Р°СЂРїР»Р°С‚"),
    }

    def classify(self, comment: str, operation_type: str, fallback: str | None = None) -> str:
        low = comment.lower()
        for slug, words in self.rules.items():
            if any(word.lower() in low for word in words):
                return slug
        if fallback in self.rules or fallback == "other":
            return fallback
        if operation_type == "income":
            return "other"
        return "other"

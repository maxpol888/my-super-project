import random
import sys


def ask_int(prompt: str, low: int | None = None, high: int | None = None) -> int:
    while True:
        raw = input(prompt).strip()
        if raw.lower() in {"quit", "exit"}:
            print("До зустрічі!")
            sys.exit(0)
        try:
            val = int(raw)
        except ValueError:
            print("Введіть ціле число, будь ласка.")
            continue
        if low is not None and val < low:
            print(f"Число має бути не менше {low}.")
            continue
        if high is not None and val > high:
            print(f"Число має бути не більше {high}.")
            continue
        return val


def choose_difficulty() -> tuple[int, int]:
    print("Оберіть складність:")
    print("  1) Легко   — число 1..50, 10 спроб")
    print("  2) Нормально — число 1..100, 8 спроб")
    print("  3) Важко   — число 1..200, 7 спроб")
    while True:
        choice = input("Ваш вибір (1/2/3): ").strip()
        if choice in ("1", "2", "3"):
            if choice == "1":
                return 50, 10
            if choice == "2":
                return 100, 8
            return 200, 7
        print("Будь ласка, введіть 1, 2 або 3.")


def play_round() -> bool:
    max_val, tries = choose_difficulty()
    secret = random.randint(1, max_val)
    print(f"Я загадав число від 1 до {max_val}. Спробуйте вгадати!")
    for attempt in range(1, tries + 1):
        guess = ask_int(f"Спроба {attempt}/{tries}. Ваш варіант: ", 1, max_val)
        if guess == secret:
            print("Вітаю! Ви вгадали число!")
            break
        if guess < secret:
            print("Більше ⬆️")
        else:
            print("Менше ⬇️")
    else:
        print(f"На жаль, спроби закінчилися. Число було: {secret}")

    again = input("Зіграємо ще раз? (y/n): ").strip().lower()
    return again in {"y", "yes", "т", "так"}


def main() -> None:
    print("Вітання у грі 'Вгадай число'! (введіть 'quit' для виходу)")
    while play_round():
        pass
    print("Дякую за гру!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nДо зустрічі!")

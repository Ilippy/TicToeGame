import requests
from Config import TOKEN
URL = f"https://api.telegram.org/bot{TOKEN}/"


class TicTacToeGame:
    def __init__(self):
        self.board = self.create_board()
        self.turn = "X"
        self.winner = None

    @staticmethod
    def create_board():
        return [[" " for _ in range(3)] for _ in range(3)]

    def check_winner(self):
        for row in self.board:
            if row[0] == row[1] == row[2] != " ":
                return row[0]
        for col in range(3):
            if self.board[0][col] == self.board[1][col] == self.board[2][col] != " ":
                return self.board[0][col]
        if self.board[0][0] == self.board[1][1] == self.board[2][2] != " ":
            return self.board[0][0]
        if self.board[0][2] == self.board[1][1] == self.board[2][0] != " ":
            return self.board[0][2]
        if all(cell != " " for row in self.board for cell in row):
            return "Draw"
        return None

    def make_move(self, x, y):
        if self.board[x][y] != " " or self.winner:
            return False
        self.board[x][y] = self.turn
        self.turn = "O" if self.turn == "X" else "X"
        return True

    def make_computer_move(self):
        print(self.board)
        best_score = float('-inf')
        best_move = None
        for i in range(3):
            for j in range(3):
                if self.board[i][j] == " ":
                    self.board[i][j] = "O"
                    score = self.minimax(False)
                    print(i, j, score)
                    self.board[i][j] = " "
                    if score > best_score:
                        best_score = score
                        best_move = (i, j)
        if best_move:
            self.make_move(*best_move)

    def minimax(self, is_maximizing):
        result = self.check_winner()
        if result == "O":
            return 1
        elif result == "X":
            return -1
        elif result == "Draw":
            return 0
        if is_maximizing:
            best_score = float('-inf')
            for i in range(3):
                for j in range(3):
                    if self.board[i][j] == " ":
                        self.board[i][j] = "O"
                        score = self.minimax(False)
                        self.board[i][j] = " "
                        best_score = max(score, best_score)
        else:
            best_score = float('inf')
            for i in range(3):
                for j in range(3):
                    if self.board[i][j] == " ":
                        self.board[i][j] = "X"
                        score = self.minimax(True)
                        self.board[i][j] = " "
                        best_score = min(score, best_score)
        return best_score

    def get_board(self):
        return "\n".join([" | ".join(row) for row in self.board])


# Отправка текстового сообщения
def send_message(chat_id, text):
    url = URL + "sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, data=payload)


def send_board(chat_id, game, end_game=False):
    buttons = []
    for i in range(3):
        row = []
        for j in range(3):
            # Используем крупные символы для отображения клеток
            cell_text = "⬛️" if game.board[i][j] == " " else ("❌" if game.board[i][j] == "X" else "⭕️")

            # Кнопки: активные только если клетка пустая и игра не окончена
            if end_game or game.board[i][j] != " ":
                row.append({"text": cell_text, "callback_data": "ignore"})  # Неактивная кнопка для занятой клетки
            else:
                row.append({"text": cell_text, "callback_data": f"/move {i} {j}"})  # Активная кнопка для пустой клетки
        buttons.append(row)

    # Добавляем кнопку "Play Again" при завершении игры или "невидимую" кнопку, если игра не завершена
    if end_game:
        buttons.append([{"text": "Play Again", "callback_data": "/play"}])

    # Формируем клавиатуру с обновленными кнопками
    keyboard = {"inline_keyboard": buttons}
    url = URL + "sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": "Ваш ход!" if not end_game else f"Игра окончена. Побеждает: {game.winner}",
        "reply_markup": keyboard
    }
    requests.post(url, json=payload)


# Обработка хода игрока
def handle_move(chat_id, game, move):
    x, y = move
    if not game.make_move(x, y):
        send_message(chat_id, "Неверный ход. Попробуйте другую клетку.")
        return
    game.winner = game.check_winner()
    if game.winner:
        send_board(chat_id, game, end_game=True)
        games.pop(chat_id)
        return

    # Ход компьютера и проверка победителя
    game.make_computer_move()
    game.winner = game.check_winner()
    if game.winner:
        send_board(chat_id, game, end_game=True)
        games.pop(chat_id)
    else:
        send_board(chat_id, game)


# Обработка inline-кнопок от Telegram
def handle_callback_query(callback_query):
    chat_id = callback_query["message"]["chat"]["id"]
    data = callback_query["data"]

    if data == "/play":
        games[chat_id] = TicTacToeGame()
        send_board(chat_id, games[chat_id])
    elif data.startswith("/move"):
        if chat_id not in games:
            send_message(chat_id, "Сначала начните игру с помощью команды /play.")
            return
        try:
            x, y = map(int, data.split()[1:])
            handle_move(chat_id, games[chat_id], (x, y))
        except (ValueError, IndexError):
            send_message(chat_id, "Неверный формат хода.")


# Получение обновлений
def get_updates(offset=None):
    url = URL + "getUpdates"
    params = {"timeout": 100, "offset": offset}
    response = requests.get(url, params=params)
    return response.json()


# Основной цикл бота
games = {}


def main():
    offset = None
    while True:
        updates = get_updates(offset)
        if "result" in updates:
            for update in updates["result"]:
                offset = update["update_id"] + 1
                if "message" in update:
                    chat_id = update["message"]["chat"]["id"]
                    text = update["message"].get("text")
                    if text == "/start":
                        send_message(chat_id, "Привет! Это игра Крестики-Нолики. Введите /play, чтобы начать.")
                    elif text == "/play":
                        games[chat_id] = TicTacToeGame()
                        send_board(chat_id, games[chat_id])
                elif "callback_query" in update:
                    handle_callback_query(update["callback_query"])


if __name__ == "__main__":
    main()

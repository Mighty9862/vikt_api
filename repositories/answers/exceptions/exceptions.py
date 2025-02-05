class AnswerNotFoundException(Exception):
    def __init__(self, message: str = "Такого ответа не существует"):
        self.message = message
        super().__init__(self.message)
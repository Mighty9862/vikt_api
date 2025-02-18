from repositories.base.exceptions.exceptions import BaseException


INCORRECT_PASSWORD_EXCEPTION_DETAIL: str = "Неправильные пароль и/или почта"

# Ошибка неправильного пароля
class IncorrectPasswordException(BaseException):
    status: int = 400
    detail: str = INCORRECT_PASSWORD_EXCEPTION_DETAIL

    def __init__(self):
        super().__init__(status=self.status, detail=self.detail)


# Ошибка неправильного типа токена, access and refresh
class TokenTypeException(BaseException):
    status: int = 400

    def __init__(self, token_type: str):
        self.detail: str = f"Ожидается токен с типом {token_type}"
        super().__init__(status=self.status, detail=self.detail)

# Ошибка неправильной структуры токена или истечения времени существования токена
class InvalidTokenException(BaseException):
    status: int = 401

    def __init__(self, error_messsage: str):
        self.detail: str = f"Invaid Token Error: {error_messsage}"
        super().__init__(status=self.status, detail=self.detail)
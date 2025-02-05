from repositories.base.exceptions.exceptions import BaseException


INCORRECT_PASSWORD_EXCEPTION_DETAIL: str = "Неправильные пароль и/или почта"

# Ошибка неправильного пароля
class IncorrectPasswordException(BaseException):
    status: int = 400
    detail: str = INCORRECT_PASSWORD_EXCEPTION_DETAIL

    def __init__(self):
        super().__init__(status=self.status, detail=self.detail)
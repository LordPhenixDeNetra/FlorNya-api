from fastapi import HTTPException


class UnauthorizedError(HTTPException):
    def __init__(self, detail: str = "unauthorized"):
        super().__init__(status_code=401, detail=detail)


class ForbiddenError(HTTPException):
    def __init__(self, detail: str = "forbidden"):
        super().__init__(status_code=403, detail=detail)


class NotFoundError(HTTPException):
    def __init__(self, detail: str = "not_found"):
        super().__init__(status_code=404, detail=detail)

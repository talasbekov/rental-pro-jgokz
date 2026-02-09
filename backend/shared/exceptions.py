class AppError(Exception):
    def __init__(self, message: str, code: str = "APP_ERROR") -> None:
        self.message = message
        self.code = code
        super().__init__(self.message)


class BookingConflictError(AppError):
    def __init__(self, message: str = "Booking conflict") -> None:
        super().__init__(message=message, code="BOOKING_CONFLICT")

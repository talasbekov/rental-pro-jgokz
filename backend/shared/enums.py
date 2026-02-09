from enum import Enum


class BookingStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"


class PaymentMethod(str, Enum):
    kaspi = "kaspi"
    card = "card"

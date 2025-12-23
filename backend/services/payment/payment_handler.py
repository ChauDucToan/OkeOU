from abc import ABC, abstractmethod
from backend import db

from backend.models import BookingStatus, PaymentStatus, Booking, Receipt
from backend.utils import payment_utils
from backend.daos import session_daos


class PaymentHandler(ABC):
    @abstractmethod
    def init_payment_and_get_amount(self, request_data, session_data, payment_method, ref):
        pass
    @abstractmethod
    def get_payment_status(self, status):
        pass

    @abstractmethod
    def update_db(self, ref, status):
        pass

class BookingHandler(PaymentHandler):
    def init_payment_and_get_amount(self, request_data, session_data, payment_method, ref):
        booking_id = request_data.get('booking_id')
        booking = Booking.query.filter_by(id=booking_id).first()
        booking.ref = ref
        db.session.commit()
        amount = booking.deposit_amount
        return amount

    def get_payment_status(self, status):
        if status == "SUCCESS":
            return BookingStatus.CONFIRMED
        else:
            return BookingStatus.CANCELLED

    def update_db(self, ref, status):
        pass

class CheckoutHandler(PaymentHandler):
    def init_payment_and_get_amount(self, request_data, session_data, payment_method, ref):
        bill_detail = session_data.get('bill_detail')
        if not bill_detail:
            raise ValueError("Phiên thanh toán hết hạn")
        session_id = bill_detail['session_id']
        receipt_id = Receipt.query.filter(Receipt.session_id == session_id).first().id
        payment_utils.update_receipt_ref(id=receipt_id, ref=ref)
        amount = bill_detail['final_total']
        return amount

    def get_payment_status(self, status):
        if status == "SUCCESS":
            return PaymentStatus.COMPLETED
        else:
            return PaymentStatus.FAILED
    def update_db(self, ref, status):
        status = self.get_payment_status(status)
        if status == PaymentStatus.COMPLETED:
            payment_utils.process_payment(session_id=session_daos.get_session_by_receipt_ref(ref=ref).id)
        payment_utils.change_receipt_status(ref=ref, status=status)

class PaymentHandlerFactory:
    @staticmethod
    def get_handler(type_name):
        handlers = {
            'CHECKOUT': CheckoutHandler,
            'BOOKING': BookingHandler,
        }
        handler = handlers.get(type_name.upper())
        return handler()
from abc import ABC, abstractmethod
from backend import db
from flask_login import current_user

from backend.models import BookingStatus, ReceiptStatus, Booking
from backend.utils import booking_utils, payment_utils
from daos import session_daos


class PaymentHandler(ABC):
    @abstractmethod
    def init_payment_and_get_amout(self, request_data, session_data, payment_method, ref):
        pass
    @abstractmethod
    def get_payment_status(self, status):
        pass

    @abstractmethod
    def update_db(self, ref, status):
        pass

class BookingHandler(PaymentHandler):
    def init_payment_and_get_amout(self, request_data, session_data, payment_method, ref):
        booking_id = request_data.get('booking_id')
        booking = Booking.query.filter_by(id=booking_id).first()
        booking.ref = ref
        amount = booking.deposit_amount
        db.session.commit()
        return amount

    def get_payment_status(self, status):
        if status == "SUCCESS":
            return BookingStatus.CONFIRMED
        else:
            return BookingStatus.CANCELLED

    def update_db(self, ref, status):
        status = self.get_payment_status(status)
        booking = Booking.query.filter_by(ref=ref).first()
        if status == BookingStatus.CONFIRMED:
            booking_utils.confirm_booking(booking_id=booking.id)
        else:
            # Doi trang thai booking ve cacelled
            booking.booking_status = BookingStatus.CANCELLED
            db.session.commit()

class CheckoutHandler(PaymentHandler):
    def init_payment_and_get_amout(self, request_data, session_data, payment_method, ref):
        bill_detail = session_data.get('bill_detail')
        if not bill_detail:
            raise ValueError("Phiên thanh toán hết hạn")
        session_id = bill_detail['session_id']
        payment_utils.create_receipt(session_id=session_id,
                                     staff_id=current_user.id, payment_method=payment_method,
                                     ref=ref)
        amount = bill_detail['final_total']
        return amount

    def get_payment_status(self, status):
        if status == "SUCCESS":
            return ReceiptStatus.COMPLETED
        else:
            return ReceiptStatus.FAILED
    def update_db(self, ref, status):
        status = self.get_payment_status(status)
        if status == ReceiptStatus.COMPLETED:
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
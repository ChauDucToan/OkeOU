from abc import ABC, abstractmethod

from backend import db

from backend.models import PaymentStatus, Receipt, Transaction, TransactionStatus

from backend.utils import payment_utils
from backend.daos import session_daos
from backend.utils.session_utils import finish_session


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
        receipt = Receipt(
            id=ref,
            session_id=request_data.get('session_id'),
            status=PaymentStatus.PENDING,
        )
        db.session.add(receipt)
        try:
            db.session.commit()
        except Exception as ex:
            db.session.rollback()
            raise ex
        return request_data.get('amount')

    def get_payment_status(self, status):
        if status == "SUCCESS":
            return TransactionStatus.COMPLETED
        else:
            return TransactionStatus.FAILED

    def update_db(self, ref, status):
        transaction = Transaction.query.filter_by(receipt_id=ref).first()
        if not transaction:
            return
        transaction.status = TransactionStatus.COMPLETED if status == "COMPLETED" else TransactionStatus.FAILED

        try:
            db.session.commit()
        except Exception as ex:
            db.session.rollback()
            print(str(ex))

class CheckoutHandler(PaymentHandler):
    def init_payment_and_get_amount(self, request_data, session_data, payment_method, ref):
        bill_detail = session_data.get('bill_detail')
        if not bill_detail:
            raise ValueError("Phiên thanh toán hết hạn")
        session_id = bill_detail['session_id']
        receipt_id = Receipt.query.filter(Receipt.session_id == session_id).first().id
        payment_utils.update_transaction_ref(id=receipt_id, ref=ref, amount = bill_detail['final_total'])
        amount = bill_detail['final_total']
        finish_session(session_id)
        return amount

    def get_payment_status(self, status):
        if status == "SUCCESS":
            return PaymentStatus.COMPLETED
        else:
            return PaymentStatus.FAILED

    def update_db(self, ref, status):
        status = self.get_payment_status(status)
        if status == PaymentStatus.COMPLETED:
            payment_utils.process_payment(session_id=session_daos.get_session_by_transaction_ref(ref=ref).id)
        payment_utils.change_transaction_status(ref=ref, status=status)


class PaymentHandlerFactory:
    @staticmethod
    def get_handler(type_name):
        handlers = {
            'CHECKOUT': CheckoutHandler,
            'BOOKING': BookingHandler,
        }
        handler = handlers.get(type_name.upper())
        return handler()

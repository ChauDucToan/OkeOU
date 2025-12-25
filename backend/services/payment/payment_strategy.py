import os
import uuid
import urllib
import requests
import hmac
import hashlib
from abc import abstractmethod, ABC
from datetime import datetime

from backend import app, db
from backend.models import PaymentMethod, TransactionStatus, Transaction
from backend.services.payment.payment_handler import PaymentHandlerFactory


class PaymentStrategy(ABC):
    def __init__(self, payment_type):
        self.payment_type = payment_type
        pass

    @abstractmethod
    def create_payment(self, amount, ref):
        pass

    @abstractmethod
    def verify_payment(self, data):
        pass

    @abstractmethod
    def get_payment_method(self):
        pass

    @abstractmethod
    def get_payment_status(self, data):
        pass

    def process_payment(self, data):
        if self.verify_payment(data):
            ref, status = self.get_payment_status(data)
            handler = PaymentHandlerFactory.get_handler(self.payment_type)
            handler.update_db(ref, status)


class CashPaymentStrategy(PaymentStrategy):
    def create_payment(self, amount, ref):
        return {
            "payUrl": "http://localhost:5000/",
        }

    def verify_payment(self, data):
        return True

    def get_payment_method(self):
        return PaymentMethod.CASH

    def get_payment_status(self, data):
        return data.get('ref'), "SUCCESS"


class MomoPaymentStrategy(PaymentStrategy):
    def __init__(self, payment_type):
        super().__init__(payment_type)
        self.accessKey = app.config["MOMO_ACCESS_KEY"]
        self.secretKey = app.config["MOMO_SECRET_KEY"]
        self.endpoint = "https://test-payment.momo.vn/v2/gateway/api/create"
        self.ipnUrl = f"https://uniramous-earline-colorational.ngrok-free.dev/api/ipn/momo/{payment_type}"
        self.redirectUrl = "http://localhost:5000/"

    def create_payment(self, amount, ref):
        partnerCode = "MOMO"
        orderId = str(ref)
        requestId = str(uuid.uuid4())
        extraData = str(ref)

        raw_signature = (f"accessKey={self.accessKey}&amount={amount}&extraData={extraData}"
                         f"&ipnUrl={self.ipnUrl}&orderId={orderId}&orderInfo=Thanh toan Momo"
                         f"&partnerCode={partnerCode}&redirectUrl={self.redirectUrl}"
                         f"&requestId={requestId}&requestType=payWithMethod")

        h = hmac.new(bytes(self.secretKey, 'ascii'), bytes(raw_signature, 'utf-8'), hashlib.sha256)
        signature = h.hexdigest()

        data = {
            'partnerCode': partnerCode,
            'partnerName': "Test",
            'storeId': "MomoTestStore",
            'requestId': requestId,
            'amount': str(amount),
            'orderId': orderId,
            'orderInfo': "Thanh toan Momo",
            'redirectUrl': self.redirectUrl,
            'ipnUrl': self.ipnUrl,
            'lang': "vi",
            'extraData': extraData,
            'requestType': "payWithMethod",
            'signature': signature,
            'autoCapture': True
        }

        try:
            response = requests.post(self.endpoint, json=data)
            if response.status_code == 200:
                return response.json()
            else:
                return {'payUrl': None, 'err_msg': response.text}
        except Exception as e:
            return {'payUrl': None, 'err_msg': str(e)}

    def verify_payment(self, data):
        keys = [
            "accessKey", "amount", "extraData", "message", "orderId",
            "orderInfo", "orderType", "partnerCode", "payType", "requestId",
            "responseTime", "resultCode", "transId"
        ]

        raw_parts = []
        for k in keys:
            if k == "accessKey":
                raw_parts.append(f"{k}={self.accessKey}")
            else:
                value = data.get(k)
                if value is None:
                    value = ""
                raw_parts.append(f"{k}={str(value)}")

        raw_signature = "&".join(raw_parts)

        h = hmac.new(bytes(self.secretKey, 'ascii'), bytes(raw_signature, 'utf-8'), hashlib.sha256)
        my_signature = h.hexdigest()

        return hmac.compare_digest(my_signature, data.get('signature', ''))

    def get_payment_status(self, data):
        status = str(data.get('resultCode'))
        ref = data.get('orderId')

        if status == '0':
            return ref, "SUCCESS"
        else:
            return ref, "FAILED"

    def get_payment_method(self):
        return PaymentMethod.MOMO


class VNPayPaymentStrategy(PaymentStrategy):
    def __init__(self, payment_type):
        super().__init__(payment_type=payment_type)
        self.vnp_TmnCode = os.getenv("VNP_TMN_CODE")
        self.vnp_HashSecret = os.getenv("VNP_HASH_SECRET")
        self.vnp_Url = "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html"
        self.vnp_ReturnUrl = f"http://localhost:5000/api/ipn/vnpay/{payment_type}"

    def create_payment(self, amount, ref):
        ip_addr = '127.0.0.1'
        vnp_Amount = int(float(amount) * 100)
        inputData = {
            "vnp_Version": "2.1.0",
            "vnp_Command": "pay",
            "vnp_TmnCode": self.vnp_TmnCode,
            "vnp_Amount": str(vnp_Amount),
            "vnp_CreateDate": datetime.now().strftime('%Y%m%d%H%M%S'),
            "vnp_CurrCode": "VND",
            "vnp_IpAddr": ip_addr,
            "vnp_Locale": "vn",
            "vnp_OrderInfo": "Thanh toán VNPay",
            "vnp_OrderType": "other",
            "vnp_ReturnUrl": self.vnp_ReturnUrl,
            "vnp_TxnRef": ref,
        }

        inputData = sorted(inputData.items())
        query_string = urllib.parse.urlencode(inputData)

        if self.vnp_HashSecret:
            secure_hash = hmac.new(
                bytes(self.vnp_HashSecret, 'utf-8'),
                bytes(query_string, 'utf-8'),
                hashlib.sha512
            ).hexdigest()
            query_string += f"&vnp_SecureHash={secure_hash}"

        payment_url = f"{self.vnp_Url}?{query_string}"

        return {
            "payUrl": payment_url,
        }

    def verify_payment(self, data):
        vnp_SecureHash = data.get('vnp_SecureHash')

        inputData = {}
        for key in data:
            if key.startswith('vnp_') and key not in ('vnp_SecureHash', 'vnp_SecureHashType'):
                inputData[key] = data[key]

        inputData = sorted(inputData.items())
        query_string = urllib.parse.urlencode(inputData)

        secure_hash = hmac.new(
            bytes(self.vnp_HashSecret, 'utf-8'),
            bytes(query_string, 'utf-8'),
            hashlib.sha512
        ).hexdigest()

        is_valid_signature = (secure_hash == vnp_SecureHash)
        return is_valid_signature

    def get_payment_status(self, data):
        status = str(data.get('vnp_ResponseCode'))
        ref = data.get('vnp_TxnRef')

        if status == '00':
            return ref, "SUCCESS"
        else:
            return ref, "FAILED"

    def get_payment_method(self):
        return PaymentMethod.VNPAY


class ZaloPayPaymentStrategy(PaymentStrategy):
    def __init__(self, payment_type):
        super().__init__(payment_type=payment_type)
        self.app_id = os.getenv("ZLP_MERCHANT_APP_ID")
        self.key1 = os.getenv("ZLP_MERCHANT_KEY1")
        self.key2 = os.getenv("ZLP_MERCHANT_KEY2")
        self.endpoint = os.getenv("ZLP_MERCHANT_ENDPOINT")
        self.gateway_endpoint = os.getenv("ZLP_MERCHANT_GATEWAY_ENDPOINT")
        self.redirect_url = os.getenv("ZLP_REDIRECT_URL") + payment_type

    def get_mac(self, data, key):
        mac = hmac.new(
            key.encode("utf-8"),
            data.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        return mac

    def create_payment(self, amount, ref):
        inputData = {
            "app_id": int(self.app_id),
            "app_user": "OkeOU",
            "app_trans_id": f"{datetime.now().strftime('%y%m%d')}_{ref.replace('-', '')}",
            "app_time": int(datetime.now().timestamp() * 1000),
            "expire_duration_seconds": 900,
            "description": f"Giao dịch thanh toán cho {ref}",
            "amount": int(amount),
            "bank_code": "",
            "embed_data": "{\"preferred_payment_method\": [\"zalopay_wallet\"], \"redirecturl\": \"" + self.redirect_url + "\"}",
            "item": '[]',
        }

        data = "|".join([
            str(inputData["app_id"]),
            inputData["app_trans_id"],
            inputData["app_user"],
            str(inputData["amount"]),
            str(inputData["app_time"]),
            inputData["embed_data"],
            inputData["item"],
        ])
        
        inputData["mac"] = self.get_mac(data, self.key1)

        print(inputData)

        transaction = Transaction(
            id = inputData["app_trans_id"],
            receipt_id = ref,
            amount = float(amount),
            status = TransactionStatus.PENDING
        )

        try:
            db.session.add(transaction)
            db.session.commit()

            response = requests.post(self.endpoint + "/create", json=inputData)
            if response.status_code == 200:
                payUrl = response.json().get("order_url")
                return {"payUrl": payUrl}
            else:
                return {'payUrl': None, 'err_msg': response.text}
        except Exception as e:
            return {'payUrl': None, 'err_msg': str(e)}

    def verify_payment(self, data):
        raw_data = "|".join([
            data["appid"],
            data["apptransid"],
            data["pmcid"],
            data["bankcode"],
            data["amount"],
            data["discountamount"],
            data["status"],
        ])

        mac = self.get_mac(raw_data, self.key2)
        return hmac.compare_digest(mac, data['checksum'])

    def get_payment_method(self):
        return PaymentMethod.ZALOPAY

    def get_payment_status(self, data):
        ref = data['apptransid'].split('_')[1]
        ref = str(uuid.UUID(ref))

        if data['status'] == '1':
            return ref, "COMPLETED"
        else:
            return ref, "FAILED"

class PaymentStrategyFactory:
    @staticmethod
    def get_strategy(method_name, payment_type):
        strategies = {
            "CASH": CashPaymentStrategy,
            "MOMO": MomoPaymentStrategy,
            "VNPAY": VNPayPaymentStrategy,
            "ZALOPAY": ZaloPayPaymentStrategy,
        }

        strategy = strategies.get(method_name.upper())
        return strategy(payment_type)

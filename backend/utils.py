import hashlib


def hash_password(password: str) -> str:
    if not password:
        raise ValueError('Password cannot be empty')
    return str(hashlib.sha256(password.encode('utf-8')).hexdigest())

def stats_order(order):
    total_quantity, total_amount = 0, 0

    if order:
        for o in order.values():
            total_quantity += o['quantity']
            total_amount += o['quantity'] * o['price']

    return{
        'total_quantity': total_quantity,
        'total_amount': total_amount
    }

if __name__ == '__main__':
    print(hash_password('123'))
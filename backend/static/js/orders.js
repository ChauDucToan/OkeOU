// ==================Add to Order==================
function updateOrderBadge(total_quantity) {
    let badges = document.getElementsByClassName('order-counter')
    for (let b of badges)
        if (total_quantity > 0) {
            b.style.display = 'inline-block'
            b.innerText = total_quantity
        } else {
            b.style.display = 'none'
        }
}

function addToOrder(sessionId, id, image, name, price, amount) {
    fetch('/api/orders', {
        method: 'post',
        body: JSON.stringify({
            'session_id': sessionId,
            'id': id,
            'image': image,
            'name': name,
            'price': price,
            'amount': amount
        }),
        headers: {
            'Content-Type': 'application/json'
        }
    })
        .then(res => res.json()
            .then(data => ({status: res.status, body: data})))
        .then(result => {
            if (result.status === 200) {
                updateOrderBadge(result.body.total_quantity)
                location.reload()
            } else {
                alert(result.body.err_msg || 'Lỗi hệ thống')
            }
        });
}

// ==================Update Order==================
function updateOrder(sessionId, id, obj) {
    fetch(`/api/orders/${id}`, {
        method: 'put',
        body: JSON.stringify({
            'session_id': sessionId,
            'quantity': obj.value
        }),
        headers: {
            'Content-Type': 'application/json'
        }
    }).then(res => res.json().then(data => ({status: res.status, body: data})))
        .then(result => {
            if (result.status === 200) {
                let counter = document.getElementsByClassName('order-counter');
                for (let e of counter)
                    e.innerText = result.body.total_quantity;

                let amount = document.getElementsByClassName('order-amount');
                for (let a of amount)
                    a.innerText = `${result.body.total_amount.toLocaleString('en')} VND`;

                let row = document.getElementById(`cart${id}`);
                let price = row.querySelector('.order-product-amount').dataset.price;
                let itemAmount = Number(price) * obj.value;

                row.querySelector('.order-product-amount').innerText = itemAmount.toLocaleString('en');
            } else {
                alert(result.body.err_msg || 'Lỗi hệ thống')
                obj.value = obj.defaultValue;
            }
        })
}

function limitQuantity(input) {
    if (input.value > 30) input.value = 30
    if (input.value < 0) input.value = 1
}

function deleteOrder(sessionId, id) {
    if (confirm("Bạn có muốn xoá không?") === true) {
        fetch(`/api/orders/${id}`, {
            method: 'delete',
            body: JSON.stringify({
                'session_id': sessionId
            }),
            headers: {
                'Content-Type': 'application/json'
            }
        }).then(res => res.json()).then(data => {
            let counter = document.getElementsByClassName('order-counter');
            for (let e of counter)
                e.innerText = data.total_quantity;

            let amount = document.getElementsByClassName('order-amount');
            for (let a of amount)
                a.innerText = `${data.total_amount.toLocaleString('en')} VND`;

            let item = document.getElementById(`cart${id}`);
            item.style.display = 'none';

            if (data.total_quantity === 0)
                location.reload()
        })
    }
}

function orderProcess(sessionId) {
    if (confirm('Bạn có chắc chắn là đặt các dịch vụ này không?') === true) {
        fetch('/api/order_process', {
            method: 'post',
            body: JSON.stringify({
                'session_id': sessionId
            }),
            headers: {
                'Content-Type': 'application/json'
            }
        })
            .then(res => res.json()
                .then(data => ({status: res.status, body: data})))
            .then(result => {
                if (result.status === 200) {
                    location.reload()
                } else {
                    alert(result.body.err_msg || 'Lỗi hệ thống')
                }
            })
    }
}
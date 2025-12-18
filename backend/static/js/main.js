function addToOrder(id, image, name, price){
    fetch('/api/orders',{
        method: 'post',
        body: JSON.stringify({
            'id': id,
            'image': image,
            'name': name,
            'price': price
        }),
        headers: {
            'Content-Type': 'application/json'
        }
    }).then(res => res.json()).then(data => {
        let elems = document.getElementsByClassName('order-counter')
        for ( let e of elems)
            e.innerText = data.total_quantity
    });
}

function updateOrder(id, obj){
    fetch(`/api/orders/${id}`, {
        method: 'put',
        body: JSON.stringify({
            'quantity': obj.value
        }),
        headers: {
            'Content-Type': 'application/json'
        }
    }).then(res => res.json()).then(data => {
        let counter = document.getElementsByClassName('order-counter');
        for ( let e of counter)
            e.innerText = data.total_quantity;

        let amount = document.getElementsByClassName('order-amount');
        for (let a of amount)
            a.innerText = `${data.total_amount.toLocaleString('en')} VND`;
    })
}

function deleteOrder(id) {
    if(confirm("Bạn có muốn xoá không?") === true){
        fetch(`/api/orders/${id}`, {
            method: 'delete'
        }).then(res => res.json()).then(data => {
            let counter = document.getElementsByClassName('order-counter');
            for ( let e of counter)
                e.innerText = data.total_quantity;

            let amount = document.getElementsByClassName('order-amount');
            for (let a of amount)
                a.innerText = `${data.total_amount.toLocaleString('en')} VND`;

            let item = document.getElementById(`cart${id}`);
            item.style.display = 'none';
        })
    }
}

function orderProcess(){
    if (confirm('Bạn có chắc chắn là đặt các dịch vụ này không?') === true){
        fetch('/api/order_process', {
            method: 'post',
        }).then(res => res.json()
            .then(data => ({ status: res.status, body: data })))
                .then(result => {
                                    if (result.status === 200) {
                                        location.reload()
                                    } else {
                                        alert(result.body.err_msg || 'Lỗi hệ thống')
                                    }
                                })
    }
}

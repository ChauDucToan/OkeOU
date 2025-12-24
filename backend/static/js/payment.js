document.getElementById('paymentForm').addEventListener('submit', async function (e) {
    e.preventDefault(); // Chặn form submit mặc định

    const formData = new FormData(this);
    const method = formData.get('payment_method');
    
    if (!method) {
        alert('Vui lòng chọn phương thức thanh toán');
        return;
    }

    await fetch(`/api/booking/update_status`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ booking_id: formData.get('booking_id'), status: 'CONFIRMED' })
    }).then(res => res.json()).then(resData => {
        if (resData.status) {
            formData.set('session_id', resData.session_id);
            formData.set('amount', resData.amount);
        }
    });

    const url = `/api/payment/create/${method}/booking`;

    try {
        const response = await fetch(url, {
            method: 'POST',
            body: formData // Gửi kèm booking_id trong body
        });

        const data = await response.json();

        if (response.ok) {
            print(data)
            if (data.order_url) {
                window.location.href = data.order_url;
            } else {
                // Hoặc chuyển hướng về trang thành công
                window.location.href = data.order_url;
            }
        } else {
            alert(data.message || 'Có lỗi xảy ra');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Lỗi kết nối server');
    }
});

window.addEventListener("load", function () {
    let remainingTime = parseInt(document.getElementById('remain_time').value);
    const timerElement = document.getElementById('countdown-timer');
    const timeoutModal = new bootstrap.Modal(document.getElementById('timeoutModal'));
    const payBtn = document.querySelector('button[type="submit"]');

    function updateTimerDisplay() {

        if (remainingTime <= 0) {
            clearInterval(timerInterval);
            timerElement.innerText = "00:00";

            payBtn.disabled = true;
            payBtn.innerText = "Hết hạn thanh toán";
            timeoutModal.show();
            return;
        }

        let m = Math.floor(remainingTime / 60);
        let s = remainingTime % 60;

        m = m < 10 ? '0' + m : m;
        s = s < 10 ? '0' + s : s;

        timerElement.innerText = `${m}:${s}`;

        if (remainingTime < 60) {
            timerElement.classList.remove('text-primary');
            timerElement.classList.add('text-danger');
        }

        remainingTime--;
    }

    updateTimerDisplay();
    const timerInterval = setInterval(updateTimerDisplay, 1000);
});
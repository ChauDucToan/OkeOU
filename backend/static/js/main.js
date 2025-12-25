window.addEventListener('scroll', function () {
    const navbar = document.getElementById('navbar');
    if (window.scrollY > 50) {
        navbar.classList.add('navbar-scrolled');
        navbar.classList.remove('glass-effect');
    } else {
        navbar.classList.remove('navbar-scrolled');
        navbar.classList.add('glass-effect');
    }
});

function pay(payment_type) {
    const paymentBtn = document.querySelector(".btn-payment.btn-primary");
    const method = paymentBtn ? paymentBtn.innerText.trim() : "CASH";

    let paidAmount = parseInt(document.getElementById("paidAmount").value) || 0;

    if (method === "CASH" && (paidAmount === 0 || isNaN(paidAmount))) {
        alert("Vui lòng nhập số tiền khách đưa!");
        return;
    }

    if (confirm("Bạn chắc chắn thanh toán?") === true) {
        let requestBody = new FormData;

        if (method === "CASH") {
            requestBody.set("amount", paidAmount);
        }

        fetch(`/api/payment/create/${method}/${payment_type}`, {
            method: "post",
            body: requestBody
        })
        .then((res) => res.json().then((data) => ({ status: res.status, body: data})))
        .then((result) => {
            if (result.status === 200) {
                window.location.href = result.body.payUrl
            } else {
                alert(result.body.err_msg || "Lỗi hệ thống!!!")
            }
        });
    }
}
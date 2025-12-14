function caculateBill(roomId) {
  //    alert('hello')
  fetch("/api/payment/caculate", {
    method: "post",
    body: JSON.stringify({
      room_id: roomId,
    }),
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((res) => {
      if (res.status !== 200) {
        console.error(res["error"]);
        alert("Hệ thống bị lỗi!");
      } else window.location.href = "/payment/";
    })
    .catch((err) => {
      console.error(err);
      alert("Hệ thống bị lỗi!");
    });
}

function pay() {
  const paymentBtn = document.querySelector(".btn-payment.btn-primary");
  const method = paymentBtn ? paymentBtn.innerText.trim() : "CASH";

  const sessionIdInput = document.getElementById("currentSessionId");
  const sessionId = sessionIdInput ? sessionIdInput.value : null;
  const customerMoney = document.getElementById("paidAmount").value;

  let paidAmount = parseInt(customerMoney) || 0;

  if (paidAmount === 0 || isNaN(paidAmount)) {
    alert("Vui lòng nhập số tiền khách đưa!");
    return;
  }

  if (confirm("Bạn chắc chắn thanh toán?") === true) {
    fetch("/api/pay", {
      method: "post",
      body: JSON.stringify({
        session_id: sessionId,
        payment_method: method,
        paid_amount: paidAmount,
      }),
      headers: {
        "Content-Type": "application/json",
      },
    })
      .then((res) => {
        if (!res.ok) {
          return res.json().then((err) => {
            throw new Error(err.err_msg);
          });
        }
        return res.json();
      })
      .then((data) => {
        alert(data.msg);
        window.location.href = "/rooms/";
      })
      .catch((err) => {
        alert(err.message);
      });
  }
}

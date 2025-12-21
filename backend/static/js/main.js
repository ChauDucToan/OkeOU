function caculateBill(roomId) {
  //    alert('hello')
  fetch("/api/payment/calculate", {
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

//Truyen vao payemnt_type de thay the cho nhieu loai thanh toan nhu la BOOKING cho dat phong, CHECKOUT cho thanh toan tra phong
function pay(payment_type) {
  const paymentBtn = document.querySelector(".btn-payment.btn-primary");
  const method = paymentBtn ? paymentBtn.innerText.trim() : "CASH";

  let paidAmount = parseInt(document.getElementById("paidAmount").value) || 0;

  if (method === "CASH" && (paidAmount === 0 || isNaN(paidAmount))) {
    alert("Vui lòng nhập số tiền khách đưa!");
    return;
  }

  if (confirm("Bạn chắc chắn thanh toán?") === true) {
      let requestBody = {};

      if (method === "CASH") {
          requestBody.paid_amount = paidAmount;
      }

      fetch(`/api/payment/create/${method}/${payment_type}`, {
          method: "post",
          body: JSON.stringify(requestBody),
          headers: {
            "Content-Type": "application/json",
          },
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
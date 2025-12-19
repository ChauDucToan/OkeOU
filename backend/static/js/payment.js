window.addEventListener("load", function() {
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
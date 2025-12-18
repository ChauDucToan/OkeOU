let occupiedRoomData = [];

function combineDateAndTime(dateStr, timeStr) {
    return new Date(`${dateStr}T${timeStr}:00`);
}

function loadTimeline() {
    const dateInput = document.getElementById('selectedDate').value;
    const tracksContainer = document.getElementById('timeline-tracks');

    const bookingForm = document.getElementById('bookingForm');
    if (!bookingForm) return;
    const roomId = bookingForm.getAttribute('data-room-id');

    if (!dateInput) return;

    tracksContainer.innerHTML = '';
    occupiedIntervals = [];

    fetch(`/api/bookings/occupies/${roomId}?date=${dateInput}`)
    .then(res => res.json())
    .then(data => {
        occupiedRoomData = data;
        drawOccupiedSlots(data);
    })
    .catch(err => console.error(err));
}

function drawOccupiedSlots(data) {
    const tracksContainer = document.getElementById('timeline-tracks');
    const dateInput = document.getElementById('selectedDate').value;

    for (let key in data) {
        const range = data[key]; // [start, end]
        const start = new Date(range[0]);
        const end = new Date(range[1]);

        // 1. Lưu vào biến toàn cục để tí nữa Validate dùng
        occupiedIntervals.push({ start: start, end: end });

        // 2. Tính toán để vẽ lên giao diện
        const dayStart = new Date(dateInput + 'T00:00:00');
        const dayEnd = new Date(dateInput + 'T23:59:59');

        let drawStart = start < dayStart ? dayStart : start;
        let drawEnd = end > dayEnd ? dayEnd : end;

        if (drawStart >= drawEnd) continue;

        const totalMinutesInDay = 24 * 60;
        const startMinutes = drawStart.getHours() * 60 + drawStart.getMinutes();
        const endMinutes = drawEnd.getHours() * 60 + drawEnd.getMinutes();
        
        const leftPercent = (startMinutes / totalMinutesInDay) * 100;
        const widthPercent = ((endMinutes - startMinutes) / totalMinutesInDay) * 100;

        // Tạo thẻ div đỏ
        const bar = document.createElement('div');
        bar.className = 'occupied-bar';
        bar.style.left = leftPercent + '%';
        bar.style.width = widthPercent + '%';
        
        // Tooltip hiển thị giờ
        const timeString = `${drawStart.getHours()}:${String(drawStart.getMinutes()).padStart(2, '0')} - ${drawEnd.getHours()}:${String(drawEnd.getMinutes()).padStart(2, '0')}`;
        bar.setAttribute('title', 'Đã đặt: ' + timeString);
        
        // (Tùy chọn) Nếu dùng Bootstrap Tooltip thì uncomment dòng dưới
        // bar.setAttribute('data-bs-toggle', 'tooltip');

        tracksContainer.appendChild(bar);
    }
}

function validateAndSubmit() {
    const dateInput = document.getElementById('selectedDate').value;
    const startInput = document.getElementsByName('start_time')[0].value;
    const endInput = document.getElementsByName('end_time')[0].value;
    const errorAlert = document.getElementById('error-alert');
    const errorMsg = document.getElementById('error-msg');

    console.log("Validating:", startInput, endInput);

    // Reset thông báo lỗi
    errorAlert.classList.add('d-none');

    if (!dateInput) {
        showError("Vui lòng chọn ngày trước.");
        return;
    }

    if (!startInput || !endInput) {
        showError("Vui lòng chọn đầy đủ thời gian.");
        return;
    }

    const userStart = combineDateAndTime(dateInput, startInput);
    const userEnd = combineDateAndTime(dateInput, endInput);

    if (userStart >= userEnd) {
        showError("Thời gian kết thúc phải sau thời gian bắt đầu.");
        return;
    }

    // Check thời gian trong quá khứ
    if (userStart < new Date()) {
            showError("Không thể đặt phòng trong quá khứ.");
            return;
    }

    // CHECK TRÙNG LỊCH (Client Side)
    let conflict = false;
    for (let interval of occupiedIntervals) {
        // Logic overlap: StartA < EndB && EndA > StartB
        if (userStart < interval.end && userEnd > interval.start) {
            conflict = true;
            break;
        }
    }

    if (conflict) {
        showError("Khung giờ bạn chọn đã bị trùng (xem thanh màu đỏ). Vui lòng chọn giờ khác.");
        return;
    }

    // Nếu mọi thứ OK -> Gửi dữ liệu đi (Gọi hàm API tạo booking của bạn)
    // Ở đây tôi giả lập việc submit form
    submitBookingAPI(); 
}

function showError(msg) {
    const errorAlert = document.getElementById('error-alert');
    const errorMsg = document.getElementById('error-msg');
    errorMsg.innerText = msg;
    errorAlert.classList.remove('d-none');
}

// Hàm gọi API thực tế (tái sử dụng từ code cũ của bạn)
function submitBookingAPI() {
    const formData = new FormData(document.getElementById('bookingForm'));
    fetch('/api/booking/confirm-create', { 
        method: 'POST',
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.code === 200) {
                // Redirect sang trang thanh toán
            window.location.href = `/booking/${data.booking_id}/payment`;
        } else {
            showError(data.msg || "Có lỗi xảy ra từ hệ thống.");
        }
    });
}

document.addEventListener("DOMContentLoaded", function(){
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('selectedDate').value = today;
    loadTimeline();
});
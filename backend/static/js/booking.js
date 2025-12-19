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
        const range = data[key];
        const start = new Date(range[0]);
        const end = new Date(range[1]);

        occupiedIntervals.push({ start: start, end: end });

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

        const bar = document.createElement('div');
        bar.className = 'occupied-bar';
        bar.style.left = leftPercent + '%';
        bar.style.width = widthPercent + '%';
        
        const timeString = `${drawStart.getHours()}:${String(drawStart.getMinutes()).padStart(2, '0')} - ${drawEnd.getHours()}:${String(drawEnd.getMinutes()).padStart(2, '0')}`;
        bar.setAttribute('title', 'Đã đặt: ' + timeString);
    
        tracksContainer.appendChild(bar);
    }
}

function validateAndSubmit() {
    const dateInput = document.getElementById('selectedDate').value;
    const startInput = document.getElementsByName('start_time')[0].value;
    const endInput = document.getElementsByName('end_time')[0].value;
    const errorAlert = document.getElementById('error-alert');

    console.log("Validating:", startInput, endInput);

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

    if (userStart < new Date()) {
            showError("Không thể đặt phòng trong quá khứ.");
            return;
    }

    let conflict = false;
    for (let interval of occupiedIntervals) {
        if (userStart < interval.end && userEnd > interval.start) {
            conflict = true;
            break;
        }
    }

    if (conflict) {
        showError("Khung giờ bạn chọn đã bị trùng (xem thanh màu đỏ). Vui lòng chọn giờ khác.");
        return;
    }


    submitBookingAPI(); 
}

function showError(msg) {
    const errorAlert = document.getElementById('error-alert');
    const errorMsg = document.getElementById('error-msg');
    errorMsg.innerText = msg;
    errorAlert.classList.remove('d-none');
}

function submitBookingAPI() {
    const formData = new FormData(document.getElementById('bookingForm'));
    
    const dateStr = document.getElementById('selectedDate').value;
    
    const timeStart = formData.get('start_time'); 
    const timeEnd = formData.get('end_time');


    const fullStartTime = `${dateStr} ${timeStart}:00`; 
    const fullEndTime = `${dateStr} ${timeEnd}:00`;

    formData.set('start_time', fullStartTime);
    formData.set('end_time', fullEndTime);
    
    fetch('/api/bookings/confirm', { 
        method: 'POST',
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 200) {
            window.location.href = `/bookings/${data.booking_id}/payment`;
        } else {
            showError(data.msg || "Có lỗi xảy ra từ hệ thống.");
        }
    });
}

window.addEventListener('load', function() {
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('selectedDate').value = today;
    loadTimeline();
});
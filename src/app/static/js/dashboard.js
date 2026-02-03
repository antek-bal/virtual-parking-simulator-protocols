const ws = new WebSocket(`ws://${window.location.host}/ws/stats`);
const eventsDiv = document.getElementById('events');
const revenueSpan = document.getElementById('revenue');
const statusSpan = document.getElementById('status');
const occupancySpan = document.getElementById('occupancy');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log("Data received:", data);

    let message = "";
    const time = new Date().toLocaleTimeString();

    switch(data.type) {
        case "VEHICLE_ENTRY":
            message = `<p class="entry">[${time}] Vehicle <b>${data.reg_no}</b> entered. Location: Floor ${data.floor}, Spot ${data.spot}</p>`;
            occupancySpan.innerText = parseInt(occupancySpan.innerText) + 1;
            break;

        case "VEHICLE_EXIT":
            message = `<p class="exit">[${time}] Vehicle <b>${data.reg_no}</b> exited from Spot ${data.spot}</p>`;
            let current = parseInt(occupancySpan.innerText);
            occupancySpan.innerText = current > 0 ? current - 1 : 0;
            break;

        case "PAYMENT_SUCCESS":
            message = `<p class="payment">[${time}] Payment received for <b>${data.reg_no}</b>: +${data.amount.toFixed(2)} PLN</p>`;
            revenueSpan.innerText = (parseFloat(revenueSpan.innerText) + data.amount).toFixed(2);
            break;

        case "EMERGENCY_STATUS":
            statusSpan.innerText = data.is_locked ? "LOCKED" : "OPEN";
            document.body.style.backgroundColor = data.is_locked ? "#ffdada" : "#f4f4f4";
            message = `<p class="emergency">[${time}] System Alert: ${data.msg}</p>`;
            break;
    }
    eventsDiv.innerHTML = message + eventsDiv.innerHTML;
};

ws.onopen = () => console.log("Connected to WebSocket");
ws.onclose = () => console.log("Disconnected from WebSocket");
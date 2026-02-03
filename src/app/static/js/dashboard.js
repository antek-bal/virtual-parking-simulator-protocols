const wsUrl = `ws://${window.location.host}/ws/stats`;
let socket = null;

const loginScreen = document.getElementById('login-screen');
const appScreen = document.getElementById('app-screen');
const eventsDiv = document.getElementById('events');
const revenueSpan = document.getElementById('revenue');
const statusSpan = document.getElementById('status');
const occupancySpan = document.getElementById('occupancy');

async function handleLogin() {
    const user = document.getElementById('username').value;
    const pass = document.getElementById('password').value;
    const errorMsg = document.getElementById('login-error');

    const credentials = btoa(user + ":" + pass);

    try {
        const res = await fetch('/login', {
            method: 'POST',
            headers: { 'Authorization': `Basic ${credentials}` }
        });

        if (res.ok) {
            loginScreen.classList.add('hidden');
            appScreen.classList.remove('hidden');

            initWebSocket();
            listActiveVehicles();
        } else {
            errorMsg.innerText = "Invalid credentials. Try admin/admin";
        }
    } catch (e) {
        errorMsg.innerText = "Connection error";
    }
}

async function handleLogout() {
    await fetch('/logout', { method: 'POST' });
    appScreen.classList.add('hidden');
    loginScreen.classList.remove('hidden');

    if (socket) {
        socket.close();
        socket = null;
    }
    location.reload();
}

function initWebSocket() {
    if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
        console.log("WebSocket connection already active");
        return;
    }

    if (socket) {
        socket.close();
    }

    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
        console.log("Connected to WebSocket");
    };

    socket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        console.log("WS Data:", data);

        let message = "";
        const time = new Date().toLocaleTimeString();

        switch(data.type) {
            case "VEHICLE_ENTRY":
                message = `<p class="entry">[${time}] <b>${data.reg_no}</b> entered. Floor ${data.floor}, Spot ${data.spot}</p>`;
                occupancySpan.innerText = parseInt(occupancySpan.innerText) + 1;
                listActiveVehicles();
                break;
            case "VEHICLE_UPDATED":
                message = `<p class="exit">[${time}] <b>${data.reg_no}</b> moved to Floor ${data.floor}</p>`;
                listActiveVehicles();
                break;
            case "VEHICLE_EXIT":
                message = `<p class="exit">[${time}] <b>${data.reg_no}</b> exited.</p>`;
                let current = parseInt(occupancySpan.innerText);
                occupancySpan.innerText = current > 0 ? current - 1 : 0;
                listActiveVehicles();
                break;
            case "PAYMENT_SUCCESS":
                message = `<p class="payment">[${time}] Paid: <b>${data.reg_no}</b> (+${data.amount} PLN)</p>`;
                revenueSpan.innerText = (parseFloat(revenueSpan.innerText) + data.amount).toFixed(2) + " PLN";
                listActiveVehicles();
                break;
            case "EMERGENCY_STATUS":
                statusSpan.innerText = data.is_locked ? "LOCKED" : "OPEN";
                document.body.style.backgroundColor = data.is_locked ? "#fee2e2" : "#f3f4f6";
                message = `<p class="emergency">[${time}] ${data.msg}</p>`;
                break;
        }
        if(message) eventsDiv.innerHTML = message + eventsDiv.innerHTML;
    };

    socket.onclose = () => {
        console.log("WebSocket disconnected");
        socket = null;
    };
}

async function manualEntry() {
    const regInput = document.getElementById('park_reg');
    const countryInput = document.getElementById('park_country');
    const floorInput = document.getElementById('park_floor');

    const reg = regInput.value;
    const country = countryInput.value;
    const floor = parseInt(floorInput.value);

    if (floor < 0 || floor > 4) {
        alert("Floor must be between 0 and 4");
        return;
    }

    const res = await fetch('/entry', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({registration_no: reg, country: country, floor: floor})
    });
    const data = await res.json();
    document.getElementById('parking-response').innerText = `Entry: ${JSON.stringify(data)}`;

    if (res.ok) {
        regInput.value = "";
        floorInput.value = "1";
    }
}

async function manualExit() {
    const regInput = document.getElementById('manage_reg');
    const reg = regInput.value;
    const country = "PL";

    const res = await fetch(`/entry/${country}/${reg}`, { method: 'DELETE' });
    const data = await res.json();
    document.getElementById('parking-response').innerText = `Exit: ${JSON.stringify(data)}`;

    if (res.ok) {
        regInput.value = "";
    }
}

async function updateFloor() {
    const regInput = document.getElementById('manage_reg');
    const reg = regInput.value;

    const newFloorInput = prompt("Enter new floor number (0-4):");
    if (newFloorInput === null) return;

    const newFloor = parseInt(newFloorInput);

    if (isNaN(newFloor) || newFloor < 0 || newFloor > 4) {
        alert("Floor must be between 0 and 4");
        return;
    }

    const res = await fetch(`/entry/PL/${reg}`, {
        method: 'PATCH',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({new_floor: newFloor})
    });
    const data = await res.json();
    document.getElementById('parking-response').innerText = `Move: ${JSON.stringify(data)}`;

    if (res.ok) {
        regInput.value = "";
    }
}

async function listActiveVehicles() {
    const res = await fetch('/vehicles');
    const vehicles = await res.json();

    const tbody = document.querySelector("#vehicles-table tbody");
    tbody.innerHTML = "";

    vehicles.forEach(v => {
        const isPaid = v.is_paid;
        const reg = v.vehicle.registration_no;
        const country = v.vehicle.country;

        let actionBtn = "";
        if (!isPaid) {
            actionBtn = `<button onclick="payForVehicle('${country}', '${reg}')" class="btn-warning" style="padding:2px 5px; font-size:12px;">Pay Now</button>`;
        } else {
            actionBtn = `<span style="color:green; font-weight:bold;">PAID</span>`;
        }

        const row = `
            <tr>
                <td><b>${reg}</b> (${country})</td>
                <td>Floor ${v.floor}, Spot ${v.spot_number}</td>
                <td>${isPaid ? 'Yes' : 'No'}</td>
                <td>${actionBtn}</td>
            </tr>
        `;
        tbody.innerHTML += row;
    });
}

async function payForVehicle(country, reg) {
    const infoRes = await fetch(`/payment/${country}/${reg}`);
    if (!infoRes.ok) { alert("Error fetching payment info"); return; }
    const info = await infoRes.json();

    if (confirm(`Confirm payment of ${info.fee} PLN for ${reg}?`)) {
        await fetch(`/payment/${country}/${reg}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({amount: info.fee})
        });
    }
}
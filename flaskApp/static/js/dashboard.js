document.addEventListener("DOMContentLoaded", () => {
    onLoad();
});

async function onLoad(){
    // update every 15sec
    async function loop() {
        try { await updateDashboard();
        } catch (err) {
            console.error("Error updating data:", err); }
        setTimeout(loop, 15000); 
    }
    await updateDashboard();
    loop();
}

async function updateDashboard(){

    // arduino port & status
    try{
        const response = await fetch("/api/arduino");
        if (!response.ok) throw new Error("Failed to fetch");
        const data = await response.json();
        const status_text = {"online": "Online",
                             "offline": "Offline",
                             "update": "Updating"}
        document.getElementById("statusText").innerText = status_text[data.status];
        document.getElementById("port").placeholder = data.port;
    } catch (err) {
        console.error("Error loading items:", err);
    }
}

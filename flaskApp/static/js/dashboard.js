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
        const status_text = {"online": ["Online", "#34a834"],
                             "offline": ["Offline", "#b72525"],
                             "update": ["Updating", "#8344b3"]}

        if (data.status == "update") {
            document.querySelectorAll('button[name="light"]').forEach(button => {
                button.disabled = true;});
        } else {
            document.querySelectorAll('button[name="light"]').forEach(button => {
                button.disabled = false;
        });}

        document.getElementById("statusText").innerText = status_text[data.status][0];
        document.getElementById("statusText").style.color = status_text[data.status][1];
        document.getElementById("port").innerText = data.port;
    } catch (err) {
        console.error("Error loading items:", err);
    }
}

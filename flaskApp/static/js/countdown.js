
document.addEventListener("DOMContentLoaded", () => {
     load();
});

async function load(){
    const response = await fetch('/api/time');
    const data = await response.json();
    scheduleRefresh(data.fish_interval);
}

function scheduleRefresh(interval) {
    const DAY_MAP = { sun: 0, mon: 1, tue: 2, wed: 3, thu: 4, fri: 5, sat: 6 };

    const now = new Date();
    const nyNow = new Date(
        now.toLocaleString('en-US', { timeZone: 'America/New_York' })
    );

    const targetDay = DAY_MAP[interval.day_of_week.toLowerCase()];
    let daysUntil = (targetDay - nyNow.getDay() + 7) % 7;
    const nextTarget = new Date(nyNow);
    nextTarget.setDate(nyNow.getDate() + daysUntil);
    nextTarget.setHours(interval.hour, interval.minute, interval.second, 0);
    if (nyNow >= nextTarget) {
        nextTarget.setDate(nextTarget.getDate() + 7);
    }
    const delayMs = nextTarget - nyNow;

    //console.log("Refresh in " + delayMs + "ms");
    startCountdown(delayMs);
    setTimeout(() => {
        location.reload();
    }, delayMs+1000);
}

function startCountdown(delayMs) {
    const endTime = Date.now() + delayMs;
    function pad(n) { return String(n).padStart(2, '0'); }

    function tick() {
        const diff = endTime - Date.now();
        const wrap = document.getElementById('countdown-wrap');

        if (diff <= 0) {
            ['days','hours','mins','secs'].forEach(id =>
                document.getElementById('cd-' + id).textContent = '00'
            );
            return;}

        const totalSecs = Math.floor(diff / 1000);
        const days  = Math.floor(totalSecs / 86400);
        const hours = Math.floor((totalSecs % 86400) / 3600);
        const mins  = Math.floor((totalSecs % 3600) / 60);
        const secs  = totalSecs % 60;

        document.getElementById('cd-days').textContent  = days;
        document.getElementById('cd-hours').textContent = pad(hours);
        document.getElementById('cd-mins').textContent  = pad(mins);
        document.getElementById('cd-secs').textContent  = pad(secs);

        if (wrap) wrap.classList.toggle('urgent', diff < 60000);
    }

    tick();
    setInterval(tick, 1000);
}
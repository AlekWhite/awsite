let selectedFishImg = null;

document.addEventListener("DOMContentLoaded", () => {
    loadFish();
});

function showLoading() {
    document.getElementById('loading_screen').style.display = 'flex';
    document.getElementById('app').hidden = true;
}

function hideLoading() {
    document.getElementById('loading_screen').style.display = 'none';
    document.getElementById('app').hidden = false;
}

async function loadFish() {
    showLoading();
    try {
        const response = await fetch('/api/fish');
        const data = await response.json();
        console.log(data);
        scheduleRefresh(data.fish_interval);
        const fishBox = document.getElementById('fish_box');
        const imageLoadPromises = [];
        fishBox.innerHTML = ''; 
        data.fish.forEach(fish => {

            const img = document.createElement('img');
            img.id = fish.name + "_fishImg";
            img.src = `/fish/${fish.name}.png`;
            img.alt = fish.name;
            img.classList.add('small_fish');
            img.style.cursor = 'pointer';
            img.addEventListener('click', () => set_main_fish(fish, img));

            const p = new Promise(resolve => {
                img.onload = resolve;
                img.onerror = resolve;
            });
            imageLoadPromises.push(p);
            fishBox.appendChild(img);
        });

        await Promise.all(imageLoadPromises);
        set_main_fish(data.fish[0], document.getElementById(data.fish[0].name + "_fishImg"))

    } catch (error) {
        console.error('Error loading fish:', error);
    } finally {
        hideLoading();
    }
}

function set_main_fish(fish, img) {
    if (selectedFishImg) selectedFishImg.classList.remove('selected');
    img.classList.add('selected');
    selectedFishImg = img;

    document.getElementById('fotw_img').src = `/fish/${fish.name}.png`;
    document.getElementById('fotw_name').innerText = fish.name;
    document.getElementById('fotw_link').href = fish.wiki_url;
    document.getElementById('fotw_link').innerText = fish.wiki_url;

    const rawDate = fish?.date;
    if (!rawDate) {
        console.error('Missing fish date');
        return;}
    const d = new Date(rawDate);
    const date_text = d.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        timezone: 'UTC'
    });

    const nowt = new Date();
    const now = Date.UTC(nowt.getUTCFullYear(), nowt.getUTCMonth(), nowt.getUTCDate());
    const diffDays = (now - d) / (1000 * 60 * 60 * 24);
    if (diffDays >= 0 && diffDays < 7){
        document.getElementById('fotw_title').innerText = "This week's fish:";
        document.getElementById('fotw_div').style.backgroundImage = "url('static/css/img/fish_bg.png')";
    } else {
        document.getElementById('fotw_title').innerText = `Week: ${date_text}:`;
        document.getElementById('fotw_div').style.backgroundImage = "url('static/css/img/blue_bg.png')";
    }
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

    console.log("Refresh in " + delayMs + "ms");
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
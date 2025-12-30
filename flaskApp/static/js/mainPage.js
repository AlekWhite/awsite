let selectedFishImg = null;

document.addEventListener("DOMContentLoaded", () => {
    loadFish();
    scheduleFridayRefresh();
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
        day: 'numeric'
    });

    const now = new Date();
    const diffDays = (now - d) / (1000 * 60 * 60 * 24);
    if (diffDays >= 0 && diffDays <= 7){
        document.getElementById('fotw_title').innerText = "This week's fish:";
        document.getElementById('fotw_div').style.backgroundImage = "url('static/css/img/fish_bg.png')";
    } else {
        document.getElementById('fotw_title').innerText = `Week: ${date_text}:`;
        document.getElementById('fotw_div').style.backgroundImage = "url('static/css/img/blue_bg.png')";
    }
}

function scheduleFridayRefresh() {
    const now = new Date();
    const nyNow = new Date(
        now.toLocaleString('en-US', { timeZone: 'America/New_York' })
    );
    const daysUntilFriday = (5 - nyNow.getDay() + 7) % 7;
    const nextFriday = new Date(nyNow);
    nextFriday.setDate(nyNow.getDate() + daysUntilFriday);
    nextFriday.setHours(0, 0, 0, 0);
    if (daysUntilFriday === 0 && nyNow >= nextFriday) {
        nextFriday.setDate(nextFriday.getDate() + 7);
    }
    const delayMs = nextFriday - nyNow;
    setTimeout(() => {
        location.reload();
    }, delayMs);
}

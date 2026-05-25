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

        const user_res = await fetch("/api/user");
        if (!user_res.ok){
            const mk_res = await fetch("/api/make_user");
            if (!mk_res.ok){
                console.log(mk_res.status);
            } 
        }

        const response = await fetch('/api/fish');
        const data = await response.json();
        
        const fishBox = document.getElementById('fish_box');
        fishBox.querySelector("#show").addEventListener("click", show_current_fish);
        fishBox.querySelector("#outer").style.backgroundImage = "url('static/css/img/blue_bg.png')";
        document.getElementById('fish_name_div').style.display = "none";
        document.getElementById('fish_link_div').style.display = "none";

        const imageLoadPromises = [];
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

    const fish_spot = document.getElementById('current_fish_div');
    const img_html = `<img id="fotw_img" style="width: 500px; height: 500px; margin: 10px;" src="/fish/${fish.name}.png" alt="fish">`;
    fish_spot.innerHTML = img_html;

    document.getElementById('fish_name_div').style.display = "flex";
    document.getElementById('fish_link_div').style.display = "flex";
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

async function show_current_fish(){
    const response = await fetch('/api/the_fish');
    const data = await response.json();
    if (data.fish) {
        const img = document.createElement('img');
        img.id = data.fish.name + "_fishImg";
        img.src = `/fish/${data.fish.name}.png`;
        img.alt = data.fish.name;
        img.classList.add('small_fish');
        img.style.cursor = 'pointer';
        img.addEventListener('click', () => set_main_fish(data.fish, img));
        set_main_fish(data.fish, img);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    load_data();
});

function showLoading() {
    document.getElementById('loading_screen').style.display = 'flex';
    document.getElementById('app').hidden = true;
}

function hideLoading() {
    document.getElementById('loading_screen').style.display = 'none';
    document.getElementById('app').hidden = false;
}

async function load_data(){
    showLoading();
    try{
        const response = await fetch('/api/leaderboard');
        const data = await response.json();
        const holder = document.getElementById("leads");
        const colors = ["rgb(112, 146, 185)", "rgb(112, 185, 128)", "rgb(201, 202, 130)"]
        for (let user of data){
            const vals = [ user.name,  user.final_score*-1 , user.guess_date];
            const stat = document.createElement('div');
            stat.classList.add("userDiv");
            for (let i=0; i<3; i++){
                const el = document.createElement("span");
                el.classList.add("mainText");
                el.innerText = vals[i];
                el.style.color = colors[i];
                stat.appendChild(el);
            }
            holder.appendChild(stat);
        }
    } catch (error) {
        console.error('Error loading leaderboard:', error);
    } finally{
        hideLoading();
    }
}
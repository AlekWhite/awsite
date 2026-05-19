
document.addEventListener("DOMContentLoaded", () => {
    take_guess("");
    show_fish_img();

    const guess_form_l = document.getElementById('guess_form');
    guess_form_l.addEventListener('submit', function(event) {
        event.preventDefault(); 
        take_guess(perp_guess(document.getElementById('guess').value));
        document.getElementById('guess').value = ""; 
        show_fish_img();
    });

});

function showLoading() {
    document.getElementById('loading_screen').style.display = 'flex';
    document.getElementById('app').hidden = true;
}

function hideLoading() {
    document.getElementById('loading_screen').style.display = 'none';
    document.getElementById('app').hidden = false;
}

function perp_guess(guess){
    if (/^[a-zA-Z ]+$/.test(guess)){
        return guess.toLowerCase();}
    return "";
}

function format_known_string(ks){
    let out = "";
    for (let c of ks){
        out += c + " ";}
    return out.trim();
}

async function show_fish_img(){
    let level = "guess_the_fish_16";
    const known_string = sessionStorage.getItem("known_string");
    if (known_string){
        const count = known_string.split('_').length - 1; 

        if (count == 0){
            const response = await fetch('/api/the_fish');
            const data = await response.json();
            if (data.fish.name) {
                level = data.fish.name;}

        } else if ( (count / known_string.length > 0.33) && (count / known_string.length < 0.66)){
            level = "guess_the_fish_32";
        } else if  (count / known_string.length <= 0.33)  {
            level = "guess_the_fish_64";
        }
    }

    const fish_spot = document.getElementById('fish_img');
    const img_html = `<img id="fotw_img" style="width: 500px; height: 500px; margin: 10px;" src="/fish/${level}.png" alt="fish">`;
    fish_spot.innerHTML = img_html;
}


async function take_guess(guess) {
    showLoading();
    try {

        const response = await fetch('/api/guess', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            credentials: 'same-origin',
            body: JSON.stringify({"guess": guess})
        },);
        if (!response.ok) {
            throw new Error("Failed to fetch");}
        const data = await response.json();
  
        let known_string = sessionStorage.getItem("known_string");
        if (!known_string){
            sessionStorage.setItem("known_string", data.hits);
            document.getElementById("known_string").innerText = format_known_string(data.hits);
        } else if (known_string.length != data.hits.length ) {
            sessionStorage.setItem("known_string", data.hits);
            sessionStorage.removeItem("attempts");
            document.getElementById("known_string").innerText = format_known_string(data.hits);
        } else {
            let known_array = known_string.split("");
            for (let i=0; i<known_array.length; i++){
                if ((known_array[i] == "_") && (data.hits[i] != "_")){
                    known_array[i] = data.hits[i];
                }
            }
            known_string = known_array.join("");
            document.getElementById("known_string").innerText = format_known_string(known_string);   
            sessionStorage.setItem("known_string", known_string);   
        }

        attempts = sessionStorage.getItem("attempts");
        if (attempts && (guess !== "")){
            document.getElementById("attempts").innerText = `Attempts: ${+attempts + 1}`; 
            sessionStorage.setItem("attempts", `${+attempts + 1}`) 
        } else if  (!attempts) {
            document.getElementById("attempts").innerText = `Attempts: ${0}`; 
            sessionStorage.setItem("attempts", "0")
        } else {
            document.getElementById("attempts").innerText = `Attempts: ${+attempts}`; 
        }

    } catch (error) {
        console.error('Error loading guess', error);
    } finally {
        hideLoading();
    }
}


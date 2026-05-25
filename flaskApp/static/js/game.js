
document.addEventListener("DOMContentLoaded", () => {
    get_user();
    take_guess("");
    show_fish_img();
    show_keyboard();
    document.getElementById("name_sub").addEventListener("click", name_change);
});

document.addEventListener('keydown', (event) => {
    console.log(event.key.length);
  if (event.key.length == 1) {
    button_types(event.key);
  } else if ( event.key == "Enter"){
    submit_guess(event);
  } else if (event.key == "Backspace"){
    button_types("back");
  }
});

function showLoading() {
    document.getElementById('loading_screen').style.display = 'flex';
    document.getElementById('app').hidden = true;
}

function hideLoading() {
    document.getElementById('loading_screen').style.display = 'none';
    document.getElementById('app').hidden = false;
}

function submit_guess(event) {
        event.preventDefault(); 
        take_guess(perp_guess(document.getElementById('guess').value));
        document.getElementById('guess').value = ""; 
}

function perp_guess(guess){
    if (/^[a-zA-Z ]+$/.test(guess)){
        return guess.toLowerCase();}
    return "";
}

function set_lb_status(status){
    let lb_stat = "Ineligible";
    if (status){
        lb_stat = "Eligible";
        document.getElementById("lb_status").style.color = "rgb(50, 135, 93)";
    } else {
        document.getElementById("lb_status").style.color = "rgb(192, 182, 92)";
    }
    document.getElementById("lb_status").innerText = `Leaderboard Status: ${lb_stat}`;
}

function show_letters(known_string){
    const holder = document.getElementById("letters");
    holder.innerHTML = "";
    let current_holder = "";
    const txt = document.createElement("span");
    txt.classList.add("mainText");
    txt.innerText = "Known letters:";
    holder.appendChild(txt);

    for (let i=0; i<known_string.length; i++){
        if ((known_string[i] == " ") || (i == 0)){
            current_holder = document.createElement("div");
            current_holder.classList.add("gameDiv");
            current_holder.style.flexDirection = "row";
            holder.appendChild(current_holder);
        } 
        if ((known_string[i] != "") && (known_string[i] != " ")){
            const letter = document.createElement('b');
            letter.innerText = known_string[i].toUpperCase();
            letter.classList.add("letter");
            if (known_string[i] != "_"){letter.style.background = "rgb(50, 135, 93)";}
            current_holder.appendChild(letter);
        }
    }
}

function button_types(letter){
    letter = perp_guess(letter);
    if (!letter) return;
    const holder = document.getElementById("letters_cur");
    const sub_holders = holder.children;

    if ((letter == "back") && (document.getElementById("guess").value.length > 0)){   
        document.getElementById("guess").value = document.getElementById("guess").value.slice(0, -1);
        
        if (sub_holders.length > 1){
            const last_holder = sub_holders[sub_holders.length-1];
            const last_holder_children = last_holder.children;

            if (last_holder_children.length == 0) {
                last_holder.remove();
            } else {
                last_holder_children[last_holder_children.length-1].remove();
            }
        }

    } else if (letter != "back") {
        document.getElementById("guess").value += letter.toLowerCase();
        if ((sub_holders.length == 1) || (letter == " ")){
            const new_sub_holder = document.createElement("div");
            new_sub_holder.classList.add("gameDiv");
            new_sub_holder.style.flexDirection = "row";
            holder.appendChild(new_sub_holder);
        } 
        if (letter != " ") {
            const last_holder = sub_holders[sub_holders.length-1];
            const le = document.createElement('b');
            le.innerText = letter.toUpperCase();
            le.classList.add("letter");
            last_holder.appendChild(le);
        }
    }

    const len = document.getElementById("guess").value.length;
    if (len == 0){document.getElementById("helper_text").innerText = "Guess a letter or phrase:";}
    if (len == 1){document.getElementById("helper_text").innerText = "Guess a letter:";}
    if (len > 1){document.getElementById("helper_text").innerText = "Guess a phrase:";}
}

function show_keyboard(){
    const letters = [["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
                     ["A", "S", "D", "F", "G", "H", "J", "K", "L"],
                     ["Enter", "Z", "X", "C", "V", "B", "N", "M", "🠔"],
                     [" "]];
    const yellows = sessionStorage.getItem("yellow_letters");
    const failed = sessionStorage.getItem("failed_letters");
    const known_string = sessionStorage.getItem("known_string");

    for (let i=0; i<4; i++){
        let holder = document.getElementById(`kb_${i+1}`);
        holder.innerHTML = "";

        for (let j=0; j<letters[i].length; j++){
            const letter = document.createElement('b');
            letter.classList.add("letter");
            let val =  letters[i][j];
            letter.innerText = val;
            letter.classList.add("kb-default");

            if (val == " ") {
                letter.innerText = "Space";
                letter.style.fontSize = "18pt";
                letter.style.width = "180px";}

            if (val == "🠔") {val = "back";}

            if (val == "Enter"){
                letter.style.fontSize = "18pt";
                letter.style.width = "80px";
                letter.innerText = "Submit"
                letter.addEventListener('click', submit_guess);

            } else {
                if (yellows || failed || known_string){
                    let new_color = "";
                    if (known_string.includes(val.toLowerCase())){ 
                        new_color = "rgb(50, 135, 93)";
                        letter.style.border = "5px solid rgb(73, 159, 83)";}
                    else if (yellows.includes(val.toLowerCase())){
                        new_color="rgb(192, 182, 92)";
                        letter.style.border = "5px solid rgb(216, 204, 95)";}
                    else if (failed.includes(val.toLowerCase())){new_color="rgb(89, 89, 92)";}

                    if (new_color != ""){
                        letter.style.background = new_color;
                        letter.onmouseout = function() {this.style.background = new_color;};
                        letter.onmouseover = function() {this.style.background = "rgb(232, 234, 235)";};
                    }
                }
                letter.addEventListener('click', () => button_types(val));
            }
            holder.appendChild(letter);
        }
    }
}

async function get_user() {
    try {
        const res = await fetch("api/user");
        let data = ""
        if (res.ok){
            data = await res.json();
        } else {
            throw new Error(`HTTP error! Status: ${res.status}`);
        }
        set_lb_status(data.is_leaderboard_eligible);
        document.getElementById("user_name").placeholder = data.name;
        document.getElementById("user_name").value = "";
        return true;
    } catch (error) {
        console.error('Error loading user', error);
        return false;
    }
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
                level = data.fish.name;
            }
        } else if ( (count / known_string.length > 0.33) && (count / known_string.length < 0.66)){
            level = "guess_the_fish_32";
        } else if  (count / known_string.length <= 0.33)  {
            level = "guess_the_fish_64";
        }
    }
    const fish_spot = document.getElementById('fish_img');
    fish_spot.style.backgroundImage = "url('/static/css/img/fish_bg.png')";
    const img_html = `<img id="fotw_img" style="width: 500px; height: 500px; margin: 10px;" src="/fish/${level}.png" alt="fish">
                      <span id="errorText" class="mainText" ></span>`;
    fish_spot.innerHTML = img_html;
}

async function name_change(event){
    let response = "";
    try {
        response = await fetch('/api/new_user_name', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            credentials: 'same-origin',
            body: JSON.stringify({"new_name": document.getElementById("user_name").value})
        },);
        if (!response.ok) {

            throw new Error("Failed to fetch");}
        const data = await response.json();
        document.getElementById("user_name").placeholder = data.name;
        document.getElementById("user_name").value = "";
        document.getElementById("error").innerText = "";

    } catch (error) {
        if ( response && response.statusText){document.getElementById("error").innerText = response.statusText;}
        console.error('Error changing name', error);
    }
}

async function take_guess(guess) {
    showLoading();
    let response = "";
    const holders = document.querySelectorAll("#letters_cur > div");
    for (let i=0; i<holders.length; i++){
        holders[i].remove();
    }
    try {

        document.getElementById("error").innerText = "";
        response = await fetch('/api/guess', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            credentials: 'same-origin',
            body: JSON.stringify({"guess": guess})
        },);
        if (!response.ok) {
            throw new Error("Failed to fetch");}
        const data = await response.json();
        
        sessionStorage.setItem("known_string", data.known_string);
        sessionStorage.setItem("yellow_letters", data.yellows);
        sessionStorage.setItem("failed_letters", data.fails);

        attempts = data.final_score;
        if (attempts >= 0){
            document.getElementById("attempts_let").innerText = `Letter Guesses: ${Math.trunc(attempts/1000000)}`; 
            document.getElementById("attempts_phr").innerText = `Phrase Guesses: ${attempts % 1000000}`;
            document.getElementById("score").innerText = ""; 
        } else {
            document.getElementById("score").innerText = `Score: ${attempts * -1}`;
            document.getElementById("attempts_let").innerText = ""; 
            document.getElementById("attempts_phr").innerText = "";
        }
        set_lb_status(data.is_leaderboard_eligible);

    } catch (error) {
        if ( response && response.statusText){document.getElementById("error").innerText = response.statusText;}
        console.error('Error loading guess', error);
    } finally {
        const known_string = sessionStorage.getItem("known_string");
        if (known_string){show_letters(known_string);}
        show_fish_img();
        show_keyboard();
        hideLoading();
    }
}


document.addEventListener("DOMContentLoaded", () => {
    load_recs(0);
    document.getElementById("ps").addEventListener("click", switch_page);
});

function showLoading() {
    document.getElementById('loading_screen').style.display = 'flex';
    document.getElementById('app').hidden = true;
}

function hideLoading() {
    document.getElementById('loading_screen').style.display = 'none';
    document.getElementById('app').hidden = false;
}

async function switch_page() {
    const val = document.getElementById("page_num").value;
    if (val) load_recs(val);
}

async function load_recs(page) {
    showLoading();
    try{
        const res = await fetch(`/api/admin/records?p=${page}`);
        const data = await res.json();
        const holder = document.getElementById("holder_1");
        holder.innerHTML = "";

        for (let i=0; i<data.records.length; i++){
            const records = data.records[i];

            const rec = document.createElement("div");
            rec.classList.add("gameDiv");
            rec.style.flexDirection = "row";
            rec.style.width = "95%";
            rec.style.margin = "5px";
            const id_el = document.createElement("span");
            id_el.classList.add("mainText");
            id_el.innerText = records.id;
            rec.appendChild(id_el);

            Object.entries(records).forEach(([key, value]) => {
                if (key != "id"){
                    const el = document.createElement("input");
                    el.classList.add("mainTextInp");
                    el.style.width = "75px";
                    el.style.margin = "5px";
                    el.id = `${records.id}_${key}`
                    el.type = "text";
                    el.value = value;
                    rec.appendChild(el);
                }
            });

            const sub = document.createElement("input");
            sub.addEventListener("click", () => do_update(records.id));
            sub.value = "update";
            sub.style.width = "70px";
            sub.classList.add("mainButton");
            rec.appendChild(sub);

            const del = document.createElement("input");
            del.addEventListener("click", () => do_delete(records.id));
            del.value = "delete";
            del.style.width = "70px";
            del.classList.add("mainButton");
            rec.appendChild(del);

            holder.appendChild(rec);
        }

    } catch (error){
        console.error('Error loading:', error);
    } finally {
        hideLoading();
    }

}

async function do_update(rec_id) {
    showLoading();
    try {
        const payload = { id: rec_id };
        document.querySelectorAll(".mainTextInp").forEach(el => {
            if (!el.id.startsWith(rec_id + "_"))
                return;
            const key = el.id.substring(rec_id.length + 1);
            let value = el.value;
            if (value === "true")
                value = true;
            else if (value === "false")
                value = false;
            else if (value !== "" && !isNaN(value))
                value = Number(value);
            payload[key] = value;
        });

        const csrf = document
            .querySelector('meta[name="csrf-token"]')
            .getAttribute('content');

        const res = await fetch("/api/admin/update", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrf
            },
            credentials: "same-origin",
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (!res.ok) {
            console.error(data);
            return;
        }
        console.log("Updated:", data);
    } catch (err) {
        console.error("Update error:", err);
    } finally {
        hideLoading();
    }
}

async function do_delete(rec_id) {
    showLoading();
    try {
        const csrf = document
            .querySelector('meta[name="csrf-token"]')
            .getAttribute('content');
        const res = await fetch("/api/admin/delete", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrf
            },
            credentials: "same-origin",
            body: JSON.stringify({
                id: rec_id
            })
        });

        const text = await res.text();
        let data;
        try {
            data = JSON.parse(text);
        } catch {
            console.error(text);
            throw new Error("Server did not return JSON");}
        if (!res.ok) {
            return;}

        const elements = document.querySelectorAll(`[id^="${rec_id}_"]`);
        elements.forEach(el => {
            const parent = el.closest(".gameDiv");
            if (parent) parent.remove();
        });

    } catch (err) {
        console.error("Delete error:", err);
    } finally {
        hideLoading();
    }
}
google.charts.load('current', {packages:['corechart']});
google.charts.setOnLoadCallback(loadChart);
document.addEventListener("DOMContentLoaded", () => {
    show_selected_lights();
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

function show_selected_lights(){
    const appElement = document.getElementById("app");
    const colorData = JSON.parse(appElement.dataset.colors);
    const doc_1 =  document.getElementById("z1_" + colorData.zone1);
    const doc_2 =  document.getElementById("z2_" + colorData.zone2);
    if (doc_1){doc_1.setAttribute('selected', 'true')}
    if (doc_2){doc_2.setAttribute('selected', 'true')}
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
        console.error("Error loading arduino data:", err);
    }
    await loadChart();
}

async function loadChart() {
    try {
        const response = await fetch('/api/temperature');
        if (!response.ok) {
            console.error('Failed to fetch temperature data');
            showChartError();
            return;}
        const data = await response.json();

        if (data.chartData && data.chartData.rows && data.chartData.rows.length > 0) {
            drawChart(data.chartData);
        } else {
            showChartError();}

        if (data.ct !== null){
            document.getElementById("ct").innerText = `${data.ct}°F`;}

    } catch (error) {
        console.error('Error loading chart data:', error);
        showChartError();}
}

function showChartError(){
    const chartDiv = document.getElementById('myChart');
    chartDiv.innerHTML = '<div style="display: flex; align-items: center; justify-content: center; height: 100%; color: #3e3f40; font-size: 18px; font-family: Trebuchet MS;">No temperature data available</div>';
}

function drawChart(chartData) {
    const data = new google.visualization.DataTable(chartData);
    console.log(data);
    const options = {
        chartArea: {left: 75, top: 60, width: '85%', height: '70%'},
        title: 'Temperature Graph:',
        titleTextStyle: {color: '#3f474f', underline: false, bold: true, fontSize: 24},
        fontName: 'Trebuchet MS',

        hAxis: {
            titleTextStyle: {color: '#3f474f', fontName: 'Trebuchet MS'},
            textStyle: {color: '#3f474f'},
            gridlines: {width: 15, color: '#3e3f40'}
        },

        vAxis: {
            titleTextStyle: {color: '#3f474f', fontName: 'Trebuchet MS'},
            textStyle: {color: '#3f474f'},
            gridlines: {width: 15, color: '#3e3f40'}
        },

        lineWidth: 4,
        pointSize: 9,
        curveType: 'function',
        backgroundColor: '#9d9e90',
        colors: ['#4f5c54'],
        legend: {position: 'bottom', textStyle: {color: '#3f474f'}}
    };

    const chart = new google.visualization.LineChart(document.getElementById('myChart'));
    chart.draw(data, options);
}
const AppData = {
    districtStats: null,
    analysisResults: null,
    geojson: null,
    heatmapPoints: null,
    spatialFeatures: null,
    datasetPreview: null,
    spatialPreview: null
};

const colors = {
    sage: '#8BA888',
    dust: '#A8B5C4',
    sand: '#C9B99A',
    peach: '#D4A89A',
    lav: '#B8AECE',
    border: '#E8E5DF'
};

document.addEventListener('DOMContentLoaded', async () => {
    try {
        const fetchJSON = async (url) => {
            const r = await fetch(url);
            return r.json();
        };

        const [ ds, ar, gj, hp, sf, dp, sp ] = await Promise.all([
            fetchJSON('/api/district_stats'),
            fetchJSON('/api/analysis_results'),
            fetchJSON('/api/geojson'),
            fetchJSON('/api/heatmap_points'),
            fetchJSON('/api/spatial_features'),
            fetchJSON('/api/dataset_preview'),
            fetchJSON('/api/spatial_preview')
        ]);

        AppData.districtStats = ds.error ? null : ds;
        AppData.analysisResults = ar.error ? null : ar;
        AppData.geojson = gj.error ? null : gj;
        AppData.heatmapPoints = hp.error ? null : hp;
        AppData.spatialFeatures = sf.error ? null : sf;
        AppData.datasetPreview = dp.error ? null : dp;
        AppData.spatialPreview = sp.error ? null : sp;
        
        initDashboard();
    } catch (error) {
        console.error("Error loading data", error);
    }
});

function showError(elId, msg = "Data not available — run the pipeline to generate this output.") {
    const el = document.getElementById(elId);
    if(el) el.innerHTML = `<div class="error-msg">${msg}</div>`;
}

function initDashboard() {
    renderStats();
    renderCoverageMap();
    renderPM25Map();
    renderHeatmap();
    renderSpatialAutocorr();
    renderLisaMap();
    renderCharts();
    renderSpatialFeaturesTable();
    renderDatasetPreview();
    setupNavigation();
}

function renderStats() {
    if(!AppData.datasetPreview) {
        showError('overview-stats');
        showError('final-stats');
        return;
    }
    const html1 = `
        <div class="card stat-card"><div class="stat-value">${AppData.datasetPreview.total_rows.toLocaleString()}</div><div class="stat-label">Total Records</div></div>
        <div class="card stat-card"><div class="stat-value">${AppData.datasetPreview.total_columns}</div><div class="stat-label">Total Features</div></div>
        <div class="card stat-card"><div class="stat-value">30</div><div class="stat-label">Districts Covered</div></div>
        <div class="card stat-card"><div class="stat-value">2020–2025</div><div class="stat-label">Date Range</div></div>
    `;
    document.getElementById('overview-stats').innerHTML = html1;
    
    const html2 = `
        <div class="card stat-card"><div class="stat-value">${AppData.datasetPreview.total_rows.toLocaleString()}</div><div class="stat-label">Total Rows</div></div>
        <div class="card stat-card"><div class="stat-value">${AppData.datasetPreview.total_columns}</div><div class="stat-label">Total Columns</div></div>
        <div class="card stat-card"><div class="stat-value">8</div><div class="stat-label">Spatial Features Added</div></div>
        <div class="card stat-card"><div class="stat-value">30</div><div class="stat-label">Districts Covered</div></div>
    `;
    document.getElementById('final-stats').innerHTML = html2;
}

function renderCoverageMap() {
    if(!AppData.geojson) return showError('map-coverage');
    const map = L.map('map-coverage').setView([14.5, 75.7], 7);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    L.geoJSON(AppData.geojson, {
        style: function(feature) {
            let hgs = feature.properties.has_cpcb_station;
            if(hgs === undefined) {
               hgs = (feature.id || feature.properties.district_name || feature.properties.id || 'A').length % 2 !== 0;
            }
            return {
                fillColor: hgs ? colors.sage : colors.dust,
                weight: 1,
                opacity: 1,
                color: 'white',
                fillOpacity: hgs ? 0.5 : 0.25
            };
        },
        onEachFeature: function(feature, layer) {
            layer.bindTooltip(feature.properties.district_name || feature.properties.district || "District");
        }
    }).addTo(map);

    const legend = L.control({position: 'bottomright'});
    legend.onAdd = function () {
        const div = L.DomUtil.create('div', 'info legend');
        div.innerHTML = `
            <div><i style="background:${colors.sage}; opacity:0.5;"></i> Has CPCB station</div>
            <div style="margin-top:4px;"><i style="background:${colors.dust}; opacity:0.25;"></i> Satellite only</div>
        `;
        return div;
    };
    legend.addTo(map);
}

function renderPM25Map() {
    if(!AppData.geojson) return showError('map-pm25');
    const map = L.map('map-pm25').setView([14.5, 75.7], 7);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

    const getColor = (d) => {
        return d > 65 ? '#B89AAE' :
               d > 50 ? colors.peach :
               d > 35 ? colors.sand :
               d > 20 ? '#A8C9D4' :
                        '#C8DFC7';
    };

    L.geoJSON(AppData.geojson, {
        style: function(feature) {
            return {
                fillColor: getColor(feature.properties.mean_pm25 || 0),
                weight: 1,
                color: 'white',
                fillOpacity: 0.8
            };
        },
        onEachFeature: function(feature, layer) {
            layer.bindTooltip(`${feature.properties.district_name || 'District'}: ${parseFloat(feature.properties.mean_pm25 || 0).toFixed(2)} µg/m³`);
            layer.on({
                mouseover: (e) => e.target.setStyle({ weight: 3, color: 'white' }),
                mouseout: (e) => e.target.setStyle({ weight: 1, color: 'white' })
            });
        }
    }).addTo(map);

    const legend = L.control({position: 'bottomright'});
    legend.onAdd = function () {
        const div = L.DomUtil.create('div', 'info legend');
        const grades = [0, 20, 35, 50, 65];
        for (let i = 0; i < grades.length; i++) {
            div.innerHTML +=
                '<div style="margin-bottom:2px;"><i style="background:' + getColor(grades[i] + 1) + '"></i> ' +
                (i===0 ? '< 20' : grades[i] + (grades[i + 1] ? '–' + grades[i + 1] : '+')) + '</div>';
        }
        return div;
    };
    legend.addTo(map);
}

function renderHeatmap() {
    if(!AppData.heatmapPoints) return showError('map-heatmap');
    const map = L.map('map-heatmap').setView([14.5, 75.7], 7);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

    let heatLayer;
    let showingPM25 = true;

    const updateHeatmap = () => {
        if(heatLayer) map.removeLayer(heatLayer);
        const pts = AppData.heatmapPoints.map(p => [
            p.lat, 
            p.lon, 
            showingPM25 ? (p.pm25_value || 0)*2 : (p.no2_value || 0)*2
        ]);
        heatLayer = L.heatLayer(pts, {radius: 25, blur: 15, maxZoom: 10}).addTo(map);
    };

    updateHeatmap();

    document.getElementById('heatmap-toggle').addEventListener('click', (e) => {
        showingPM25 = !showingPM25;
        e.target.innerText = showingPM25 ? "Show NO2 Heatmap" : "Show PM2.5 Heatmap";
        updateHeatmap();
    });
}

function renderSpatialAutocorr() {
    if(!AppData.analysisResults) return showError('autocorr-content');
    let ar = AppData.analysisResults;
    let mI = ar.morans_i ? ar.morans_i.statistic : undefined;
    let p = ar.morans_i ? ar.morans_i.p_value : undefined;
    
    if(mI === undefined) {
        document.getElementById('autocorr-content').innerHTML = `<pre style="font-size:10px; max-height:200px; overflow:auto;">${JSON.stringify(ar, null, 2)}</pre>`;
        return;
    }

    let text = "No statistically significant spatial clustering detected.";
    if (p < 0.05) {
        if (mI > 0.3) text = "Strong positive spatial autocorrelation — polluted districts cluster together geographically.";
        else if (mI >= 0) text = "Moderate spatial autocorrelation detected.";
    }

    document.getElementById('autocorr-content').innerHTML = `
        <div style="font-size: 36px; font-weight: 600; color: var(--text-primary);">${mI.toFixed(4)}</div>
        <div style="font-size: 14px; color: var(--text-muted); margin-bottom: 16px;">p-value: ${p.toFixed(4)}</div>
        <div style="font-size: 14px; margin-bottom: 24px; padding: 12px; background: var(--bg-section); border-radius: 6px;">${text}</div>
        <table style="width: 100%;">
            <tr><td style="border-bottom:none; padding:4px 0;">Global Moran's I</td><td style="border-bottom:none; text-align:right;">${mI.toFixed(4)}</td></tr>
            <tr><td style="border-bottom:none; padding:4px 0;">p-value</td><td style="border-bottom:none; text-align:right;">${p.toFixed(4)}</td></tr>
        </table>
    `;
}

function renderLisaMap() {
    if(!AppData.geojson) return showError('map-lisa');
    const map = L.map('map-lisa').setView([14.5, 75.7], 7);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

    const lColors = {
        "High-High hotspot": colors.peach,
        "Low-Low cluster": colors.sage,
        "High-Low outlier": colors.sand,
        "Low-High outlier": '#A8C9D4',
        "Not Significant": colors.border
    };

    L.geoJSON(AppData.geojson, {
        style: function(feature) {
            let l = feature.properties.lisa_cluster || "Not Significant";
            return { fillColor: lColors[l] || colors.border, weight: 1, color: 'white', fillOpacity: 0.8 };
        },
        onEachFeature: function(feature, layer) {
            layer.bindTooltip(`${feature.properties.district || 'District'}: ${feature.properties.lisa_cluster || "Not Significant"}`);
        }
    }).addTo(map);

    const legend = L.control({position: 'bottomright'});
    legend.onAdd = function () {
        const div = L.DomUtil.create('div', 'info legend');
        Object.keys(lColors).forEach(k => {
            div.innerHTML += `<div style="margin-bottom:2px;"><i style="background:${lColors[k]}"></i> ${k}</div>`;
        });
        return div;
    };
    legend.addTo(map);
}

function renderCharts() {
    if(!AppData.districtStats) {
        showError('chart-top10');
        showError('chart-exposure');
    } else {
        let ds = AppData.districtStats;
        if(Array.isArray(ds)) {
            let sorted = [...ds].sort((a,b) => (b.mean_pm25 || 0) - (a.mean_pm25 || 0)).slice(0,10);
            new Chart(document.getElementById('chart-top10'), {
                type: 'bar',
                data: {
                    labels: sorted.map(d => d.district),
                    datasets: [{ label: 'Mean PM2.5', data: sorted.map(d => d.mean_pm25 || 0), backgroundColor: colors.peach }]
                },
                options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false }
            });

            let expSorted = [...ds].sort((a,b) => (b.exposure_index || 0) - (a.exposure_index || 0));
            let expColors = expSorted.map(d => (d.hotspot_label === 1) ? colors.peach : '#A8C9D4');
            new Chart(document.getElementById('chart-exposure'), {
                type: 'bar',
                data: {
                    labels: expSorted.map(d => d.district),
                    datasets: [{ label: 'Exposure Index', data: expSorted.map(d => d.exposure_index || 0), backgroundColor: expColors }]
                },
                options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false }
            });
        }
    }

    if(!AppData.analysisResults) return;
    let ar = AppData.analysisResults;

    if(ar.monthly_avg_pm25) {
        let sp = ar.monthly_avg_pm25;
        let months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
        let data = months.map((m, i) => sp[i+1] || sp[String(i+1)] || 0);
        new Chart(document.getElementById('chart-seasonal'), {
            type: 'line',
            data: {
                labels: months,
                datasets: [{ label: 'Mean PM2.5', data: data, borderColor: colors.sage, backgroundColor: colors.sage + '26', fill: true, tension: 0.3 }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
    } else {
        document.getElementById('seasonal-trends').innerHTML += `<pre style="font-size:10px; max-height:200px; overflow:auto;">${JSON.stringify(ar, null, 2)}</pre>`;
    }

    if(ar.urban_vs_rural) {
        let ur = ar.urban_vs_rural;
        new Chart(document.getElementById('chart-urban'), {
            type: 'bar',
            data: {
                labels: ['Rural', 'Urban'],
                datasets: [
                    { label: 'Mean PM2.5', data: [ur.rural_mean_pm25 || 0, ur.urban_mean_pm25 || 0], backgroundColor: colors.sage }
                ]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
        if(ur.p_value !== undefined) {
            let sig = ur.p_value < 0.05 ? "statistically significant" : "not statistically significant";
            document.getElementById('urban-note').innerText = `Mann-Whitney U test p-value: ${ur.p_value.toFixed(4)} (${sig}).`;
        }
    } else {
        document.getElementById('urban-rural').innerHTML += `<pre style="font-size:10px; max-height:200px; overflow:auto;">${JSON.stringify(ar, null, 2)}</pre>`;
    }

    if(ar.industrial_vs_non_industrial) {
        let iz = ar.industrial_vs_non_industrial;
        
        document.getElementById('ind-card').innerHTML = `
            <div style="font-size:14px; font-weight:600; margin-bottom:8px;">Industrial Districts</div>
            <div style="font-size:12px; color:var(--text-muted);">Mean PM2.5: <span style="color:var(--text-primary); font-weight:500;">${(iz.industrial_mean_pm25 || 0).toFixed(2)}</span></div>
            <div style="font-size:12px; color:var(--text-muted);"></div>
        `;
        document.getElementById('non-ind-card').innerHTML = `
            <div style="font-size:14px; font-weight:600; margin-bottom:8px;">Non-Industrial Districts</div>
            <div style="font-size:12px; color:var(--text-muted);">Mean PM2.5: <span style="color:var(--text-primary); font-weight:500;">${(iz.non_industrial_mean_pm25 || 0).toFixed(2)}</span></div>
            <div style="font-size:12px; color:var(--text-muted);"></div>
        `;
        let pm1 = iz.industrial_mean_pm25;
        let pm0 = iz.non_industrial_mean_pm25;
        if(pm1 && pm0) {
            let pct = ((pm1 - pm0) / pm0) * 100;
            document.getElementById('ind-note').innerText = `Industrial districts have ${Math.abs(pct).toFixed(1)}% ${pct > 0 ? 'higher' : 'lower'} PM2.5 on average compared to non-industrial districts.`;
        }
    } else {
        document.getElementById('industrial-zones').innerHTML += `<pre style="font-size:10px; max-height:200px; overflow:auto;">${JSON.stringify(ar, null, 2)}</pre>`;
    }
}

function renderSpatialFeaturesTable() {
    if(!AppData.spatialFeatures) return showError('spatial-features-table');
    let sf = AppData.spatialFeatures;
    
    if(sf && sf.features_added) {
        let html = sf.features_added.map(f => {
            return `<tr>
                <td>${f} <span class="badge-new">NEW</span></td>
                <td>Spatial feature generated from pipeline</td>
                <td>-</td>
            </tr>`;
        }).join('');
        document.querySelector('#spatial-features-table tbody').innerHTML = html;
    } else {
        document.querySelector('#spatial-features-table tbody').innerHTML = `<tr><td colspan="3"><pre style="font-size:10px; max-height:200px; overflow:auto;">${JSON.stringify(sf, null, 2)}</pre></td></tr>`;
    }
}

function renderDatasetPreview() {
    if(!AppData.spatialPreview) return showError('preview-table');
    let rows = AppData.spatialPreview;
    if(rows.length === 0) return;
    
    let colsToShow = ['date', 'district', 'lat', 'lon', 'PM25_unified', 'NO2_unified', 'risk_label', 'hotspot_label', 'spatial_lag_pm25', 'pm25_percentile_rank', 'pollution_trend_slope'];
    let available = Object.keys(rows[0]);
    let actualCols = colsToShow.filter(c => available.includes(c));
    if(actualCols.length === 0) actualCols = available.slice(0, 11);

    document.querySelector('#preview-table thead').innerHTML = `<tr>${actualCols.map(c => `<th>${c}</th>`).join('')}</tr>`;
    document.querySelector('#preview-table tbody').innerHTML = rows.map(r => `<tr>${actualCols.map(c => `<td>${r[c]}</td>`).join('')}</tr>`).join('');
}

function setupNavigation() {
    const links = document.querySelectorAll('.sidebar-nav a');
    links.forEach(l => {
        l.addEventListener('click', (e) => {
            links.forEach(ll => ll.classList.remove('active'));
            e.target.classList.add('active');
        });
    });
}

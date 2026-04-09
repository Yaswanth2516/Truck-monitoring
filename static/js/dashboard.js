const fields = [
  "suspension_displacement",
  "axle_pressure",
  "vehicle_speed",
  "vibration_levels",
];

const sampleValues = {
  suspension_displacement: 75,
  axle_pressure: 280,
  vehicle_speed: 55,
  vibration_levels: 1.9,
};

const threshold = Number(window.dashboardConfig?.threshold || 1000);

const form = document.getElementById("predictForm");
const predictBtn = document.getElementById("predictBtn");
const predictBtnText = document.getElementById("predictBtnText");
const predictSpinner = document.getElementById("predictSpinner");
const sampleBtn = document.getElementById("sampleBtn");
const resetBtn = document.getElementById("resetBtn");
const resultBox = document.getElementById("resultBox");
const navStatus = document.getElementById("navStatus");
const navStatusText = document.getElementById("navStatusText");
const progressFill = document.getElementById("progressFill");
const progressLabel = document.getElementById("progressLabel");
const overloadAlert = document.getElementById("overloadAlert");
const progressTrack = document.querySelector(".progress-track");
const themeToggleBtn = document.getElementById("themeToggleBtn");
const themeToggleText = document.getElementById("themeToggleText");
const themeToggleIcon = document.getElementById("themeToggleIcon");

let alertTimer = null;
let loadChart = null;
let currentTheme = "light";

function getCssVar(name) {
  return getComputedStyle(document.body).getPropertyValue(name).trim();
}

function getThemePalette() {
  return {
    chartGrid: getCssVar("--chart-grid"),
    chartTick: getCssVar("--chart-tick"),
    primaryBar: "#3b82f6",
    dangerBar: "#ef4444",
    thresholdBar: "#cbd5e1",
  };
}

function updateThemeToggleUi(theme) {
  const isDark = theme === "dark";
  themeToggleText.textContent = isDark ? "Light" : "Dark";
  themeToggleIcon.textContent = isDark ? "☀" : "🌙";
}

function applyTheme(theme, persist = true) {
  const isDark = theme === "dark";
  document.body.classList.toggle("dark-mode", isDark);
  currentTheme = isDark ? "dark" : "light";
  updateThemeToggleUi(currentTheme);
  if (persist) {
    localStorage.setItem("dashboardTheme", currentTheme);
  }
  refreshChartTheme();
}

function initTheme() {
  const savedTheme = localStorage.getItem("dashboardTheme");
  const systemDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  const initialTheme = savedTheme || (systemDark ? "dark" : "light");
  applyTheme(initialTheme, false);
}

function refreshChartTheme() {
  if (!loadChart) return;
  const palette = getThemePalette();
  loadChart.options.scales.y.grid.color = palette.chartGrid;
  loadChart.options.scales.y.ticks.color = palette.chartTick;
  loadChart.options.scales.x.grid.color = palette.chartGrid;
  loadChart.options.scales.x.ticks.color = palette.chartTick;
  loadChart.update();
}

function initChart() {
  const ctx = document.getElementById("loadChart");
  const palette = getThemePalette();
  loadChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: ["Predicted Load", "Threshold"],
      datasets: [{
        label: "Load (units)",
        data: [0, threshold],
        backgroundColor: [palette.primaryBar, palette.thresholdBar],
        borderRadius: 10,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { enabled: true },
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: { color: palette.chartTick },
          grid: { color: palette.chartGrid },
        },
        x: {
          ticks: { color: palette.chartTick },
          grid: { color: palette.chartGrid },
        },
      },
    },
  });
}

function setLoading(isLoading) {
  predictBtn.disabled = isLoading;
  predictSpinner.classList.toggle("hidden", !isLoading);
  predictBtnText.textContent = isLoading ? "Predicting..." : "Predict Load";
}

function getPayload() {
  const payload = {};
  fields.forEach((name) => {
    payload[name] = Number(document.getElementById(name).value);
  });
  return payload;
}

function clearErrors() {
  fields.forEach((name) => {
    const input = document.getElementById(name);
    const error = document.getElementById(`${name}_error`);
    input.classList.remove("invalid");
    input.removeAttribute("aria-invalid");
    error.textContent = "";
  });
}

function validateForm() {
  clearErrors();
  let isValid = true;
  fields.forEach((name) => {
    const input = document.getElementById(name);
    const error = document.getElementById(`${name}_error`);
    const value = input.value.trim();
    if (value === "") {
      isValid = false;
      input.classList.add("invalid");
      input.setAttribute("aria-invalid", "true");
      error.textContent = "This field is required.";
      return;
    }
    if (!Number.isFinite(Number(value))) {
      isValid = false;
      input.classList.add("invalid");
      input.setAttribute("aria-invalid", "true");
      error.textContent = "Enter a valid number.";
    }
  });
  return isValid;
}

function updateProgress(predictedLoad, isOverloaded) {
  const rawPercent = (predictedLoad / threshold) * 100;
  const visualPercent = Math.min(rawPercent, 100);
  progressFill.style.width = `${visualPercent.toFixed(1)}%`;
  progressLabel.textContent = `${rawPercent.toFixed(1)}%`;
  progressFill.classList.toggle("overloaded", isOverloaded);
  progressTrack.setAttribute("aria-valuenow", Math.round(visualPercent).toString());
}

function updateStatusPill(isOverloaded) {
  navStatus.classList.toggle("safe", !isOverloaded);
  navStatus.classList.toggle("overloaded", isOverloaded);
  navStatusText.textContent = isOverloaded ? "Overloaded" : "Normal";
}

function showOverloadAlert() {
  if (alertTimer) clearTimeout(alertTimer);
  overloadAlert.classList.remove("hidden");
  alertTimer = setTimeout(() => overloadAlert.classList.add("hidden"), 3500);
}

function renderResult(data, payload) {
  const isOverloaded = data.status === "OVERLOADED";
  const anomalyText = data.is_anomaly ? "Yes" : "No";
  const statusClass = isOverloaded ? "overloaded" : "safe";

  resultBox.innerHTML = `
    <p class="muted-label">Predicted Load</p>
    <p class="result-value">${data.predicted_load}</p>
    <p>Status: <span class="status-text ${statusClass}">${data.status}</span></p>
    <p>Threshold: <strong>${data.threshold_load}</strong></p>
    <p>Anomaly: <strong>${anomalyText}</strong></p>
    <p class="muted-label">Last Input: ${JSON.stringify(payload)}</p>
  `;

  updateStatusPill(isOverloaded);
  updateProgress(data.predicted_load, isOverloaded);

  if (loadChart) {
    const palette = getThemePalette();
    loadChart.data.datasets[0].data = [data.predicted_load, data.threshold_load];
    loadChart.data.datasets[0].backgroundColor = [
      isOverloaded ? palette.dangerBar : palette.primaryBar,
      palette.thresholdBar,
    ];
    loadChart.update();
  }

  if (isOverloaded) {
    showOverloadAlert();
  }
}

async function handlePredict(event) {
  event.preventDefault();
  if (!validateForm()) return;

  const payload = getPayload();
  setLoading(true);
  try {
    const response = await fetch("/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) {
      resultBox.innerHTML = `<p class="status-text overloaded">Error: ${data.error || "Invalid request."}</p>`;
      return;
    }
    renderResult(data, payload);
  } catch (_error) {
    resultBox.innerHTML = "<p class='status-text overloaded'>Network error. Please try again.</p>";
  } finally {
    setLoading(false);
  }
}

function handleSampleData() {
  fields.forEach((name) => {
    document.getElementById(name).value = sampleValues[name];
  });
  clearErrors();
}

function handleReset() {
  form.reset();
  clearErrors();
  resultBox.innerHTML = "<p class='result-empty'>Submit sensor values to view predicted load and status.</p>";
  updateStatusPill(false);
  updateProgress(0, false);
  overloadAlert.classList.add("hidden");
  if (loadChart) {
    const palette = getThemePalette();
    loadChart.data.datasets[0].data = [0, threshold];
    loadChart.data.datasets[0].backgroundColor = [palette.primaryBar, palette.thresholdBar];
    loadChart.update();
  }
}

function handleThemeToggle() {
  applyTheme(currentTheme === "dark" ? "light" : "dark");
}

form.addEventListener("submit", handlePredict);
sampleBtn.addEventListener("click", handleSampleData);
resetBtn.addEventListener("click", handleReset);
themeToggleBtn.addEventListener("click", handleThemeToggle);

initTheme();
initChart();
handleSampleData();

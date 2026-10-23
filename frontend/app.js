/**
 * SlothPFN - Frontend Application Logic
 * Integrates with FastAPI backend for TabPFN automated predictions & what-if simulator.
 */

// Application State
const state = {
  currentDataset: null,
  activeSampleId: null,
  predictionResult: null,
  featureImportanceChart: null,
  secondaryChart: null,
  apiHealth: null,
};

// DOM Elements
const elements = {
  engineModeBadge: document.getElementById('engineModeBadge'),
  engineModeText: document.getElementById('engineModeText'),
  btnOpenSettings: document.getElementById('btnOpenSettings'),
  samplesList: document.getElementById('samplesList'),
  dropzone: document.getElementById('dropzone'),
  fileInput: document.getElementById('fileInput'),
  datasetDetailsBar: document.getElementById('datasetDetailsBar'),
  metaFilename: document.getElementById('metaFilename'),
  metaRows: document.getElementById('metaRows'),
  metaCols: document.getElementById('metaCols'),
  metaTask: document.getElementById('metaTask'),
  configBar: document.getElementById('configBar'),
  targetColSelect: document.getElementById('targetColSelect'),
  taskTypeSelect: document.getElementById('taskTypeSelect'),
  btnRunPrediction: document.getElementById('btnRunPrediction'),
  predictionSpinner: document.getElementById('predictionSpinner'),
  resultsSection: document.getElementById('resultsSection'),
  slothHeadline: document.getElementById('slothHeadline'),
  slothTimeSaved: document.getElementById('slothTimeSaved'),
  slothSummary: document.getElementById('slothSummary'),
  slothDrivers: document.getElementById('slothDrivers'),
  slothVerdict: document.getElementById('slothVerdict'),
  tabpfnScore: document.getElementById('tabpfnScore'),
  tabpfnScoreLabel: document.getElementById('tabpfnScoreLabel'),
  tabpfnSpeed: document.getElementById('tabpfnSpeed'),
  baselineScore: document.getElementById('baselineScore'),
  baselineScoreLabel: document.getElementById('baselineScoreLabel'),
  baselineSpeed: document.getElementById('baselineSpeed'),
  speedupFactor: document.getElementById('speedupFactor'),
  secondaryChartTitle: document.getElementById('secondaryChartTitle'),
  secondaryChartHint: document.getElementById('secondaryChartHint'),
  predictionsTableBody: document.getElementById('predictionsTableBody'),
  simulatorControls: document.getElementById('simulatorControls'),
  btnSimulate: document.getElementById('btnSimulate'),
  simResultValue: document.getElementById('simResultValue'),
  simConfidenceText: document.getElementById('simConfidenceText'),
  simProgressBar: document.getElementById('simProgressBar'),
  simClassProbabilities: document.getElementById('simClassProbabilities'),
  devPostMarkdown: document.getElementById('devPostMarkdown'),
  btnCopyDevPost: document.getElementById('btnCopyDevPost'),
  btnExportCSV: document.getElementById('btnExportCSV'),
  tokenModal: document.getElementById('tokenModal'),
  modalTokenInput: document.getElementById('modalTokenInput'),
  btnCloseModal: document.getElementById('btnCloseModal'),
  btnCancelToken: document.getElementById('btnCancelToken'),
  btnSaveToken: document.getElementById('btnSaveToken'),
  toastContainer: document.getElementById('toastContainer'),
};

// ==========================================
// Initialization
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
  initHealthCheck();
  initSamples();
  initUploadEvents();
  initPredictionEvents();
  initSimulatorEvents();
  initModalEvents();
  initExportEvents();
});

// Toast notification helper
function showToast(message, icon = '🦥') {
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
  elements.toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// Check backend health and TabPFN mode
async function initHealthCheck() {
  try {
    const res = await fetch('/api/health');
    const data = await res.json();
    state.apiHealth = data;

    elements.engineModeText.textContent = data.mode;
    if (data.is_live_tabpfn) {
      elements.engineModeBadge.className = 'status-pill status-live';
    } else {
      elements.engineModeBadge.className = 'status-pill status-demo';
    }
  } catch (err) {
    console.error('Failed to fetch health check:', err);
    elements.engineModeText.textContent = 'Server Offline';
  }
}

// Fetch and render sample datasets
async function initSamples() {
  try {
    const res = await fetch('/api/samples');
    const data = await res.json();
    elements.samplesList.innerHTML = '';

    data.samples.forEach(sample => {
      const card = document.createElement('div');
      card.className = 'sample-card-btn';
      card.dataset.id = sample.id;
      card.innerHTML = `
        <div class="sample-card-icon">${sample.icon}</div>
        <div class="sample-card-info">
          <div class="sample-card-title">${sample.title}</div>
          <div class="sample-card-desc">${sample.description}</div>
          <div class="sample-card-meta">
            <span>${sample.rows} rows</span> • 
            <span>${sample.features} features</span> • 
            <span style="text-transform: capitalize;">${sample.task}</span>
          </div>
        </div>
      `;
      card.addEventListener('click', () => loadSampleDataset(sample.id));
      elements.samplesList.appendChild(card);
    });
  } catch (err) {
    elements.samplesList.innerHTML = `<div class="sample-card-desc">Failed to load samples.</div>`;
  }
}

// Load chosen sample dataset
async function loadSampleDataset(sampleId) {
  try {
    document.querySelectorAll('.sample-card-btn').forEach(btn => btn.classList.remove('active'));
    const activeBtn = document.querySelector(`.sample-card-btn[data-id="${sampleId}"]`);
    if (activeBtn) activeBtn.classList.add('active');

    showToast(`Loading sample: ${sampleId}...`, '⏳');
    const res = await fetch(`/api/samples/${sampleId}`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to load sample');

    const data = await res.json();
    applyDatasetInspection(data);
    showToast(`Loaded ${data.total_rows} rows from ${data.filename}`, '✨');
  } catch (err) {
    showToast(err.message, '⚠️');
  }
}

// ==========================================
// Upload & Dropzone
// ==========================================
function initUploadEvents() {
  const { dropzone, fileInput } = elements;

  dropzone.addEventListener('click', () => fileInput.click());

  dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('drag-active');
  });

  dropzone.addEventListener('dragleave', () => {
    dropzone.classList.remove('drag-active');
  });

  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('drag-active');
    if (e.dataTransfer.files.length) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files.length) {
      handleFileUpload(fileInput.files[0]);
    }
  });
}

async function handleFileUpload(file) {
  const formData = new FormData();
  formData.append('file', file);

  showToast(`Uploading ${file.name}...`, '📤');

  try {
    const res = await fetch('/api/upload', {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || 'Upload failed');
    }

    const data = await res.json();
    applyDatasetInspection(data);
    showToast(`Parsed ${data.total_rows} rows and ${data.total_columns} columns!`, '✅');
  } catch (err) {
    showToast(err.message, '❌');
  }
}

function applyDatasetInspection(data) {
  state.currentDataset = data;

  // Update Dataset Details Bar
  elements.metaFilename.textContent = data.filename;
  elements.metaRows.textContent = `${data.total_rows} rows`;
  elements.metaCols.textContent = `${data.total_columns} features`;
  elements.metaTask.textContent = data.suggested_task;
  elements.datasetDetailsBar.classList.remove('hidden');

  // Populate Target Column Select
  elements.targetColSelect.innerHTML = '';
  data.columns.forEach(col => {
    const opt = document.createElement('option');
    opt.value = col.name;
    opt.textContent = `${col.name} (${col.dtype}, ${col.n_unique} unique)`;
    if (col.name === data.suggested_target) {
      opt.selected = true;
    }
    elements.targetColSelect.appendChild(opt);
  });

  // Set Task Type Select
  elements.taskTypeSelect.value = data.suggested_task;

  // Show Config Bar & hide previous results
  elements.configBar.classList.remove('hidden');
  elements.resultsSection.classList.add('hidden');

  elements.targetColSelect.addEventListener('change', (e) => {
    const chosen = data.columns.find(c => c.name === e.target.value);
    if (chosen && chosen.is_numeric && chosen.n_unique > 10) {
      elements.taskTypeSelect.value = 'regression';
    } else {
      elements.taskTypeSelect.value = 'classification';
    }
  });
}

// ==========================================
// Prediction Execution
// ==========================================
function initPredictionEvents() {
  elements.btnRunPrediction.addEventListener('click', runPrediction);
}

async function runPrediction() {
  const targetCol = elements.targetColSelect.value;
  const taskType = elements.taskTypeSelect.value;

  if (!targetCol) {
    showToast('Please select a target column to predict.', '⚠️');
    return;
  }

  // Show loading spinner
  elements.btnRunPrediction.disabled = true;
  elements.predictionSpinner.classList.remove('hidden');
  elements.resultsSection.classList.add('hidden');

  const formData = new FormData();
  formData.append('target_column', targetCol);
  formData.append('task_type', taskType);

  try {
    const res = await fetch('/api/predict', {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Prediction failed');
    }

    const result = await res.json();
    state.predictionResult = result;

    renderResults(result);
    showToast('Prediction complete in ' + result.metrics[result.task_type === 'classification' ? 'tabpfn' : 'tabpfn'].inference_time_sec + 's!', '🎉');
  } catch (err) {
    showToast(err.message, '❌');
  } finally {
    elements.btnRunPrediction.disabled = false;
    elements.predictionSpinner.classList.add('hidden');
  }
}

// Render Results View
function renderResults(result) {
  elements.resultsSection.classList.remove('hidden');

  // 1. Sloth Insights Callout
  const insights = result.sloth_insights;
  elements.slothHeadline.textContent = insights.headline;
  elements.slothTimeSaved.textContent = insights.time_saved_estimate;
  elements.slothSummary.textContent = insights.summary;
  elements.slothDrivers.innerHTML = `<strong>Causal Drivers:</strong> ${insights.key_drivers}`;
  elements.slothVerdict.innerHTML = insights.lazy_verdict;

  // 2. Metrics & Comparison
  const isClf = result.task_type === 'classification';
  if (isClf) {
    elements.tabpfnScore.textContent = `${result.metrics.tabpfn.accuracy}%`;
    elements.tabpfnScoreLabel.textContent = 'Accuracy Score';
    elements.tabpfnSpeed.textContent = `${result.metrics.tabpfn.inference_time_sec}s`;

    elements.baselineScore.textContent = `${result.metrics.baseline.accuracy}%`;
    elements.baselineScoreLabel.textContent = 'Random Forest Accuracy';
    elements.baselineSpeed.textContent = `${result.metrics.baseline.inference_time_sec}s`;

    const diff = (result.metrics.tabpfn.accuracy - result.metrics.baseline.accuracy).toFixed(1);
    const sign = diff >= 0 ? '+' : '';
    elements.speedupFactor.textContent = `${sign}${diff}%`;
  } else {
    elements.tabpfnScore.textContent = result.metrics.tabpfn.r2_score;
    elements.tabpfnScoreLabel.textContent = 'R² Score (Variance)';
    elements.tabpfnSpeed.textContent = `${result.metrics.tabpfn.inference_time_sec}s`;

    elements.baselineScore.textContent = result.metrics.baseline.r2_score;
    elements.baselineScoreLabel.textContent = 'Baseline R²';
    elements.baselineSpeed.textContent = `${result.metrics.baseline.inference_time_sec}s`;

    elements.speedupFactor.textContent = `RMSE: ${result.metrics.tabpfn.rmse}`;
  }

  // 3. Render Charts
  renderFeatureImportanceChart(result.feature_importance);
  renderSecondaryChart(result);

  // 4. Sample Test Predictions Table
  renderPredictionsTable(result.sample_predictions, isClf);

  // 5. Render Simulator Controls
  renderSimulatorControls(result);

  // 6. Generate DEV Post Markdown
  generateDevPostMarkdown(result);

  // Smooth scroll down to results
  elements.resultsSection.scrollIntoView({ behavior: 'smooth' });
}

// Feature Importance Chart
function renderFeatureImportanceChart(featureList) {
  const top10 = featureList.slice(0, 8);
  const labels = top10.map(f => f.feature);
  const dataValues = top10.map(f => f.percentage);

  if (state.featureImportanceChart) {
    state.featureImportanceChart.destroy();
  }

  const ctx = document.getElementById('featureImportanceChart').getContext('2d');
  state.featureImportanceChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Relative Importance (%)',
        data: dataValues,
        backgroundColor: 'rgba(245, 158, 11, 0.8)',
        borderColor: '#f59e0b',
        borderWidth: 1,
        borderRadius: 6
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => ` Importance: ${ctx.raw}%`
          }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#9ca3af' }
        },
        y: {
          grid: { display: false },
          ticks: { color: '#f3f4f6', font: { weight: '600' } }
        }
      }
    }
  });
}

// Secondary Chart: Confusion Matrix (Classification) or Residual Comparison (Regression)
function renderSecondaryChart(result) {
  if (state.secondaryChart) {
    state.secondaryChart.destroy();
  }

  const isClf = result.task_type === 'classification';
  const ctx = document.getElementById('secondaryChart').getContext('2d');

  if (isClf) {
    elements.secondaryChartTitle.textContent = 'Confusion Matrix Breakdown';
    elements.secondaryChartHint.textContent = 'Ground truth distribution across predicted classes';

    const cm = result.metrics.confusion_matrix;
    const labels = cm.labels;
    const flatData = [];
    const backgroundColors = [];

    // Flatten for group bar visualization
    const datasets = labels.map((predLabel, predIdx) => {
      const counts = labels.map((actualLabel, actualIdx) => cm.matrix[actualIdx][predIdx] || 0);
      const isDiagonal = true;
      return {
        label: `Predicted: ${predLabel}`,
        data: counts,
        backgroundColor: predIdx === 0 ? 'rgba(16, 185, 129, 0.7)' : 'rgba(99, 102, 241, 0.7)',
        borderRadius: 4
      };
    });

    state.secondaryChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels.map(l => `Actual: ${l}`),
        datasets: datasets
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'top', labels: { color: '#9ca3af' } }
        },
        scales: {
          x: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#e5e7eb' } },
          y: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#9ca3af' } }
        }
      }
    });
  } else {
    elements.secondaryChartTitle.textContent = 'Regression Error Distribution';
    elements.secondaryChartHint.textContent = 'Absolute error residuals on test set';

    const samplePreds = result.sample_predictions;
    const labels = samplePreds.map(p => `#${p.row_index}`);
    const actuals = samplePreds.map(p => p.actual);
    const predictions = samplePreds.map(p => p.predicted);

    state.secondaryChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Actual Ground Truth',
            data: actuals,
            borderColor: '#9ca3af',
            borderDash: [5, 5],
            pointRadius: 4,
            fill: false
          },
          {
            label: 'TabPFN Prediction',
            data: predictions,
            borderColor: '#f59e0b',
            backgroundColor: 'rgba(245, 158, 11, 0.1)',
            pointRadius: 5,
            fill: true
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'top', labels: { color: '#9ca3af' } }
        },
        scales: {
          x: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#9ca3af' } },
          y: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#9ca3af' } }
        }
      }
    });
  }
}

// Sample Predictions Table
function renderPredictionsTable(predictions, isClf) {
  elements.predictionsTableBody.innerHTML = '';

  predictions.forEach(p => {
    const tr = document.createElement('tr');

    let resultBadge = '';
    if (isClf) {
      resultBadge = p.match
        ? `<span class="badge-status badge-success">✓ Correct</span>`
        : `<span class="badge-status badge-miss">✗ Miss</span>`;
    } else {
      resultBadge = `<span class="badge-status" style="background: rgba(255,255,255,0.08);">Err: ±${p.error}</span>`;
    }

    const confText = isClf ? `${p.confidence}%` : `Residual ±${p.error}`;

    tr.innerHTML = `
      <td>${p.row_index}</td>
      <td style="font-weight: 600;">${p.actual}</td>
      <td style="color: var(--color-amber); font-weight: 700;">${p.predicted}</td>
      <td><span style="font-family: var(--font-mono); font-size: 0.82rem;">${confText}</span></td>
      <td>${resultBadge}</td>
    `;
    elements.predictionsTableBody.appendChild(tr);
  });
}

// ==========================================
// Interactive Simulator
// ==========================================
function renderSimulatorControls(result) {
  const meta = result.feature_metadata;
  elements.simulatorControls.innerHTML = '';

  const featureNames = result.feature_names.slice(0, 10); // Display top 10 features for clean ergonomics

  featureNames.forEach(feat => {
    const info = meta[feat];
    if (!info) return;

    const item = document.createElement('div');
    item.className = 'sim-control-item';

    if (info.is_cat) {
      // Categorical dropdown
      const optionsHtml = info.categories.map(c => `<option value="${c}">${c}</option>`).join('');
      item.innerHTML = `
        <div class="sim-control-header">
          <span>${feat}</span>
          <span class="sim-control-val" id="simVal_${feat}">${info.categories[0]}</span>
        </div>
        <select class="config-select" id="simInput_${feat}">
          ${optionsHtml}
        </select>
      `;
      elements.simulatorControls.appendChild(item);

      const sel = item.querySelector(`#simInput_${feat}`);
      sel.addEventListener('change', (e) => {
        document.getElementById(`simVal_${feat}`).textContent = e.target.value;
      });
    } else {
      // Numerical slider
      const min = Math.floor(info.min);
      const max = Math.ceil(info.max);
      const step = (max - min) > 50 ? 1 : 0.1;
      const initial = info.median;

      item.innerHTML = `
        <div class="sim-control-header">
          <span>${feat}</span>
          <span class="sim-control-val" id="simVal_${feat}">${initial}</span>
        </div>
        <input type="range" class="sim-slider" id="simInput_${feat}" min="${min}" max="${max}" step="${step}" value="${initial}">
      `;
      elements.simulatorControls.appendChild(item);

      const slider = item.querySelector(`#simInput_${feat}`);
      slider.addEventListener('input', (e) => {
        document.getElementById(`simVal_${feat}`).textContent = e.target.value;
      });
    }
  });

  // Trigger initial simulation
  runSimulation();
}

function initSimulatorEvents() {
  elements.btnSimulate.addEventListener('click', runSimulation);
}

async function runSimulation() {
  if (!state.predictionResult) return;

  const targetCol = state.predictionResult.target_column;
  const taskType = state.predictionResult.task_type;
  const featureNames = state.predictionResult.feature_names;

  const featurePayload = {};
  featureNames.forEach(feat => {
    const input = document.getElementById(`simInput_${feat}`);
    if (input) {
      featurePayload[feat] = input.value;
    }
  });

  try {
    const res = await fetch('/api/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        target_column: targetCol,
        task_type: taskType,
        features: featurePayload
      })
    });

    if (!res.ok) throw new Error('Simulation failed');
    const simResult = await res.json();

    elements.simResultValue.textContent = simResult.predicted_value;

    if (simResult.task_type === 'classification') {
      elements.simConfidenceBarContainer.classList.remove('hidden');
      elements.simConfidenceText.textContent = `${simResult.confidence}%`;
      elements.simProgressBar.style.width = `${simResult.confidence}%`;

      if (simResult.probabilities) {
        elements.simClassProbabilities.innerHTML = simResult.probabilities.map(p => `
          <div class="sim-class-item">
            <span>${p.label}</span>
            <span style="font-weight: 700; color: #f59e0b;">${p.probability}%</span>
          </div>
        `).join('');
      }
    } else {
      elements.simConfidenceBarContainer.classList.add('hidden');
      elements.simClassProbabilities.innerHTML = '';
    }
  } catch (err) {
    console.error('Simulation error:', err);
  }
}

// ==========================================
// Export & DEV Post Markdown Generator
// ==========================================
function initExportEvents() {
  elements.btnExportCSV.addEventListener('click', exportPredictionsCSV);
  elements.btnCopyDevPost.addEventListener('click', copyDevPostMarkdown);
}

function exportPredictionsCSV() {
  if (!state.predictionResult || !state.predictionResult.sample_predictions) return;

  const preds = state.predictionResult.sample_predictions;
  let csv = 'RowIndex,Actual,TabPFN_Predicted,Confidence_Or_Error,Result\n';
  preds.forEach(p => {
    csv += `${p.row_index},"${p.actual}","${p.predicted}",${p.confidence || p.error},"${p.match ? 'Correct' : 'Miss'}"\n`;
  });

  const blob = new Blob([csv], { type: 'text/csv' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.setAttribute('href', url);
  a.setAttribute('download', `slothpfn_predictions_${Date.now()}.csv`);
  a.click();
  showToast('Exported predictions CSV!', '📥');
}

function generateDevPostMarkdown(result) {
  const isClf = result.task_type === 'classification';
  const metricVal = isClf ? `${result.metrics.tabpfn.accuracy}% Accuracy` : `R² = ${result.metrics.tabpfn.r2_score}`;
  const baseVal = isClf ? `${result.metrics.baseline.accuracy}%` : `R² = ${result.metrics.baseline.r2_score}`;
  const timeSaved = result.sloth_insights.time_saved_estimate;
  const topFeatures = result.feature_importance.slice(0, 3).map(f => f.feature).join(', ');

  const md = `---
title: "SlothPFN: Zero-Effort Tabular AI Agent with Prior Labs TabPFN"
published: false
tags: devchallenge, hf26challenge, ai, machinelearning, tabpfn
---

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 3: Slow and Steady](https://dev.to/challenges/hacktoberfest-week3-2026-10-19)*

## What I Built
**SlothPFN** is an open-source tabular AI agent built for unapologetically lazy developers and data scientists. In celebration of International Sloth Day, SlothPFN automates the most dreaded parts of data science: manual feature encoding, missing value imputation, hyperparameter tuning loops, and model benchmarking.

Users drop any raw CSV file and do *literally nothing*. SlothPFN instantly infers column semantics, auto-detects target objectives, runs Prior Labs' pre-trained **TabPFN** foundation model in a single forward pass, generates causal feature drivers, and launches an interactive scenario simulator.

## Demo
- **Live Demo / Web Interface:** [Explore SlothPFN Live Demo](#)
- **Video Walkthrough:** [YouTube / Loom Demo Link](#)

## Code
{% github https://github.com/your-username/slothpfn %}

## How I Built It
- **Core AI:** Powered by [Prior Labs' TabPFN-3.5](https://priorlabs.ai) foundation model for tabular data. Instead of fitting gradient-boosted decision trees over hundreds of iterations, TabPFN operates as a pre-trained transformer over causal priors, producing calibrated Bayesian posterior distributions in less than 2 seconds.
- **Backend:** Built using Python 3.14 with FastAPI, Pandas, and Scikit-Learn for baseline benchmarking and scenario simulation.
- **Frontend:** Responsive, glassmorphic dark-mode dashboard built with vanilla CSS, modern typography (Outfit & Inter), and Chart.js visualizations.

## Why Does Open Innovation Matter?
Open innovation is essential for tabular AI because sensitive business and personal data (such as financial records, patient diagnostics, and customer churn) should never be blindly streamed to closed proprietary cloud APIs. 
With open-weight models like **TabPFN**, full Bayesian tabular inference can run locally on standard consumer CPUs and GPUs without internet access, zero API costs, and total data privacy.

## The Lazy Payoff
- **Effort Saved:** An estimated **${timeSaved}** by eliminating manual hyperparameter grid searching and one-hot encoding pipelines.
- **Results:** On dataset \`${result.filename}\`, TabPFN achieved **${metricVal}** (compared to traditional baseline of ${baseVal}) with top drivers being **${topFeatures}**.

## Prize Categories
- **Primary Track:** Hacktoberfest Open-Source AI Challenge: Week 3 (Slow and Steady)
- **Partner Category:** Best Use of TabPFN ($200 Prior Labs Partner Prize)

<!-- Optional: Embed your DevRelay Agent Session Transcript -->
<!-- {% agent_session session_id %} -->
`;

  elements.devPostMarkdown.value = md;
}

function copyDevPostMarkdown() {
  elements.devPostMarkdown.select();
  navigator.clipboard.writeText(elements.devPostMarkdown.value);
  showToast('Copied DEV submission markdown to clipboard!', '📋');
}

// ==========================================
// Prior Labs Settings Modal
// ==========================================
function initModalEvents() {
  elements.btnOpenSettings.addEventListener('click', () => {
    elements.tokenModal.classList.remove('hidden');
    elements.modalTokenInput.focus();
  });

  elements.btnCloseModal.addEventListener('click', closeModal);
  elements.btnCancelToken.addEventListener('click', closeModal);

  elements.btnSaveToken.addEventListener('click', async () => {
    const token = elements.modalTokenInput.value.trim();
    showToast('Validating Prior Labs token...', '🔑');

    try {
      const res = await fetch('/api/settings/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: token })
      });

      const data = await res.json();
      elements.engineModeText.textContent = data.mode;
      if (data.is_live_tabpfn) {
        elements.engineModeBadge.className = 'status-pill status-live';
        showToast('TabPFN-3.5 Live Engine Connected!', '🟢');
      } else {
        elements.engineModeBadge.className = 'status-pill status-demo';
        showToast('Running in Prior Simulator Mode', 'ℹ️');
      }
      closeModal();
    } catch (err) {
      showToast('Error setting token', '❌');
    }
  });

  elements.tokenModal.addEventListener('click', (e) => {
    if (e.target === elements.tokenModal) closeModal();
  });
}

function closeModal() {
  elements.tokenModal.classList.add('hidden');
}

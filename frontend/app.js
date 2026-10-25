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
  btnExportCSV: document.getElementById('btnExportCSV'),
  toastContainer: document.getElementById('toastContainer'),
  btnPlayBriefing: document.getElementById('btnPlayBriefing'),
  voiceBriefingBtnText: document.getElementById('voiceBriefingBtnText'),
  voiceStatusBadge: document.getElementById('voiceStatusBadge'),
  voiceProviderLabel: document.getElementById('voiceProviderLabel'),
  briefingAudioPlayer: document.getElementById('briefingAudioPlayer'),
  voiceSelect: document.getElementById('voiceSelect'),
  btnRecordVoice: document.getElementById('btnRecordVoice'),
  voiceQuestionInput: document.getElementById('voiceQuestionInput'),
  btnAskVoice: document.getElementById('btnAskVoice'),
  voiceAnswerBox: document.getElementById('voiceAnswerBox'),
  voiceAnswerText: document.getElementById('voiceAnswerText'),
  voiceAnswerStatus: document.getElementById('voiceAnswerStatus'),
  chatAudioPlayer: document.getElementById('chatAudioPlayer'),
  ambientWakeToggle: document.getElementById('ambientWakeToggle'),
  btnClearSession: document.getElementById('btnClearSession'),
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
  initExportEvents();
  initVoiceAgent();
  initAmbientSession();
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

  if (elements.btnClearSession) {
    elements.btnClearSession.addEventListener('click', async () => {
      try {
        await fetch('/api/ambient/clear', { method: 'POST' });
      } catch (_) {}
      state.currentDataset = null;
      state.predictionResult = null;
      lastAmbientTimestamp = Date.now() / 1000;
      elements.datasetDetailsBar.classList.add('hidden');
      elements.configBar.classList.add('hidden');
      elements.resultsSection.classList.add('hidden');
      document.querySelectorAll('.sample-card-btn').forEach(btn => btn.classList.remove('active'));
      showToast('Cleared. Drop a CSV to start!', '🧹');
    });
  }
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
  elements.slothDrivers.innerHTML = insights.key_drivers;
  elements.slothVerdict.innerHTML = insights.lazy_verdict;

  // 2. Metrics & Comparison
  const isClf = result.task_type === 'classification';
  if (isClf) {
    elements.tabpfnScore.textContent = `${result.metrics.tabpfn.accuracy}%`;
    elements.tabpfnScoreLabel.textContent = 'Accuracy';
    elements.tabpfnSpeed.textContent = `${result.metrics.tabpfn.inference_time_sec}s`;

    elements.baselineScore.textContent = `${result.metrics.baseline.accuracy}%`;
    elements.baselineScoreLabel.textContent = 'Baseline';
    elements.baselineSpeed.textContent = `${result.metrics.baseline.inference_time_sec}s`;

    const diff = (result.metrics.tabpfn.accuracy - result.metrics.baseline.accuracy).toFixed(1);
    const sign = diff >= 0 ? '+' : '';
    elements.speedupFactor.textContent = `${sign}${diff}%`;
  } else {
    elements.tabpfnScore.textContent = result.metrics.tabpfn.r2_score;
    elements.tabpfnScoreLabel.textContent = 'R²';
    elements.tabpfnSpeed.textContent = `${result.metrics.tabpfn.inference_time_sec}s`;

    elements.baselineScore.textContent = result.metrics.baseline.r2_score;
    elements.baselineScoreLabel.textContent = 'Baseline';
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
// Export CSV
// ==========================================
function initExportEvents() {
  elements.btnExportCSV.addEventListener('click', exportPredictionsCSV);
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

// ==========================================
// ElevenLabs Voice Agent & Lazy Briefing
// ==========================================
let voiceState = {
  hasElevenLabs: false,
  isPlayingBriefing: false,
  isPlayingChat: false,
  ambientWakeActive: false,
  selectedVoiceId: 'JBFqnCBsd6RMkjVDRZzb',
};

let speechRecognitionInstance = null;
let isRecordingMic = false;
let lastAmbientTimestamp = 0;

async function initVoiceAgent() {
  try {
    const res = await fetch('/api/voice/status');
    if (res.ok) {
      const data = await res.json();
      voiceState.hasElevenLabs = data.has_elevenlabs;
      voiceState.selectedVoiceId = data.voice_id || 'JBFqnCBsd6RMkjVDRZzb';

      if (elements.voiceProviderLabel) {
        if (data.has_elevenlabs) {
          elements.voiceProviderLabel.textContent = 'ElevenLabs AI Voice Active';
          elements.voiceStatusBadge.classList.add('elevenlabs');
        } else {
          elements.voiceProviderLabel.textContent = 'Browser Speech Voice';
          elements.voiceStatusBadge.classList.remove('elevenlabs');
        }
      }

      if (elements.voiceSelect && data.voices && data.voices.length > 0) {
        elements.voiceSelect.innerHTML = data.voices.map(v => `
          <option value="${v.voice_id}" ${v.voice_id === data.voice_id ? 'selected' : ''}>
            ${v.label || v.name}
          </option>
        `).join('');
      }
    }
  } catch (e) {
    console.warn('Voice status check failed, using browser speech fallback', e);
  }

  // Voice selector change listener
  if (elements.voiceSelect) {
    elements.voiceSelect.addEventListener('change', (e) => {
      voiceState.selectedVoiceId = e.target.value;
      showToast(`Selected voice: ${e.target.options[e.target.selectedIndex].text}`, '🎙️');
    });
  }

  // Ambient Wake Toggle Listener
  if (elements.ambientWakeToggle) {
    elements.ambientWakeToggle.addEventListener('change', (e) => {
      voiceState.ambientWakeActive = e.target.checked;
      if (voiceState.ambientWakeActive) {
        showToast('Ambient Wake Active! Say "Hey Sloth" anytime.', '🦥');
        startAmbientListening();
      } else {
        showToast('Ambient Wake Deactivated.', '💤');
        stopAmbientListening();
      }
    });
  }

  // Briefing button
  if (elements.btnPlayBriefing) {
    elements.btnPlayBriefing.addEventListener('click', toggleBriefingAudio);
  }

  // Audio player end listeners
  if (elements.briefingAudioPlayer) {
    elements.briefingAudioPlayer.addEventListener('ended', onBriefingEnded);
    elements.briefingAudioPlayer.addEventListener('pause', () => {
      if (!elements.briefingAudioPlayer.ended) onBriefingEnded();
    });
  }

  // Voice Q&A ask button & enter key
  if (elements.btnAskVoice && elements.voiceQuestionInput) {
    elements.btnAskVoice.addEventListener('click', () => {
      const q = elements.voiceQuestionInput.value.trim();
      if (q) handleAskVoice(q);
    });

    elements.voiceQuestionInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        const q = elements.voiceQuestionInput.value.trim();
        if (q) handleAskVoice(q);
      }
    });
  }

  // Quick Chips
  document.querySelectorAll('.qa-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const q = chip.getAttribute('data-q');
      if (elements.voiceQuestionInput) elements.voiceQuestionInput.value = q;
      handleAskVoice(q);
    });
  });

  // Microphone Speech-to-Text Setup
  initSpeechRecognition();
}

function startAmbientListening() {
  if (!speechRecognitionInstance) return;
  if (voiceState.isPlayingBriefing || voiceState.isPlayingChat) return;

  try {
    speechRecognitionInstance.start();
  } catch (err) {
    // If recognition is already active, ignore InvalidStateError
  }
}

function stopAmbientListening() {
  if (!speechRecognitionInstance) return;
  try {
    speechRecognitionInstance.stop();
  } catch (err) {}
}

function initSpeechRecognition() {
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRec) {
    if (elements.btnRecordVoice) {
      elements.btnRecordVoice.title = "Browser Speech Recognition not supported; type to ask.";
      elements.btnRecordVoice.style.opacity = "0.5";
    }
    if (elements.ambientWakeToggle) {
      elements.ambientWakeToggle.disabled = true;
      elements.ambientWakeToggle.title = "Speech Recognition not supported in this browser.";
    }
    return;
  }

  speechRecognitionInstance = new SpeechRec();
  speechRecognitionInstance.continuous = false; // Using auto-restart on 'end' for consistent cross-browser performance
  speechRecognitionInstance.interimResults = false;
  speechRecognitionInstance.lang = 'en-US';

  speechRecognitionInstance.onstart = () => {
    isRecordingMic = true;
    if (elements.btnRecordVoice && !voiceState.ambientWakeActive) {
      elements.btnRecordVoice.classList.add('recording');
      elements.btnRecordVoice.title = "Listening... Speak your question";
      showToast("Listening... Speak your question now!", "🎙️");
    }
  };

  speechRecognitionInstance.onresult = (event) => {
    if (!event.results || event.results.length === 0) return;
    const transcript = event.results[0][0].transcript.trim();
    if (!transcript) return;

    if (voiceState.ambientWakeActive) {
      const lower = transcript.toLowerCase();
      console.log("[Sloth Ambient Mic]", lower);

      const wakeTriggers = ["hey sloth", "ok sloth", "okay sloth", "hello sloth", "hi sloth", "sloth"];
      let matchedTrigger = null;
      for (const trigger of wakeTriggers) {
        if (lower.startsWith(trigger) || lower.includes(trigger)) {
          matchedTrigger = trigger;
          break;
        }
      }

      if (matchedTrigger) {
        let query = "";
        const idx = lower.indexOf(matchedTrigger);
        query = lower.slice(idx + matchedTrigger.length).replace(/^[,:.\s]+/, '').trim();

        showToast(`🦥 "Hey Sloth" heard: "${transcript}"`, '🎙️');

        if (!query || query.length < 2) {
          query = "Give me a lazy executive summary";
        }

        if (elements.voiceQuestionInput) {
          elements.voiceQuestionInput.value = query;
        }
        handleAskVoice(query);
        return;
      }
      // Non-wake background chatter is ignored in ambient mode
      return;
    }

    // Manual Mic Click Mode
    if (elements.voiceQuestionInput) {
      elements.voiceQuestionInput.value = transcript;
    }
    handleAskVoice(transcript);
  };

  speechRecognitionInstance.onerror = (event) => {
    isRecordingMic = false;
    if (elements.btnRecordVoice) {
      elements.btnRecordVoice.classList.remove('recording');
      elements.btnRecordVoice.title = "Speak your question (Speech-to-Text)";
    }
    if (event.error !== 'no-speech' && !voiceState.ambientWakeActive) {
      showToast("Mic note: " + event.error, "⚠️");
    }
  };

  speechRecognitionInstance.onend = () => {
    isRecordingMic = false;
    if (elements.btnRecordVoice) {
      elements.btnRecordVoice.classList.remove('recording');
      elements.btnRecordVoice.title = "Speak your question (Speech-to-Text)";
    }

    // Auto-restart ambient listening if active and no audio playing
    if (voiceState.ambientWakeActive && !voiceState.isPlayingBriefing && !voiceState.isPlayingChat) {
      setTimeout(() => {
        if (voiceState.ambientWakeActive && !voiceState.isPlayingBriefing && !voiceState.isPlayingChat) {
          startAmbientListening();
        }
      }, 500);
    }
  };

  if (elements.btnRecordVoice) {
    elements.btnRecordVoice.addEventListener('click', () => {
      if (!speechRecognitionInstance) {
        showToast("Speech Recognition not supported in this browser.", "⚠️");
        return;
      }
      if (isRecordingMic) {
        speechRecognitionInstance.stop();
      } else {
        try {
          speechRecognitionInstance.start();
        } catch (e) {
          console.warn("Recognition start warning", e);
        }
      }
    });
  }
}

function stopAllVoiceAudio() {
  if (window.speechSynthesis) window.speechSynthesis.cancel();
  if (elements.briefingAudioPlayer) {
    elements.briefingAudioPlayer.pause();
    elements.briefingAudioPlayer.currentTime = 0;
  }
  if (elements.chatAudioPlayer) {
    elements.chatAudioPlayer.pause();
    elements.chatAudioPlayer.currentTime = 0;
  }
  onBriefingEnded();
}

function onBriefingEnded() {
  voiceState.isPlayingBriefing = false;
  if (elements.btnPlayBriefing) {
    elements.btnPlayBriefing.classList.remove('playing');
    elements.voiceBriefingBtnText.textContent = 'Listen to Sloth Briefing';
  }
  if (voiceState.ambientWakeActive) {
    setTimeout(startAmbientListening, 600);
  }
}

async function toggleBriefingAudio() {
  if (voiceState.isPlayingBriefing) {
    stopAllVoiceAudio();
    return;
  }

  if (!state.predictionResult) {
    showToast('Run a prediction first to generate a briefing!', '🦥');
    return;
  }

  stopAmbientListening();

  try {
    elements.btnPlayBriefing.classList.add('playing');
    elements.voiceBriefingBtnText.textContent = 'Synthesizing Briefing...';
    stopAllVoiceAudio();

    const selectedVoice = elements.voiceSelect ? elements.voiceSelect.value : voiceState.selectedVoiceId;

    if (voiceState.hasElevenLabs) {
      // Use live streaming audio for instantaneous playback
      const streamUrl = `/api/voice/stream?voice_id=${encodeURIComponent(selectedVoice)}`;
      voiceState.isPlayingBriefing = true;
      elements.voiceBriefingBtnText.textContent = 'Pause Briefing';
      elements.briefingAudioPlayer.src = streamUrl;
      await elements.briefingAudioPlayer.play();
    } else {
      const res = await fetch('/api/voice/narrate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: '', voice_id: selectedVoice })
      });

      if (!res.ok) throw new Error('Briefing synthesis request failed');
      const data = await res.json();

      voiceState.isPlayingBriefing = true;
      elements.voiceBriefingBtnText.textContent = 'Speaking (Browser Voice)...';
      speakWithBrowser(data.text, onBriefingEnded);
    }
  } catch (err) {
    console.error('Briefing error:', err);
    showToast('Failed to play briefing audio: ' + err.message, '⚠️');
    onBriefingEnded();
  }
}

async function handleAskVoice(question) {
  if (!question) return;

  stopAllVoiceAudio();
  stopAmbientListening();
  voiceState.isPlayingChat = true;

  if (elements.voiceAnswerBox) elements.voiceAnswerBox.classList.remove('hidden');
  if (elements.voiceAnswerText) elements.voiceAnswerText.textContent = 'Consulting the sloth brain...';
  if (elements.voiceAnswerStatus) elements.voiceAnswerStatus.textContent = 'Thinking...';
  if (elements.btnAskVoice) elements.btnAskVoice.disabled = true;

  try {
    const selectedVoice = elements.voiceSelect ? elements.voiceSelect.value : voiceState.selectedVoiceId;
    const res = await fetch('/api/voice/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: question, voice_id: selectedVoice })
    });

    if (!res.ok) throw new Error('Voice query failed');
    const data = await res.json();

    if (elements.voiceAnswerText) elements.voiceAnswerText.textContent = data.answer;

    if (data.has_audio && data.audio_data) {
      if (elements.voiceAnswerStatus) elements.voiceAnswerStatus.textContent = 'Playing ElevenLabs Audio';
      elements.chatAudioPlayer.classList.remove('hidden');
      elements.chatAudioPlayer.src = data.audio_data;
      await elements.chatAudioPlayer.play();
      elements.chatAudioPlayer.onended = () => {
        voiceState.isPlayingChat = false;
        if (elements.voiceAnswerStatus) elements.voiceAnswerStatus.textContent = 'Finished';
        if (voiceState.ambientWakeActive) setTimeout(startAmbientListening, 600);
      };
    } else {
      if (elements.voiceAnswerStatus) elements.voiceAnswerStatus.textContent = 'Playing Browser Audio';
      elements.chatAudioPlayer.classList.add('hidden');
      speakWithBrowser(data.answer, () => {
        voiceState.isPlayingChat = false;
        if (elements.voiceAnswerStatus) elements.voiceAnswerStatus.textContent = 'Finished';
        if (voiceState.ambientWakeActive) setTimeout(startAmbientListening, 600);
      });
    }
  } catch (err) {
    console.error('Ask voice error:', err);
    voiceState.isPlayingChat = false;
    if (elements.voiceAnswerText) elements.voiceAnswerText.textContent = 'Sorry, could not answer right now: ' + err.message;
    if (elements.voiceAnswerStatus) elements.voiceAnswerStatus.textContent = 'Error';
    if (voiceState.ambientWakeActive) setTimeout(startAmbientListening, 600);
  } finally {
    if (elements.btnAskVoice) elements.btnAskVoice.disabled = false;
  }
}

function speakWithBrowser(text, onEndCallback) {
  if (!window.speechSynthesis) {
    if (onEndCallback) onEndCallback();
    return;
  }
  window.speechSynthesis.cancel();
  const clean = text.replace(/[*_#`🦥⚡🌿]/g, '').trim();
  const utterance = new SpeechSynthesisUtterance(clean);
  utterance.rate = 0.95;
  utterance.pitch = 0.95;
  utterance.onend = () => {
    if (onEndCallback) onEndCallback();
  };
  utterance.onerror = () => {
    if (onEndCallback) onEndCallback();
  };
  window.speechSynthesis.speak(utterance);
}

// ==========================================
// Ambient Session Sync (Folder Watcher / Right Click)
// ==========================================
function initAmbientSession() {
  checkAmbientSession();
  window.addEventListener('focus', checkAmbientSession);
  setInterval(checkAmbientSession, 5000);
}

async function checkAmbientSession() {
  try {
    const res = await fetch('/api/ambient/session');
    if (!res.ok) return;
    const data = await res.json();
    if (data.has_ambient_session && data.session && data.session.result) {
      const s = data.session;
      if (s.timestamp && s.timestamp > lastAmbientTimestamp) {
        lastAmbientTimestamp = s.timestamp;
        state.predictionResult = s.result;
        renderResults(s.result);
        if (elements.metaFilename) elements.metaFilename.textContent = s.filename || 'Ambient Dataset';
        if (elements.metaRows) elements.metaRows.textContent = `${s.row_count || (s.result.training_samples + s.result.test_samples)} rows`;
        if (elements.metaCols) elements.metaCols.textContent = `${s.result.feature_count} features`;
        if (elements.metaTask) elements.metaTask.textContent = s.task_type || s.result.task_type;
        if (elements.datasetDetailsBar) elements.datasetDetailsBar.classList.remove('hidden');
        showToast(`🦥 Ambient data loaded: ${s.filename}`, '⚡');
      }
    }
  } catch (err) {
    // Non-blocking sync check
  }
}

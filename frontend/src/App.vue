<script setup>
import { ref, computed, onMounted, onUnmounted, onBeforeUpdate } from 'vue';
import axios from 'axios';
import MacroChart from './components/MacroChart.vue';
import StockChart from './components/StockChart.vue';
import GlobalDashboard from './components/GlobalDashboard.vue';
import PredictingCard from './components/PredictingCard.vue';
import FinancialCard from './components/FinancialCard.vue';

// ─── State ────────────────────────────────────────────────────────────
const searchQuery = ref('');
const isLoading = ref(false);
const lastUpdated = ref('--:--:--');
const errorMsg = ref('');
const reportData = ref(null);
const activeTab = ref('swot');
const macroChartRefs = ref([]);
const isRefreshingCharts = ref(false);
const aiReady = ref(false);
const aiStatusMsg = ref('Initializing AI engine...');
let statusPollTimer = null;

// Poll backend until AI engine is ready
const checkAiStatus = async () => {
  try {
    const res = await axios.get('/api/status');
    lastUpdated.value = new Date().toLocaleTimeString('zh-TW', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
    if (res.data.ai_ready) {
      aiReady.value = true;
      aiStatusMsg.value = 'AI Engine Ready';
      clearInterval(statusPollTimer);
    } else {
      aiStatusMsg.value = res.data.message || 'AI engine is preparing...';
    }
  } catch {
    aiStatusMsg.value = 'Waiting for backend connection...';
  }
};

onMounted(() => {
  checkAiStatus();
  statusPollTimer = setInterval(checkAiStatus, 2000);
});

onUnmounted(() => clearInterval(statusPollTimer));
onBeforeUpdate(() => {
  macroChartRefs.value = [];
});

const refreshAllCharts = async () => {
  if (isRefreshingCharts.value) return;
  isRefreshingCharts.value = true;
  await Promise.all(macroChartRefs.value.map(chart => chart?.refresh()));
  isRefreshingCharts.value = false;
};

// ─── Computed ─────────────────────────────────────────────────────────
const displayedNews = computed(() => {
  if (!reportData.value?.news_context) return [];
  const groups = {};
  reportData.value.news_context.forEach(item => {
    if (!groups[item.keyword]) groups[item.keyword] = [];
    if (groups[item.keyword].length < 6) groups[item.keyword].push(item);
  });
  return Object.values(groups).flat();
});

const sentimentClass = computed(() => {
  const s = reportData.value?.analysis_report?.market_sentiment;
  if (s === 'Bullish' || s === '偏多') return 'up';
  if (s === 'Bearish' || s === '偏空') return 'dn';
  return 'neu';
});

// ─── Actions ──────────────────────────────────────────────────────────
const analyzeStock = async () => {
  const target = searchQuery.value.trim();
  if (!target) return;
  isLoading.value = true;
  errorMsg.value = '';
  try {
    const response = await axios.post('/api/analyze', {
      ticker: target
    });
    reportData.value = response.data.data;
    activeTab.value = 'swot';
  } catch (err) {
    errorMsg.value = err.response?.data?.detail || 'Request failed, please check if the backend is running.';
  } finally {
    isLoading.value = false;
  }
};
</script>

<template>
  <div class="app-shell">

    <!-- ═══ HEADER ════════════════════════════════════════════════ -->
    <header class="top-bar">
      <div class="logo-block">
        <span class="logo-icon">✦</span>
        <div class="logo-words">
          <span class="logo-main">AI <strong>QUANT</strong></span>
          <span class="logo-sub">INTELLIGENCE PLATFORM</span>
        </div>
      </div>

      <div class="header-source-info">
        <span class="source-label">Data Sources: Yahoo Finance · FRED | Last Update: {{ lastUpdated }}</span>
      </div>

      <div class="bar-status">
        <div class="live-pill">
          <span class="live-dot"></span>
          <span class="live-text font-mono">LIVE DATA</span>
        </div>
        <span v-if="reportData" class="ticker-readout font-mono">{{ reportData.stock_info?.symbol }}</span>
      </div>
    </header>


    <!-- ═══ MAIN ══════════════════════════════════════════════════ -->
    <div class="main-grid">

      <!-- ── LEFT: Global Market Dashboard (always visible) ───── -->
      <section class="panel-section market-section">
        <div class="section-label">
          <span class="section-icon">🌐</span>
          <span>Global Market Overview</span>
          <span class="section-badge">Auto-refresh 60s</span>
        </div>
        <GlobalDashboard class="market-content" :ready="aiReady" />
      </section>

      <!-- ── RIGHT: Analysis Zone (always visible, prominent CTA) -->
      <aside class="panel-section analysis-section" :class="{ 'has-results': reportData }">

        <!-- CTA Header -->
        <div class="analysis-cta-block">
          <div class="cta-eyebrow">
            <span class="cta-icon">⚡</span>
            <span class="cta-title">Stock Analysis</span>
            <span class="cta-sub">POWERED BY GEMINI AI</span>
          </div>

          <!-- Search Row -->
          <div class="search-row">
            <div class="search-box" :class="{ 'is-loading': isLoading }">
              <span class="search-pfx">⌕</span>
              <input
                v-model="searchQuery"
                type="text"
                placeholder="Enter stock ticker (e.g. 2330.TW, AAPL)"
                @keyup.enter="analyzeStock"
                class="search-inp font-mono"
                id="ticker-input"
                :disabled="isLoading || !aiReady"
              />
              <button
                @click="analyzeStock"
                :disabled="isLoading || !searchQuery.trim() || !aiReady"
                class="analyze-btn"
                id="analyze-btn"
                :title="!aiReady ? aiStatusMsg : 'Run Analysis'"
              >
                <span v-if="isLoading" class="spin-ring"></span>
                <template v-else-if="!aiReady">
                  <span class="ai-init-dot"></span>
                  <span>Initializing</span>
                </template>
                <span v-else>⚡ Analyze</span>
              </button>
            </div>
          </div>

          <!-- Error -->
          <div v-if="errorMsg" class="err-bar">
            <span>⚠ {{ errorMsg }}</span>
          </div>
        </div>

        <!-- ── IDLE: No Results -->
        <div v-if="!reportData && !isLoading" class="idle-placeholder">
          <div class="idle-radar">
            <div class="radar-ring">
              <div class="radar-sweep"></div>
              <div class="radar-center-dot"></div>
            </div>
          </div>
          <p class="idle-hint">Enter a ticker and click "Analyze"</p>
          <p class="idle-hint-sub">AI will analyze SWOT, market sentiment, risks, and macro environment</p>
        </div>

        <!-- ── LOADING -->
        <div v-else-if="isLoading" class="ana-loading">
          <div class="big-radar">
            <div class="radar-ring big">
              <div class="radar-sweep"></div>
              <div class="radar-center-dot"></div>
            </div>
          </div>
          <div class="loading-lbl font-mono">ANALYZING {{ searchQuery?.toUpperCase() }}</div>
          <div class="loading-sub font-mono">AI · FRED · NEWS · MARKET DATA</div>
        </div>

        <!-- ── RESULTS -->
        <div v-else-if="reportData" class="results-body">

          <!-- 1. Overview Panel -->
          <div class="ana-panel">
            <div class="ana-ph">
              <div class="ana-pt">📊 Market Overview</div>
            </div>
            <div class="eq-strip">
              <div class="eq-name-block">
                <span class="eq-nm">{{ reportData.stock_info?.shortName || 'Unknown Corp' }}</span>
                <span class="eq-sym font-mono">{{ reportData.stock_info?.symbol }}</span>
              </div>
              <div class="eq-badges">
                <span class="eq-sector font-mono">{{ reportData.stock_info?.sector || 'General' }}</span>
                <span :class="`sentiment-chip ${sentimentClass}`">
                  {{ reportData.analysis_report?.market_sentiment || 'Neutral' }}
                  {{ reportData.analysis_report?.sentiment_score || 50 }}/100
                </span>
              </div>
            </div>
            <div class="score-band">
              <div class="score-track">
                <div class="score-fill" :style="`width: ${reportData.analysis_report?.sentiment_score || 50}%`"></div>
              </div>
              <span :class="`score-num font-mono ${sentimentClass}`">{{ reportData.analysis_report?.sentiment_score || 50 }}</span>
            </div>
          </div>

          <!-- 2. Technical Panel -->
          <div class="ana-panel">
            <div class="ana-ph">
              <div class="ana-pt">📈 Technical Analysis</div>
            </div>
            <div class="kline-inner">
              <StockChart :ticker="reportData.stock_info?.symbol" />
            </div>
          </div>

          <!-- 3. Financial Visualization Panel -->
          <div class="ana-panel">
          <FinancialCard :financials="reportData.financials" />
          </div>

          <!-- 4. AI Prediction Panel -->
          <div class="ana-panel">
          <PredictingCard
            ref="predictorRef"
            :ticker="reportData.stock_info?.symbol"
          />
          </div>
          
          <!-- 5. Macro Charts Panel -->
          <div class="ana-panel">
            <div class="ana-ph">
              <div class="ana-pt">💡 Key Macro Indicators — {{ reportData.stock_info?.industry || 'Market Overview' }}</div>
              <button
                class="zone-refresh-btn"
                @click="refreshAllCharts"
                :disabled="isRefreshingCharts"
                title="Refresh All Indicators"
              >
                <span v-if="!isRefreshingCharts">⟳ Refresh</span>
                <span v-else>Loading...</span>
              </button>
            </div>
            <div class="macro-grid">
              <MacroChart
                v-for="(id, idx) in reportData.recommended_charts"
                :key="id"
                :indicator-id="id"
                :ref="el => { if(el) macroChartRefs[idx] = el }"
              />
            </div>
          </div>

          <!-- 6. AI Insights Panel -->
          <div class="ana-panel">
            <div class="ana-ph">
              <div class="ana-pt">🤖 AI Research Report</div>
            </div>
            <div class="ai-tabs">
              <button
                v-for="t in [{id:'swot',l:'SWOT'},{id:'sentiment',l:'Sentiment'},{id:'risk',l:'Risk'},{id:'news',l:'News'}]"
                :key="t.id"
                :class="['ai-tab', {active: activeTab === t.id}]"
                @click="activeTab = t.id"
              >{{ t.l }}</button>
            </div>

            <div class="ai-tab-content">
              <!-- SWOT -->
              <div v-if="activeTab === 'swot'" class="tab-pane">
                <p class="report-p">{{ reportData.analysis_report?.swot_analysis || 'Analysis data failed to load.' }}</p>
              </div>
              <!-- Sentiment -->
              <div v-else-if="activeTab === 'sentiment'" class="tab-pane">
                <ul class="reason-ul">
                  <li v-for="(r, i) in (reportData.analysis_report?.sentiment_reasons || [])" :key="i">
                    <span class="r-bul">›</span> {{ r }}
                  </li>
                </ul>
              </div>
              <!-- Risk -->
              <div v-else-if="activeTab === 'risk'" class="tab-pane">
                <div class="risk-block">
                  <span class="risk-ico">⚠</span>
                  <p class="report-p warn">{{ reportData.analysis_report?.risk_warnings || 'No risk assessment data available.' }}</p>
                </div>
              </div>
              <!-- News -->
              <div v-else-if="activeTab === 'news'" class="tab-pane tab-pane--news">
                <div v-for="(n, i) in displayedNews" :key="i" class="news-row">
                  <div class="news-meta">
                    <span class="n-date font-mono">{{ n?.date || 'Today' }}</span>
                    <span class="n-kw">#{{ n?.keyword || 'News' }}</span>
                  </div>
                  <a :href="n?.url || '#'" target="_blank" class="n-title">{{ n?.title || 'No Title Available' }}</a>
                </div>
              </div>
            </div>
          </div>

        </div>
      </aside>
    </div>

  </div>
</template>

<style scoped>
/* ══ Shell ══════════════════════════════════════════════════════════ */
.app-shell {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  background: var(--bg);
}

/* ══ Top Bar ════════════════════════════════════════════════════════ */
.top-bar {
  height: var(--header-h);
  background: var(--surface);
  border-bottom: 1.5px solid #2a4a72;
  display: flex;
  align-items: center;
  padding: 0 16px;
  gap: 14px;
  flex-shrink: 0;
  box-shadow: 0 2px 16px rgba(0,0,0,0.4);
}

.logo-block {
  display: flex;
  align-items: center;
  gap: 9px;
  flex: 1;
}


.logo-icon {
  color: var(--accent-blue);
  font-size: 20px;
  line-height: 1;
  filter: drop-shadow(0 0 8px rgba(59,130,246,0.6));
}

.logo-words {
  display: flex;
  flex-direction: column;
  line-height: 1.1;
}

.logo-main {
  font-size: 14px;
  font-weight: 400;
  color: var(--text-secondary);
  letter-spacing: 2.5px;
  text-transform: uppercase;
}
.logo-main strong { color: var(--text); font-weight: 800; }

.logo-sub {
  font-size: 11px;
  color: var(--text-muted);
  letter-spacing: 1.5px;
  text-transform: uppercase;
  font-family: var(--font-mono);
}

.header-source-info {
  flex: 2;
  text-align: center;
}



.bar-status {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  flex: 1;
}

.live-pill {
  display: flex;
  align-items: center;
  gap: 5px;
  background: rgba(34,197,94,0.1);
  border: 1px solid rgba(34,197,94,0.25);
  padding: 3px 10px;
  border-radius: 20px;
}
.live-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--live-color);
  box-shadow: 0 0 6px var(--live-color);
  animation: pulse-dot 2s infinite;
}
.live-text { font-size: 11px; font-weight: 700; color: var(--live-color); letter-spacing: 1px; }

.ticker-readout {
  font-size: 12px;
  font-weight: 700;
  color: var(--accent-cyan);
  background: rgba(34,211,238,0.08);
  border: 1px solid rgba(34,211,238,0.2);
  padding: 3px 10px;
  border-radius: 4px;
}

/* ══ Main Grid ══════════════════════════════════════════════════════ */
.main-grid {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  min-height: 0;
}

/* ══ Section Panel ══════════════════════════════════════════════════ */
.panel-section {
  display: flex;
  flex-direction: column;
  background: var(--panel-bg);
  border: 1.5px solid #2a4a72;
  border-radius: 10px;
  overflow: hidden;
  min-height: 0;
  box-shadow: 0 0 0 1px rgba(59,130,246,0.05), 0 6px 30px rgba(0,0,0,0.5);
}

.section-label {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px 9px;
  background: linear-gradient(180deg, #162640 0%, rgba(15,30,50,0.9) 100%);
  border-bottom: 1.5px solid #2a4a72;
  flex-shrink: 0;
  font-size: 15px;
  font-weight: 700;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 1px;
}

.section-icon { font-size: 14px; }

.section-badge {
  margin-left: auto;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--border);
  padding: 2px 7px;
  border-radius: 10px;
  font-family: var(--font-mono);
  letter-spacing: 0.3px;
}

.market-content {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

/* ══ Analysis Section ════════════════════════════════════════════ */
.analysis-section {
  border-color: rgba(59,130,246,0.4);
  box-shadow:
    0 0 0 1px rgba(59,130,246,0.15),
    0 0 30px rgba(59,130,246,0.08),
    0 6px 30px rgba(0,0,0,0.5);
}
.analysis-section.has-results {
  border-color: #3b82f6;
  box-shadow:
    0 0 0 1px rgba(59,130,246,0.3),
    0 0 40px rgba(59,130,246,0.12),
    0 6px 30px rgba(0,0,0,0.5);
}

/* ── CTA Block ────── */
.analysis-cta-block {
  background: linear-gradient(180deg, #0d1e38 0%, #0f1e32 100%);
  border-bottom: 1.5px solid #2a4570;
  padding: 14px 14px 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex-shrink: 0;
}

.cta-eyebrow {
  display: flex;
  align-items: center;
  gap: 7px;
}
.cta-icon { font-size: 16px; filter: drop-shadow(0 0 6px rgba(250,204,21,0.6)); }
.cta-title { font-size: 15px; font-weight: 800; color: var(--text); letter-spacing: 0.5px; }
.cta-sub {
  font-size: 11px;
  font-weight: 700;
  color: var(--accent-blue);
  background: rgba(59,130,246,0.1);
  border: 1px solid rgba(59,130,246,0.25);
  padding: 2px 7px;
  border-radius: 20px;
  font-family: var(--font-mono);
  letter-spacing: 0.5px;
  margin-left: auto;
}

/* Search Row */
.search-box {
  display: flex;
  align-items: center;
  background: var(--bg);
  border: 1.5px solid var(--border-strong);
  border-radius: 6px;
  padding: 0 4px 0 10px;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.search-box:focus-within, .search-box.is-loading {
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 3px rgba(59,130,246,0.15);
}

.search-pfx { color: var(--text-dim); font-size: 30px; flex-shrink: 0; }
.search-inp {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--text);
  font-size: 12px;
  padding: 8px 6px;
  outline: none;
  min-width: 0;
}
.search-inp::placeholder { color: var(--text-muted); font-family: var(--font-body); font-size: 15px; }
.search-inp:disabled { opacity: 0.5; }

.analyze-btn {
  background: linear-gradient(135deg, #1d4ed8, #3b82f6);
  color: white;
  border: none;
  padding: 7px 18px;
  border-radius: 4px;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
  margin: 3px;
  font-family: var(--font-body);
  min-width: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  letter-spacing: 0.3px;
}
.analyze-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #1e40af, #2563eb);
  box-shadow: 0 0 16px rgba(59,130,246,0.5);
}
.analyze-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.spin-ring {
  width: 14px; height: 14px;
  border: 2px solid rgba(255,255,255,0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 0.7s linear infinite;
}

.err-bar {
  background: rgba(239,68,68,0.08);
  border: 1px solid rgba(239,68,68,0.25);
  border-radius: 5px;
  padding: 7px 10px;
  font-size: 11px;
  color: #ef4444;
}

/* ── Idle Placeholder ──── */
.idle-placeholder {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  padding: 24px;
}

.idle-hint { font-size: 13px; color: var(--text-secondary); text-align: center; }
.idle-hint-sub { font-size: 11px; color: var(--text-dim); text-align: center; line-height: 1.6; max-width: 240px; }

.idle-radar { display: flex; align-items: center; justify-content: center; }
.radar-ring {
  position: relative;
  width: 60px; height: 60px;
  border-radius: 50%;
  border: 1px solid rgba(59,130,246,0.2);
}
.radar-ring.big { width: 80px; height: 80px; }

.radar-ring::before {
  content: ''; position: absolute; inset: -8px;
  border-radius: 50%; border: 1px solid rgba(59,130,246,0.1);
}
.radar-ring::after {
  content: ''; position: absolute; inset: -16px;
  border-radius: 50%; border: 1px solid rgba(59,130,246,0.05);
}

.radar-sweep {
  position: absolute; inset: 0; border-radius: 50%;
  background: conic-gradient(from 0deg, transparent 70%, rgba(59,130,246,0.7) 100%);
  animation: radar-sweep 2.5s linear infinite;
}

.radar-center-dot {
  position: absolute; top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  width: 5px; height: 5px;
  border-radius: 50%;
  background: var(--accent-blue);
  box-shadow: 0 0 10px var(--accent-blue);
}

/* ── Loading State ──── */
.ana-loading {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
}
.big-radar { display: flex; align-items: center; justify-content: center; }
.loading-lbl { font-size: 13px; font-weight: 700; color: var(--text-secondary); letter-spacing: 2px; }
.loading-sub { font-size: 11px; color: var(--text-muted); letter-spacing: 1.5px; }

/* ── Results ──── */
.results-body {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 14px;
  min-height: 0;
}

/* --- High-Density Panel System for Stock Analysis --- */
.ana-panel {
  background: var(--panel-bg);
  border: 1.5px solid #2a4a72;
  border-radius: 8px;
  box-shadow: var(--panel-shadow), inset 0 1px 0 rgba(255,255,255,0.04);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  flex-shrink: 0;
}

.ana-ph {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 9px 12px 8px;
  background: linear-gradient(180deg, var(--surface) 0%, rgba(15,30,50,0.8) 100%);
  border-bottom: 1px solid #2a4570;
  flex-shrink: 0;
}

.ana-pt {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 1px;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Equity Strip */
.eq-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  background: rgba(59,130,246,0.02);
  flex-shrink: 0;
}
.eq-name-block { display: flex; align-items: baseline; gap: 8px; }
.eq-nm { font-size: 18px; font-weight: 800; color: var(--text); }
.eq-sym { font-size: 12px; color: var(--accent-cyan); }
.eq-badges { display: flex; gap: 6px; align-items: center; }
.eq-sector {
  font-size: 11px; font-weight: 700;
  color: var(--text-dim);
  background: rgba(255,255,255,0.05);
  border: 1px solid var(--border);
  padding: 2px 7px; border-radius: 3px;
  text-transform: uppercase; letter-spacing: 0.5px;
}

.sentiment-chip {
  font-size: 11px; font-weight: 700;
  padding: 3px 9px; border-radius: 3px;
  font-family: var(--font-mono);
}
.sentiment-chip.up  { background: rgba(239,68,68,0.12); color: #ef4444; border: 1px solid rgba(239,68,68,0.3); }
.sentiment-chip.dn  { background: rgba(34,197,94,0.1);  color: #22c55e; border: 1px solid rgba(34,197,94,0.25); }
.sentiment-chip.neu { background: rgba(59,130,246,0.1);  color: #60a5fa; border: 1px solid rgba(59,130,246,0.25); }

/* Score Band */
.score-band {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px 14px;
  flex-shrink: 0;
}
.score-track {
  flex: 1; height: 5px;
  background: rgba(255,255,255,0.07);
  border-radius: 3px; overflow: hidden;
}
.score-fill {
  height: 100%;
  background: linear-gradient(90deg, #22c55e, #f59e0b, #ef4444);
  border-radius: 3px; transition: width 0.6s ease;
}
.score-num { font-size: 12px; font-weight: 900; min-width: 40px; text-align: right; }
.score-num.up  { color: #ef4444; }
.score-num.dn  { color: #22c55e; }
.score-num.neu { color: #60a5fa; }

/* KLine Zone */
.kline-inner {
  height: 380px;
  position: relative;
  overflow: hidden;
}
.kline-inner :deep(.kline-container) {
  height: 100%; width: 100%;
  border: none; border-radius: 0; margin: 0;
  padding: 4px 8px; background: transparent; box-shadow: none;
}
.kline-inner :deep(.chart-wrapper) { height: calc(100% - 40px); }

/* AI Zone */
.ai-tabs {
  display: flex;
  padding: 8px 12px;
  background: #0f1828;
  border-bottom: 1px solid var(--border-strong);
  gap: 8px;
  overflow-x: auto;
  scrollbar-width: none;
  flex-shrink: 0;
}
.ai-tabs::-webkit-scrollbar { display: none; }

.ai-tab {
  padding: 7px 16px;
  font-size: 11px;
  font-weight: 800;
  color: var(--text-dim);
  border: 1px solid var(--border-strong);
  background: var(--surface);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  white-space: nowrap;
  font-family: var(--font-body);
  letter-spacing: 0.8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.3);
}
.ai-tab:hover {
  color: var(--text-secondary);
  background: var(--surface-hover);
  border-color: rgba(59,130,246,0.5);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.4);
}
.ai-tab.active {
  color: white;
  background: rgba(59,130,246,0.25);
  border-color: var(--accent-blue);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.15), 0 0 10px rgba(59,130,246,0.3);
}

.ai-tab-content { background: var(--panel-bg); }

.tab-pane { padding: 12px 14px; }
.report-p { font-size: 11px; font-weight: 700; color: var(--text-secondary); line-height: 1.6; }
.report-p.warn { color: var(--warning-color); }

.reason-ul { list-style: none; display: flex; flex-direction: column; gap: 6px; }
.reason-ul li { font-size: 11px; font-weight: 700; color: var(--text-secondary); line-height: 1.5; display: flex; gap: 6px; }
.r-bul { color: var(--accent-blue); font-weight: 900; flex-shrink: 0; }

.risk-block {
  display: flex; gap: 10px;
  padding: 10px 12px;
  background: rgba(239,68,68,0.06);
  border: 1px solid rgba(239,68,68,0.2);
  border-radius: 5px;
  border-left: 3px solid #ef4444;
}
.risk-ico { color: #f59e0b; font-size: 15px; flex-shrink: 0; line-height: 1.8; }

.tab-pane--news { padding: 0; }
.news-row {
  padding: 10px 14px;
  border-bottom: 1px solid var(--border-subtle);
  transition: background 0.1s;
}
.news-row:hover { background: var(--surface-hover); }
.news-meta { display: flex; gap: 8px; align-items: center; margin-bottom: 4px; }
.n-date { font-size: 11px; color: var(--text-muted); font-weight: 700; }
.n-kw { font-size: 11px; color: var(--accent-blue); font-weight: 900; }
.n-title {
  font-size: 11px; font-weight: 700; color: var(--text-secondary); text-decoration: none; line-height: 1.4;
  display: -webkit-box; -webkit-line-clamp: 2; line-clamp: 2;
  -webkit-box-orient: vertical; overflow: hidden;
  transition: color 0.15s;
}
.n-title:hover { color: var(--text); }

/* Macro Zone */
.macro-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1px;
  background: var(--border);
}
.macro-grid :deep(.chart-container) {
  border: none; border-radius: 0;
  padding: 4px; background: var(--panel-bg);
  box-shadow: none; height: 260px;
  transition: background 0.15s;
}
.macro-grid :deep(.chart-container:hover) { background: var(--surface-hover); }

/* ══ Scrollbar ══════════════════════════════════════════════════════ */
.results-body::-webkit-scrollbar { width: 4px; }
.results-body::-webkit-scrollbar-track { background: transparent; }
.results-body::-webkit-scrollbar-thumb { background: var(--border-strong); border-radius: 2px; }

/* ══ Animations ══════════════════════════════════════════════════════ */
@keyframes pulse-dot { 0%,100%{opacity:1}50%{opacity:0.3} }
@keyframes spin { to{transform:rotate(360deg)} }
@keyframes radar-sweep { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }

/* ══ Mobile ══════════════════════════════════════════════════════════ */
@media (max-width: 1060px) {
  .main-grid { grid-template-columns: 1fr; overflow-y: auto; }
  .panel-section { min-height: 480px; }
  .analysis-section { min-height: 600px; }
}

.zone-refresh-btn {
  flex-shrink: 0;
  padding: 3px 10px;
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.3);
  color: var(--accent-blue);
  font-size: 11px;
  font-weight: 700;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  font-family: var(--font-mono);
  letter-spacing: 0.5px;
}
.zone-refresh-btn:hover:not(:disabled) {
  background: var(--accent-blue);
  color: #fff;
  box-shadow: 0 0 8px rgba(59,130,246,0.4);
}
.zone-refresh-btn:disabled {
  opacity: 0.5;
  cursor: wait;
}

/* AI 就緒狀態指示燈 */
.ai-init-dot {
  display: inline-block;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--accent-amber, #f59e0b);
  margin-right: 6px;
  animation: ai-pulse 1.2s ease-in-out infinite;
  vertical-align: middle;
  flex-shrink: 0;
}
@keyframes ai-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%       { opacity: 0.3; transform: scale(0.7); }
}
</style>
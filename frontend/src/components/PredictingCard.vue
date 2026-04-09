<script setup>
import { ref, watch, onUnmounted, nextTick, computed } from 'vue';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart, BarChart } from 'echarts/charts';
import { 
  GridComponent, 
  TooltipComponent, 
  MarkLineComponent, 
  LegendComponent, 
  ToolboxComponent,
  DataZoomComponent
} from 'echarts/components';
import VChart from 'vue-echarts';
import axios from 'axios';

use([
  CanvasRenderer, 
  LineChart, 
  BarChart, 
  GridComponent, 
  TooltipComponent, 
  MarkLineComponent, 
  LegendComponent,
  ToolboxComponent,
  DataZoomComponent
]);

const props = defineProps({
  ticker: { type: String, required: true }
});

const isLoading = ref(false);
const predictResult = ref(null);
const chartOption = ref({});
const shapChartOption = ref({});
const errorMsg = ref('');
const progressText = ref('深度學習模型運算中...');
const showInsights = ref(false);
const insightsLoading = ref(false);

const shapData = ref({});
const selectedModel = ref('');
const modelOptions = computed(() => Object.keys(shapData.value));

const fetchInsights = async () => {
  insightsLoading.value = true;
  try {
    const res = await axios.get(`/api/predict/importance/${props.ticker}`);
    if (res.data.status === 'success') {
        shapData.value = res.data.data;
        if (modelOptions.value.length > 0) {
            selectedModel.value = modelOptions.value[0];
            updateShapChart();
        }
    }
  } catch (err) {
    console.error("無法取得 SHAP 分析:", err);
  } finally {
    insightsLoading.value = false;
  }
};

const updateShapChart = () => {
  if (!selectedModel.value || !shapData.value[selectedModel.value]) return;
  const d = shapData.value[selectedModel.value];
  const combined = d.features.map((f, i) => ({ name: f, score: d.scores[i] }));
  combined.sort((a, b) => a.score - b.score);

  // 設定前 5 高的顏色為金色 (highlight)，其餘為藍色
  const colors = combined.map((_, index) => {
      return index >= combined.length - 5 ? '#fbbf24' : '#3b82f6';
  });

  shapChartOption.value = {
      title: { text: `SHAP 特徵貢獻度 (${selectedModel.value})`, textStyle: { color: '#ffffff', fontSize: 12 } },
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'value', axisLabel: { color: '#ffffff' } },
      yAxis: { type: 'category', data: combined.map(item => item.name), axisLabel: { color: '#ffffff' } },
      series: [{ 
          type: 'bar', 
          data: combined.map(item => item.score), 
          itemStyle: { 
              color: (params) => colors[params.dataIndex] 
          } 
      }]
  };
  };
  watch(selectedModel, updateShapChart);

watch(showInsights, (val) => {
  if (val) fetchInsights();
});

// 當 Ticker 改變時，重置預測結果
watch(() => props.ticker, () => {
  predictResult.value = null;
  errorMsg.value = '';
  showInsights.value = false;
});

let pollTimer = null;

const runPrediction = async () => {
  if (!props.ticker) return;
  if (isLoading.value) return; 

  isLoading.value = true;
  errorMsg.value = '';
  predictResult.value = null;
  showInsights.value = false;
  
  try {
    await axios.post('/api/predict', { ticker: props.ticker });
    if (pollTimer) clearInterval(pollTimer);
    pollTimer = setInterval(pollStatus, 5000);
  } catch (err) {
    isLoading.value = false;
    errorMsg.value = '啟動預測任務失敗，請檢查後端服務。';
    console.error(err);
  }
};

const pollStatus = async () => {
  try {
    const tickerUpper = props.ticker.toUpperCase();
    const response = await axios.get(`/api/predict/status/${tickerUpper}`);
    const task = response.data.task;
    
    if (task.status === 'success') {
      clearInterval(pollTimer);
      handleResult(task.result);
      isLoading.value = false;
    } else if (task.status === 'error') {
      clearInterval(pollTimer);
      errorMsg.value = `預測失敗: ${task.error}`;
      isLoading.value = false;
    } else if (task.progress) {
      progressText.value = task.progress;
    }
  } catch (err) {
    console.warn("輪詢狀態失敗，正在重試...", err);
  }
};

const handleResult = (resData) => {
    predictResult.value = resData;
    const labels = ["D+1", "D+2", "D+3", "D+4", "D+5"];
    const values = resData.forecast.map(v => parseFloat(v.toFixed(2)));
    const lastPrice = resData.last_price;
    const isUp = resData.change_pct >= 0;
    const themeColor = isUp ? '#ef4444' : '#22c55e';

    chartOption.value = {
      tooltip: { 
        trigger: 'axis',
        backgroundColor: 'rgba(15, 23, 42, 0.98)',
        borderColor: '#2a4570',
        borderWidth: 1,
        textStyle: { color: '#f8fafc', fontSize: 11 },
        formatter: (params) => {
          const val = params[0].value;
          const diff = ((val - lastPrice) / lastPrice * 100).toFixed(2);
          const color = diff >= 0 ? '#ef4444' : '#22c55e';
          return `<div style="font-family: var(--font-mono); padding: 4px">
                    <div style="color: #94a3b8; font-size: 11px; margin-bottom: 4px">${params[0].name} 集成預估</div>
                    <div style="font-size: 15px; font-weight: 800; color: #fff">$${val.toFixed(2)}</div>
                    <div style="font-size: 11px; color: ${color}; font-weight: 700">
                      ${diff >= 0 ? '+' : ''}${diff}%
                    </div>
                  </div>`;
        }
      },
      grid: { left: '4%', right: '10%', top: '15%', bottom: '15%', containLabel: true },
      xAxis: { 
        type: 'category', 
        data: labels,
        axisLine: { lineStyle: { color: '#2a4570' } },
        axisLabel: { color: '#8aaccf', fontSize: 11 },
        boundaryGap: false
      },
      yAxis: { 
        type: 'value', 
        scale: true,
        axisLine: { show: false },
        axisLabel: { color: '#8aaccf', fontSize: 11, formatter: (v) => `$${v}` },
        splitLine: { lineStyle: { color: '#1a2a44', type: 'dashed' } }
      },
      series: [{
        data: values,
        type: 'line',
        smooth: 0.3,
        symbol: 'circle',
        symbolSize: 8,
        lineStyle: { color: themeColor, width: 3 },
        itemStyle: { color: themeColor, borderColor: '#fff', borderWidth: 1 },
        areaStyle: {
          color: {
            type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [{ offset: 0, color: themeColor + '44' }, { offset: 1, color: themeColor + '00' }]
          }
        },
        markLine: {
          silent: true,
          symbol: 'none',
          data: [{ yAxis: lastPrice }],
          lineStyle: { color: '#4e7090', type: 'dashed', opacity: 0.6 },
          label: { 
            show: true, position: 'end', formatter: '現價', 
            fontSize: 11, color: '#4e7090', backgroundColor: 'rgba(15, 23, 42, 0.8)'
          }
        }
      }]
    };
};

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer);
});

defineExpose({ runPrediction, isLoading });
</script>

<template>
  <div class="prediction-section">
    <div class="zone-label-fixed">
      <div class="l-left">
        <span class="l-ico">⚡</span>
        <span class="l-title">深度學習集成預測</span>
        <span class="l-tag">MODELS: LSTM+GRU+CNN-LSTM</span>
      </div>
      <button 
        class="l-btn" 
        @click="runPrediction" 
        :disabled="isLoading"
      >
        {{ isLoading ? '運算中...' : '⚡ 執行預測' }}
      </button>
    </div>

    <div class="p-pane">
      <div v-if="isLoading" class="p-loading-overlay">
        <div class="radar-ring">
          <div class="radar-sweep"></div>
          <div class="radar-dot"></div>
        </div>
        <div class="loading-tip">
          <span class="radar-text">{{ progressText }}</span>
          <span class="radar-subtext">正在整合 {{ ticker }} 相關序列資料</span>
        </div>
      </div>

      <div v-if="errorMsg" class="p-error">
        <span class="err-ico">⚠</span>
        <div class="err-txt">{{ errorMsg }}</div>
      </div>

      <template v-else-if="predictResult">
        <!-- Key Multi-variate Stats -->
        <div class="p-stats">
          <div class="p-item">
            <span class="p-lbl">基準價格</span>
            <span class="p-val font-mono">${{ predictResult.last_price.toFixed(2) }}</span>
          </div>
          <div class="p-item">
            <span class="p-lbl">5日預測方向</span>
            <span :class="['p-val font-mono', predictResult.signal]">
              {{ predictResult.change_pct > 0 ? '+' : '' }}{{ predictResult.change_pct.toFixed(2) }}%
            </span>
          </div>
          <div class="p-item-wide">
            <span class="p-lbl">綜合評級策略</span>
            <div :class="['p-strat-badge', predictResult.signal]">
              {{ predictResult.strategy }}
            </div>
          </div>
        </div>

        <div class="charts-single">
           <!-- Price Prediction Trend -->
           <div class="p-chart-box">
             <div class="chart-tag">5日集成趨勢預測 (Deep Learning Ensemble)</div>
             <div class="p-chart-body">
               <v-chart class="chart-canvas" :option="chartOption" autoresize />
             </div>
           </div>
        </div>

        <!-- Insights -->
        <div class="p-insights">
          <button class="insights-toggle" @click="showInsights = !showInsights">
            {{ showInsights ? '▲ 隱藏模型分析' : '▼ 查看詳細模型分析' }}
          </button>
          
          <div v-if="showInsights" class="insights-content">
            <div v-if="insightsLoading" class="feat-loading">
              <div class="shap-spinner"></div>
              <span>正在計算 SHAP 特徵貢獻度...</span>
            </div>
            <div v-else class="shap-chart-container">
              <div class="model-selector" v-if="modelOptions.length > 0">
                <select v-model="selectedModel" class="model-select">
                    <option v-for="m in modelOptions" :key="m" :value="m">{{ m }} Model</option>
                </select>
              </div>
              <v-chart class="shap-chart-canvas" :option="shapChartOption" autoresize />
            </div>
          </div>
        </div>

        <div class="p-foot">
          <span class="p-meta">
            FEATURES: PRICE + 4Q FINANCIALS | CONFIDENCE: {{ (predictResult.confidence * 100).toFixed(0) }}%
          </span>
          <span class="p-disclaimer">※ 整合財報因子之 AI 預算結果，僅供投資參考</span>
        </div>
      </template>

      <div v-else class="p-idle">
        <p>點擊按鈕執行報酬預測</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.prediction-section {
  display: flex; flex-direction: column; 
  background: transparent;
  width: 100%;
  overflow: hidden;
}
.zone-label-fixed {
  padding: 9px 12px 8px;
  background: linear-gradient(180deg, var(--surface) 0%, rgba(15,30,50,0.8) 100%);
  border-bottom: 1px solid #2a4570;
  display: flex; align-items: center; justify-content: space-between;
  white-space: nowrap;
}
.l-left { display: flex; align-items: center; gap: 8px; }
.l-ico { color: var(--accent-blue); font-size: 14px; }
.l-title { 
  font-size: 13px; font-weight: 700; color: var(--text-secondary);
  text-transform: uppercase; letter-spacing: 1px;
}
.l-tag {
  font-size: 10px; color: var(--accent-cyan); font-weight: normal; margin-left: 6px; opacity: 0.7;
}

.l-btn {
  background: rgba(59, 130, 246, 0.15); border: 1px solid rgba(59, 130, 246, 0.4);
  color: var(--accent-blue); font-size: 11px; font-weight: 800; padding: 4px 10px;
  border-radius: 4px; cursor: pointer; transition: all 0.2s; letter-spacing: 0.5px;
}
.l-btn:hover:not(:disabled) { background: var(--accent-blue); color: white; box-shadow: 0 0 12px rgba(59, 130, 246, 0.4); }
.l-btn:disabled { opacity: 0.5; cursor: wait; }

.p-pane { padding: 12px; position: relative; min-height: 200px; }
.p-loading-overlay {
  position: absolute; inset: 0; display: flex; flex-direction: column;
  justify-content: center; align-items: center; gap: 12px;
  background: rgba(8, 14, 26, 0.85); z-index: 20;
}
.loading-tip { display: flex; flex-direction: column; align-items: center; }
.radar-text {
  font-size: 11px; color: var(--accent-blue); font-family: var(--font-mono);
  letter-spacing: 1px; text-transform: uppercase; font-weight: 700;
}
.radar-subtext {
  font-size: 10px; color: var(--text-dim); opacity: 0.6; margin-top: 2px;
}
.radar-ring {
  position: relative; width: 32px; height: 32px; border-radius: 50%;
  border: 1px solid rgba(59, 130, 246, 0.2);
}
.radar-sweep {
  position: absolute; inset: 0; border-radius: 50%;
  background: conic-gradient(from 0deg, transparent 70%, rgba(59, 130, 246, 0.5) 100%);
  animation: radar-sweep 2s linear infinite;
}
.radar-dot {
  position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
  width: 4px; height: 4px; border-radius: 50%; background: #3b82f6; box-shadow: 0 0 6px #3b82f6;
}

.p-error { border: 1px solid rgba(239,68,68,0.2); background: rgba(239,68,68,0.05); padding: 12px; border-radius: 6px; display: flex; align-items: center; gap: 10px; color: var(--up-color); }
.err-ico { font-size: 16px; font-weight: 700; }
.err-txt { font-size: 11px; font-weight: 700; }

.p-stats { display: grid; grid-template-columns: 1fr 1fr 1.5fr; gap: 10px; margin-bottom: 12px; }
.p-item, .p-item-wide { display: flex; flex-direction: column; gap: 4px; padding: 8px 10px; background: rgba(255,255,255,0.02); border: 1px solid var(--border-subtle); border-radius: 4px; }
.p-lbl { font-size: 12px; color: #ffffff; text-transform: uppercase; font-weight: 800; letter-spacing: 0.5px; }
.p-val { font-size: 12px; font-weight: 900; color: #ffffff; }
.p-val.buy { color: var(--up-color); }
.p-val.sell { color: var(--down-color); }
.p-strat-badge { font-size: 11px; font-weight: 900; padding: 4px 8px; border-radius: 3px; border: 1px solid transparent; text-align: center; }
.p-strat-badge.buy { color: var(--up-color); background: rgba(239, 68, 68, 0.1); border-color: rgba(239, 68, 68, 0.2); }
.p-strat-badge.sell { color: var(--down-color); background: rgba(34, 197, 94, 0.08); border-color: rgba(34, 197, 94, 0.2); }
.p-strat-badge.hold { color: #ffffff; background: rgba(59, 130, 246, 0.08); border-color: rgba(59, 130, 246, 0.2); }

.charts-single { display: block; margin-top: 12px; }
.p-chart-box { background: var(--bg-secondary); border: 1px solid var(--border-subtle); border-radius: 4px; overflow: hidden; position: relative; }
.chart-tag { position: absolute; top: 6px; left: 10px; font-size: 10px; color: #ffffff; font-weight: 800; z-index: 5; text-transform: uppercase; background: var(--surface); padding: 2px 6px; border-radius: 3px; border: 1px solid var(--border-subtle); }
.p-chart-body { height: 200px; position: relative; }
.chart-canvas { width: 100%; height: 100%; }

.p-insights { margin-top: 12px; border: 1px solid var(--border-subtle); border-radius: 4px; background: rgba(255,255,255,0.01); }
.insights-toggle { width: 100%; background: none; border: none; padding: 8px; color: #ffffff; font-size: 11px; font-weight: 700; cursor: pointer; text-align: left; }
.insights-content { padding: 12px; border-top: 1px solid var(--border-subtle); }
.insight-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
h4 { font-size: 11px; color: #ffffff; margin-bottom: 8px; text-transform: uppercase; }
.feat-row { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.feat-lbl { font-size: 10px; width: 80px; }
.feat-bar-bg { flex: 1; height: 6px; background: #1e293b; border-radius: 3px; overflow: hidden; }
.feat-bar-fill { height: 100%; background: var(--accent-blue); }
.feat-pct { font-size: 10px; font-family: var(--font-mono); width: 30px; text-align: right; }
.f-step { display: flex; align-items: center; gap: 8px; font-size: 10px; color: #ffffff; margin-bottom: 6px; }
.f-step span { width: 16px; height: 16px; background: var(--accent-blue); color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 9px; font-weight: bold; }

.p-foot { display: flex; justify-content: space-between; align-items: center; margin-top: 10px; padding-top: 8px; border-top: 1px solid var(--border-subtle); }
.p-meta { font-size: 11px; font-family: var(--font-mono); color: #ffffff; font-weight: 800; opacity: 0.9; }
.p-disclaimer { font-size: 11px; color: #ffffff; font-weight: 700; opacity: 0.8; }

.feat-loading { 
  display: flex; flex-direction: column; align-items: center; justify-content: center; 
  padding: 40px; color: var(--accent-blue); font-size: 12px; gap: 10px;
}
.shap-spinner {
  width: 24px; height: 24px; border: 2px solid rgba(59, 130, 246, 0.2);
  border-top-color: var(--accent-blue); border-radius: 50%;
  animation: spin 1s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.model-selector {
  margin-bottom: 0px;
  display: flex;
  justify-content: flex-end;
}
.model-select {
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid #334155;
  color: #ffffff;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  outline: none;
  transition: all 0.2s ease;
  min-width: 120px;
}
.model-select:hover {
  border-color: var(--accent-blue);
  background: rgba(30, 41, 59, 0.9);
}
.model-select:focus {
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
}

.shap-chart-container { height: 450px; width: 100%; }
.shap-chart-canvas { width: 100%; height: 100%; }

@keyframes radar-sweep { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
</style>

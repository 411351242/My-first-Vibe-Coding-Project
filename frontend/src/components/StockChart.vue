<script setup>
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart, CandlestickChart } from 'echarts/charts';
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent,
  ToolboxComponent
} from 'echarts/components';
import VChart from 'vue-echarts';
import { ref, watch, onMounted } from 'vue';
import axios from 'axios';

use([
  CanvasRenderer,
  LineChart,
  CandlestickChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent,
  ToolboxComponent
]);

const props = defineProps({
  ticker: { type: String, required: true },
});

const chartOption = ref({});
const isLoading = ref(true);
const chartError = ref('');

const period = ref('5d');
const interval = ref('5m');

const periodOptions = [
  { label: '5 Days', value: '5d' },
  { label: '1 Month', value: '1mo' },
  { label: '60 Days', value: '60d' },
  { label: '1 Year', value: '1y' },
];

const intervalOptions = [
  { label: '5m', value: '5m' },
  { label: '1h', value: '1h' },
  { label: '1d', value: '1d' },
];

const loadChartData = async () => {
  isLoading.value = true;
  chartError.value = '';
  try {
    const res = await axios.get(`/api/kline`, {
      params: { ticker: props.ticker, interval: interval.value, period: period.value }
    });
    
    const d = res.data.data;

    if (!d.values || d.values.length === 0) {
      chartError.value = 'Data not found';
      chartOption.value = {};
      return;
    }
    
    // Calculate the K-line data for the chart
    const upColor = '#ef4444';
    const downColor = '#10b981';

    // Prepare volume data (colored by up/down)
    const volumesData = d.volumes.map((vol, i) => {
      // Determine if the price went up or down
      const isUp = d.values[i][1] > d.values[i][0];
      return {
        value: vol,
        itemStyle: { color: isUp ? upColor : downColor, opacity: 0.5 }
      };
    });

    chartOption.value = {
      title: {
        text: `${props.ticker} K-Line Chart`,
        left: 'left',
        textStyle: { color: '#f8fafc', fontSize: 16 }
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' },
        backgroundColor: 'rgba(15, 23, 42, 0.9)',
        borderColor: '#334155',
        textStyle: { color: '#f8fafc' }
      },
      legend: {
        data: ['Candlestick', 'Volume', d.ma1_name, d.ma2_name],
        top: 0,
        right: 0,
        textStyle: { color: '#ffffff' }
      },
      grid: [
        { left: '5%', right: '5%', height: '55%', top: '15%' },
        { left: '5%', right: '5%', height: '20%', bottom: '15%' }
      ],
      xAxis: [
        {
          type: 'category',
          data: d.times,
          scale: true,
          boundaryGap: false,
          axisLine: { onZero: false },
          splitLine: { show: false },
          axisLabel: { show: false }
        },
        {
          type: 'category',
          gridIndex: 1,
          data: d.times,
          scale: true,
          boundaryGap: false,
          axisLine: { onZero: false },
          splitLine: { show: false },
          axisLabel: { color: '#ffffff' }
        }
      ],
      yAxis: [
        {
          scale: true,
          splitArea: { show: false },
          axisLabel: { color: '#ffffff' },
          splitLine: { lineStyle: { color: '#334155', type: 'dashed' } }
        },
        {
          scale: true,
          gridIndex: 1,
          splitNumber: 2,
          axisLabel: { show: false },
          axisLine: { show: false },
          axisTick: { show: false },
          splitLine: { show: false }
        }
      ],
      dataZoom: [
        { type: 'inside', xAxisIndex: [0, 1], start: 0, end: 100 },
        { show: true, xAxisIndex: [0, 1], type: 'slider', bottom: '0%', start: 0, end: 100, textStyle: {color: '#ffffff'} }
      ],
      series: [
        {
          name: 'K-Line',
          type: 'candlestick',
          data: d.values,          itemStyle: {
            color: upColor, 
            color0: downColor,
            borderColor: upColor,
            borderColor0: downColor
          }
        },
        {
          name: d.ma1_name,
          type: 'line',
          data: d.ma1,
          smooth: true,
          lineStyle: { opacity: 0.8, width: 2, color: '#f59e0b' },
          symbol: 'none'
        },
        {
          name: d.ma2_name,
          type: 'line',
          data: d.ma2,
          smooth: true,
          lineStyle: { opacity: 0.8, width: 2, color: '#3b82f6' },
          symbol: 'none'
        },
        {
          name: 'Volume',          type: 'bar',
          xAxisIndex: 1,
          yAxisIndex: 1,
          data: volumesData
        }
      ]
    };
  } catch(e) {
    console.error(e);
    chartError.value = 'Failed to load chart data.';
  } finally {
    isLoading.value = false;
  }
};

const changePeriod = (p) => {
  if (p === '1y' && interval.value === '5m') return;
  period.value = p;
  loadChartData();
};

const changeInterval = (i) => {
  interval.value = i;
  if (i === '5m' && period.value === '1y') {
    period.value = '60d';
  }
  loadChartData();
};

watch(() => props.ticker, (newTicker) => {
  if(newTicker) loadChartData();
});

onMounted(() => {
  if (props.ticker) loadChartData();
});
</script>

<template>
  <div class="kline-container">
    <div class="kline-header">
      <div class="time-filters">
        <button 
          v-for="opt in periodOptions" 
          :key="opt.value"
          @click="changePeriod(opt.value)"
          :class="{'active': period === opt.value}"
          :disabled="opt.value === '1y' && interval === '5m'"
          class="filter-btn"
        >
          {{ opt.label }}
        </button>
      </div>
      <div class="time-filters">
        <button 
          v-for="opt in intervalOptions" 
          :key="opt.value"
          @click="changeInterval(opt.value)"
          :class="{'active': interval === opt.value}"
          class="filter-btn"
        >
          {{ opt.label }}
        </button>
      </div>
    </div>
    
    <div class="chart-wrapper">
      <div v-if="isLoading" class="loading-overlay">
        <div class="radar-ring">
          <div class="radar-sweep"></div>
          <div class="radar-dot"></div>
        </div>
        <div class="loading-tip">
          <span class="radar-text">Loading {{ ticker }} data...</span>
          <span class="radar-subtext">Calculating trends and optimizing chart view...</span>
        </div>
      </div>
      <div v-else-if="chartError" class="chart-error">
        <div class="error-pulse">!</div>
        <span class="error-msg">{{ chartError }}</span>
        <button class="retry-btn" @click="loadChartData">Retry Loading</button>
      </div>
      <v-chart v-else class="chart" :option="chartOption" autoresize />
    </div>
  </div>
</template>

<style scoped>
/* Container Styles */
.kline-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: transparent;
  border: none;
  border-radius: 0;
  padding: 4px 8px;
  box-shadow: none;
  margin: 0;
}

/* Control Bar Styles */
.kline-header {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
  margin-bottom: 4px;
  flex-shrink: 0;
}

.time-filters {
  display: flex;
  align-items: center;
  gap: 6px;
  background: transparent;
  border: none;
  padding: 2px;
}

.filter-btn {
  background: var(--surface);
  color: #ffffff;
  border: 1px solid var(--border-strong);
  padding: 5px 12px;
  border-radius: 4px;
  font-size: var(--text-xs);
  font-weight: 700;
  font-family: var(--font-mono);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  letter-spacing: 0.3px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

.filter-btn:hover:not(:disabled) {
  color: white;
  background: var(--surface-hover);
  border-color: rgba(59,130,246,0.6);
  transform: translateY(-1px);
  box-shadow: 0 4px 6px rgba(0,0,0,0.3);
}

.filter-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
  box-shadow: none;
}

.filter-btn.active {
  background: rgba(59,130,246,0.25);
  color: white;
  border-color: var(--accent-blue);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.15), 0 0 10px rgba(59,130,246,0.3);
}

/* ─── 图表区域 ────────────────────────────────────────────────────────────────── */
.chart-wrapper {
  position: relative;
  flex: 1;
  min-height: 0;
}

.chart {
  width: 100%;
  height: 100%;
}

/* ?? States ??????????????????????????????????????????????? */
.loading-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 10px;
  background: rgba(8, 14, 26, 0.7);
  z-index: 10;
}

.radar-ring {
  position: relative;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 1px solid rgba(59, 130, 246, 0.25);
}

.radar-sweep {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: conic-gradient(from 0deg, transparent 70%, rgba(59, 130, 246, 0.6) 100%);
  animation: radar-sweep 2s linear infinite;
}

.radar-dot {
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  width: 4px; height: 4px;
  border-radius: 50%;
  background: #3b82f6;
  box-shadow: 0 0 6px #3b82f6;
}

.radar-text {
  font-size: var(--text-xs);
  color: var(--accent-blue);
  font-family: var(--font-mono);
  letter-spacing: 1px;
  text-transform: uppercase;
  font-weight: 700;
}

.radar-subtext {
  font-size: var(--text-xs);
  color: #ffffff;
  opacity: 0.6;
  margin-top: 2px;
}

.loading-tip {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.chart-error {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 12px;
  background: rgba(8, 14, 26, 0.85);
  padding: 2rem;
  text-align: center;
}

.error-pulse {
  font-size: 24px;
  color: var(--accent-amber);
  animation: error-pulse 1.5s infinite;
}

.error-msg {
  color: #ffffff;
  font-size: var(--text-base);
  font-weight: 500;
}

.retry-btn {
  margin-top: 8px;
  padding: 6px 16px;
  background: rgba(245, 158, 11, 0.1);
  border: 1px solid rgba(245, 158, 11, 0.3);
  color: var(--accent-amber);
  font-size: var(--text-xs);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.retry-btn:hover {
  background: var(--accent-amber);
  color: #000;
}

@keyframes error-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.9); }
}

@keyframes radar-sweep {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>


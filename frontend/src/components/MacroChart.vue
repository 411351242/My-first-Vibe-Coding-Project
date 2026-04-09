<script setup>
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart, BarChart } from 'echarts/charts';
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent,
  ToolboxComponent
} from 'echarts/components';
import VChart from 'vue-echarts';
import { ref, onMounted, watch } from 'vue';

// 註�? ECharts 必�??�件
use([
  CanvasRenderer,
  LineChart,
  BarChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent,
  ToolboxComponent
]);

import axios from 'axios';

const props = defineProps({
  indicatorId: {
    type: String,
    required: true
  },
  title: {
    type: String,
    default: '總�??��?'
  }
});

const chartOption = ref({});
const isLoading = ref(true);
const hasEmptyData = ref(false);

const loadRealData = async (id, forceRefresh = false) => {
  isLoading.value = true;
  hasEmptyData.value = false;
  try {
    const url = forceRefresh ? `/api/macro/${id}?refresh=true` : `/api/macro/${id}`;
    const response = await axios.get(url);
    const dataObj = response.data.data;
    
    // 如�??�為沒填 Key ?�傳�?Mock 結�?，�??��??�實結�?，都?��? title/dates/values
    let xAxisData = dataObj.dates || [];
    let seriesData = dataObj.values || [];
    
    // 依照使用?��?求�?保�?官方?��??�稱，�??��??�割?��??�中??    let name = dataObj.title || id;
    if (name.length > 55) {
      name = name.substring(0, 55) + '...';
    }

    if (xAxisData.length === 0) {
      hasEmptyData.value = true;
    } else {
      hasEmptyData.value = false;
    }

    const sourceLink = `https://fred.stlouisfed.org/series/${id}`;

    chartOption.value = {
      title: {
        text: `${name}`,
        subtext: `資�?來�?: FRED (${id}) ??`,
        link: sourceLink,
        sublink: sourceLink,
        target: 'blank',
        subtarget: 'blank',
        left: 'center',
        textStyle: { color: '#f8fafc', fontSize: 13, fontWeight: 'bold' },
        subtextStyle: { color: '#94a3b8', fontSize: 11 }
      },
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(15, 23, 42, 0.9)',
        borderColor: '#334155',
        textStyle: { color: '#f8fafc' }
      },
      grid: {
        left: '5%',
        right: '5%',
        bottom: '15%',
        containLabel: true
      },
      dataZoom: [
        { type: 'inside', start: 0, end: 100 },
        { show: true, type: 'slider', bottom: '0%', start: 0, end: 100, textStyle: { color: '#94a3b8' } }
      ],
      xAxis: {
        type: 'category',
        data: xAxisData,
        axisLabel: { color: '#94a3b8' }
      },
      yAxis: {
        type: 'value',
        axisLabel: { color: '#94a3b8' },
        splitLine: { lineStyle: { color: '#334155', type: 'dashed' } },
        scale: true // �?y 軸�?要永?��? 0 ?��?
      },
      series: [
        {
          data: seriesData,
          type: 'line',
          smooth: true,
          lineStyle: { color: '#3b82f6', width: 3 },
          itemStyle: { color: '#3b82f6' },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(59, 130, 246, 0.5)' },
                { offset: 1, color: 'rgba(59, 130, 246, 0.0)' }
              ]
            }
          }
        }
      ]
    };
  } catch (error) {
    console.error("Chart data fetch failed", error);
  } finally {
    isLoading.value = false;
  }
};

watch(() => props.indicatorId, (newVal) => {
  if(newVal) loadRealData(newVal);
}, { immediate: true });

// 讓父�?(App.vue) ?�以?�叫此方法�?觸發帶快?��??��?強制?�整
defineExpose({
  refresh: () => loadRealData(props.indicatorId, true)
});
</script>

<template>
  <div class="chart-container">
    <div v-if="isLoading" class="loading-overlay">
      <div class="radar-ring">
        <div class="radar-sweep"></div>
        <div class="radar-dot"></div>
      </div>
      <span class="radar-text">LOADING...</span>
    </div>
    
    <div v-else-if="hasEmptyData" class="empty-overlay">
      <span class="empty-icon">⚠</span>
      <span class="empty-text">No Data Available</span>
      <button class="retry-btn" @click="loadRealData(props.indicatorId, true)">
        Retry
      </button>
    </div>
    
    <v-chart v-else class="chart" :option="chartOption" autoresize />
  </div>
</template>

<style scoped>
.chart-container {
  width: 100%;
  height: 200px;
  background: var(--panel-bg);
  border: none;
  border-radius: 0;
  padding: 4px;
  position: relative;
  overflow: hidden;
  box-shadow: none;
  transition: background 0.15s;
}

.chart-container:hover {
  background: var(--surface-hover);
}

.chart {
  width: 100%;
  height: 100%;
}

.loading-overlay, .empty-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 8px;
  background: rgba(8, 14, 26, 0.8);
  z-index: 10;
}

.empty-icon {
  font-size: 24px;
  color: var(--text-muted);
}

.empty-text {
  font-size: var(--text-xs);
  color: var(--text-muted);
}

.retry-btn {
  margin-top: 4px;
  padding: 4px 12px;
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.3);
  color: var(--accent-blue);
  font-size: var(--text-xs);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.retry-btn:hover {
  background: var(--accent-blue);
  color: #fff;
}

.radar-ring {
  position: relative;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 1px solid rgba(59, 130, 246, 0.2);
}

.radar-sweep {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: conic-gradient(from 0deg, transparent 70%, rgba(59, 130, 246, 0.5) 100%);
  animation: radar-sweep 2s linear infinite;
}

.radar-dot {
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  width: 3px; height: 3px;
  border-radius: 50%;
  background: #3b82f6;
  box-shadow: 0 0 4px #3b82f6;
}

.radar-text {
  font-size: var(--text-xs);
  color: #4e7090;
  font-family: var(--font-mono);
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

@keyframes radar-sweep {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}
</style>


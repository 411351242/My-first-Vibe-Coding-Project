<script setup>
import { ref, watch, nextTick, computed } from 'vue';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { BarChart, LineChart, ScatterChart } from 'echarts/charts';
import { 
  GridComponent, 
  TooltipComponent, 
  LegendComponent,
  MarkLineComponent
} from 'echarts/components';
import VChart from 'vue-echarts';

use([
  CanvasRenderer, BarChart, LineChart, ScatterChart,
  GridComponent, TooltipComponent, LegendComponent, MarkLineComponent
]);

const props = defineProps({
  financials: { type: Object, default: null }
});

const fundMode = ref('Quarterly'); // Annual / Quarterly

const epsOption = computed(() => {
  if (!props.financials || !props.financials.eps) return {};
  
  const epsData = props.financials.eps;
  const min = Math.min(...epsData) * 0.95;
  const max = Math.max(...epsData) * 1.05;

  return {
    tooltip: { trigger: 'axis' },
    grid: { left: '15%', right: '10%', top: '15%', bottom: '15%', containLabel: false },
    xAxis: { 
      type: 'category', 
      data: props.financials.dates,
      boundaryGap: true,
      axisLabel: { 
        color: '#8aaccf', 
        fontSize: 10 
      }
    },
    yAxis: { 
      type: 'value', 
      min: min, 
      max: max,
      splitNumber: 5,
      axisLabel: { 
        color: '#8aaccf', 
        fontSize: 10,
        formatter: (value, index) => {
          // 隱藏最大值與最小值刻度
          if (index === 0 || index === 5) return '';
          return value.toFixed(1);
        }
      } 
    },
    series: [{
      name: 'EPS', type: 'scatter', symbolSize: 16,
      data: epsData, 
      itemStyle: { color: '#10b981' }
    }]
  };
});

const formatYAxis = (v) => {
  if (v >= 1e12) return `${(v / 1e12).toFixed(1)}T`;
  if (v >= 1e9) return `${(v / 1e9).toFixed(1)}B`;
  if (v >= 1e6) return `${(v / 1e6).toFixed(1)}M`;
  return `${(v / 1e3).toFixed(0)}K`;
};

const fundOption = computed(() => {
  if (!props.financials) return {};
  
  // 假設 backend 傳來的 props.financials 若有年度數據，通常名稱會不同
  // 目前專注於切換邏輯，需在 fetchData 時準備好資料結構
  const revenue = fundMode.value === 'Quarterly' ? props.financials.revenue : (props.financials.revenue_annual || props.financials.revenue);
  const earnings = fundMode.value === 'Quarterly' ? props.financials.earnings : (props.financials.earnings_annual || props.financials.earnings);
  const dates = fundMode.value === 'Quarterly' ? props.financials.dates : (props.financials.dates_annual || props.financials.dates);
  
  return {
    legend: { data: ['營收', '淨利'], textStyle: { color: '#94a3b8', fontSize: 11 }, top: 0 },
    tooltip: { 
      trigger: 'axis',
      formatter: (params) => {
        let res = params[0].name + '<br/>';
        params.forEach(p => {
          res += `${p.marker} ${p.seriesName}: ${formatYAxis(p.value)}<br/>`;
        });
        return res;
      }
    },
    grid: { left: '4%', right: '4%', top: '5%', bottom: '10%', containLabel: true },
    xAxis: { type: 'category', data: dates, axisLabel: { color: '#8aaccf', fontSize: 10 } },
    yAxis: { 
      type: 'value', 
      axisLabel: { color: '#8aaccf', fontSize: 10, formatter: formatYAxis } 
    },
    series: [
      { name: '營收', type: 'bar', data: revenue, itemStyle: { color: '#3b82f6' } },
      { name: '淨利', type: 'bar', data: earnings, itemStyle: { color: '#8b5cf6' } }
    ]
  };
});
</script>

<template>
  <div class="financial-section">
    <div class="zone-label-fixed">
      <div class="l-left"><span class="l-ico">📊</span><span class="l-title">公司財報趨勢</span></div>
    </div>
    
    <div class="p-pane grid-pane">
      <!-- EPS Chart -->
      <div class="p-chart-box">
        <div class="chart-header">
          <div class="chart-tag">Earnings Per Share</div>
        </div>
        <div class="p-chart-body">
          <v-chart class="chart-canvas" :option="epsOption" autoresize />
        </div>
      </div>
      
      <!-- Revenue/Earnings Chart -->
      <div class="p-chart-box">
        <div class="chart-header">
          <div class="chart-tag">Revenue vs. Earnings</div>
          <div class="toggle-group">
            <button :class="{active: fundMode === 'Annual'}" @click="fundMode = 'Annual'">Annual</button>
            <button :class="{active: fundMode === 'Quarterly'}" @click="fundMode = 'Quarterly'">Quarterly</button>
          </div>
        </div>
        <div class="p-chart-body">
          <v-chart class="chart-canvas" :option="fundOption" autoresize />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.financial-section { background: transparent; width: 100%; overflow: hidden; }
.zone-label-fixed { padding: 9px 12px 8px; background: rgba(15,30,50,0.8); border-bottom: 1px solid #2a4570; }
.l-left { display: flex; align-items: center; gap: 8px; }
.l-title { font-size: 13px; font-weight: 700; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 1px; }

.grid-pane { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; padding: 12px; }
.p-chart-box { background: var(--bg-secondary); border: 1px solid var(--border-subtle); border-radius: 5px; overflow: hidden; }
.chart-header { display: flex; justify-content: space-between; align-items: center; padding: 6px 10px; background: rgba(255,255,255,0.03); }
.chart-tag { font-size: 11px; font-weight: 800; color: #fff; }
.toggle-group { display: flex; border: 1px solid #334155; border-radius: 4px; overflow: hidden; }
.toggle-group button { background: transparent; border: none; color: #94a3b8; padding: 4px 8px; font-size: 11px; cursor: pointer; }
.toggle-group button.active { background: #334155; color: #fff; }

.p-chart-body { height: 300px; }
.chart-canvas { width: 100%; height: 100%; }
</style>
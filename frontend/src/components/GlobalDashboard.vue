<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';
import axios from 'axios';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart, TreemapChart } from 'echarts/charts';
import { GridComponent, TooltipComponent } from 'echarts/components';
import VChart from 'vue-echarts';

use([CanvasRenderer, LineChart, TreemapChart, GridComponent, TooltipComponent]);

const isIndicesExpanded = ref(false);

const data = ref(null);
const isLoading = ref(true);
const isUpdating = ref(false);
const lastUpdated = ref('--:--:--');
const errorMsg = ref('');
let refreshTimer = null;

const load = async () => {
  isUpdating.value = true;
  try {
    const res = await axios.get('/api/market-overview');
    data.value = res.data.data;
    errorMsg.value = '';
    lastUpdated.value = new Date().toLocaleTimeString('zh-TW', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
  } catch (e) {
    errorMsg.value = '市場資料載入失敗';
  } finally {
    isLoading.value = false;
    setTimeout(() => { isUpdating.value = false; }, 1200);
  }
};

onMounted(() => {
  load();
  refreshTimer = setInterval(load, 60000);
});
onUnmounted(() => clearInterval(refreshTimer));

// ?�?� Helpers ?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�
const fmtPct = (v) => {
  if (v === null || v === undefined) return '--';
  return `${v > 0 ? '+' : ''}${v.toFixed(2)}%`;
};
const fmtPrice = (v) => {
  if (v === null || v === undefined) return '--';
  if (v >= 10000) return v.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  if (v >= 1000) return v.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  if (v >= 10) return v.toFixed(2);
  return v.toFixed(4);
};
const isUp = (v) => v !== null && v !== undefined && v > 0;
const isDown = (v) => v !== null && v !== undefined && v < 0;

// Bar width for change-magnitude visualization (cap at 5% = 100%)
const barWidth = (pct) => {
  if (pct === null || pct === undefined) return 0;
  return Math.min(Math.abs(pct) / 5 * 100, 100);
};

// Commodity heatmap cell color
const heatBg = (pct) => {
  if (pct === null || pct === undefined) return 'rgba(255,255,255,0.03)';
  const intensity = Math.min(Math.abs(pct) / 4, 1);
  if (pct > 0) return `rgba(239,68,68,${0.07 + intensity * 0.42})`;
  return `rgba(34,197,94,${0.07 + intensity * 0.38})`;
};

// Macro alert level
const macroLevel = (item) => {
  const v = item.value;
  if (v === null) return 'neutral';
  if (item.id === 'VIXCLS') return v > 20 ? 'danger' : v > 15 ? 'warn' : 'ok';
  if (item.id === 'RECPROUSM156N') return v > 20 ? 'danger' : v > 10 ? 'warn' : 'ok';
  if (item.id === 'T10Y2Y')   return v < 0 ? 'danger' : v < 0.5 ? 'warn' : 'ok';
  if (item.id === 'FEDFUNDS') return v >= 5 ? 'warn' : 'ok';
  if (item.id === 'UNRATE')   return v >= 5 ? 'warn' : 'ok';
  return 'ok';
};
const macroLevelColor = { danger: '#ef4444', warn: '#f59e0b', ok: '#22c55e', neutral: '#4e7090' };

// Max absolute pct for normalization (for relative bars)
const maxIndexPct = computed(() => {
  if (!data.value?.indices) return 3;
  const vals = data.value.indices.map(i => Math.abs(i.change_pct ?? 0));
  return Math.max(...vals, 1);
});
const maxFxPct = computed(() => {
  if (!data.value?.fx) return 1;
  const vals = data.value.fx.map(f => Math.abs(f.change_pct ?? 0));
  return Math.max(...vals, 0.5);
});
const relBarWidth = (pct, max) => {
  if (!pct) return 0;
  return Math.min(Math.abs(pct) / max * 100, 100);
};

const treemapOption = computed(() => {
  if (!data.value?.indices || data.value.indices.length === 0) return null;

  const groups = {
    '美洲 (Americas)': [],
    '歐洲 (Europe)': [],
    '亞洲 (Asia)': [],
    '大�?�?(Oceania)': []
  };
  
  data.value.indices.forEach(idx => {
    const val = idx.change_pct ?? 0;
    const absVal = Math.abs(val);
    const heatColor = heatBg(val);

    const node = {
      name: idx.name,
      value: absVal, // Size mapped to absolute change
      actualChange: val,
      price: idx.price,
      itemStyle: { color: heatColor }
    };
    
    if (idx.region === 'US') groups['美洲 (Americas)'].push(node);
    else if (['UK', 'DE', 'FR'].includes(idx.region)) groups['歐洲 (Europe)'].push(node);
    else if (['JP', 'HK', 'TW', 'CN', 'KR', 'IN'].includes(idx.region)) groups['亞洲 (Asia)'].push(node);
    else if (idx.region === 'AU') groups['大�?�?(Oceania)'].push(node);
    else groups['美洲 (Americas)'].push(node); 
  });

  const treeData = [];
  const geoOrder = ['美洲 (Americas)', '歐洲 (Europe)', '亞洲 (Asia)', '大�?�?(Oceania)'];
  for (const gName of geoOrder) {
    const children = groups[gName];
    if (children && children.length > 0) {
      treeData.push({
        name: gName,
        value: children.reduce((sum, c) => sum + c.value, 0),
        children: children
      });
    }
  }

  return {
    tooltip: {
      backgroundColor: 'rgba(15, 30, 50, 0.9)',
      borderColor: '#2a4570',
      textStyle: { color: '#e2e8f0', fontSize: 12, fontFamily: 'Inter, sans-serif' },
      formatter: function (info) {
        if (info.data.actualChange === undefined) return info.name;
        const v = info.data.actualChange;
        return `<strong>${info.name}</strong><br/><span style="font-family:monospace">${fmtPrice(info.data.price)}</span><br/><span style="color:${v > 0 ? '#ef4444' : '#22c55e'}; font-family:monospace">${v > 0 ? '+' : ''}${v.toFixed(2)}%</span>`;
      }
    },
    toolbox: {
      show: true,
      feature: {
        restore: { 
          title: '?��?縮放', 
          iconStyle: { borderColor: '#cbd5e1' }
        }
      },
      top: 0,
      right: 0
    },
    series: [{
      type: 'treemap',
      data: treeData,
      width: '100%',
      height: '100%',
      sort: false, // Forces the geoOrder layout left-to-right
      roam: true, // Enable mouse wheel zoom and drag pan
      nodeClick: 'zoomToNode', // Click to dive into continents
      breadcrumb: { 
        show: true,
        bottom: 10,
        itemStyle: { color: '#1e293b' },
        textStyle: { color: '#cbd5e1', fontSize: 12, fontFamily: 'Inter, sans-serif' }
      },
      label: {
        show: true,
        formatter: function(params) {
          if (params.data.actualChange === undefined) return params.name;
          const v = params.data.actualChange;
          const px = fmtPrice(params.data.price);
          return `{name|${params.name}}\n{val|${px}}\n{chg|${v > 0 ? '+' : ''}${v.toFixed(2)}%}\n{unit|pts}`;
        },
        rich: {
          name: { fontSize: 13, fontFamily: 'Inter, sans-serif', color: '#ffffff', fontWeight: 'bold', align: 'center', lineHeight: 22 },
          val: { fontSize: 13, fontFamily: 'Inter, monospace', color: '#ffffff', fontWeight: '600', align: 'center', lineHeight: 18 },
          chg: { fontSize: 12, fontFamily: 'Inter, sans-serif', color: '#cbd5e1', align: 'center', lineHeight: 16 },
          unit: { fontSize: 11, fontFamily: 'Inter, sans-serif', color: 'rgba(255,255,255,0.4)', align: 'center', lineHeight: 14 }
        }
      },
      levels: [
        {
          itemStyle: { borderColor: '#0f172a', borderWidth: 2, gapWidth: 4 },
          upperLabel: { show: false }
        },
        {
          itemStyle: { borderColor: '#1e293b', borderWidth: 2, gapWidth: 2 },
          upperLabel: { 
            show: true, 
            height: 24, 
            color: '#cbd5e1', 
            fontSize: 12, 
            fontFamily: 'Inter, sans-serif',
            fontWeight: '600',
            backgroundColor: '#0f172a'
          }
        },
        {
          itemStyle: { borderColor: '#000000', borderWidth: 1, gapWidth: 1 }
        }
      ]
    }]
  };
});

const sparklineOption = (history, color) => ({
  grid: { top: 2, bottom: 2, left: 2, right: 2 },
  xAxis: { type: 'time', show: false },
  yAxis: { type: 'value', show: false, scale: true },
  series: [{
    type: 'line',
    data: history,
    showSymbol: false,
    lineStyle: { color: color, width: 2 },
    areaStyle: {
      color: {
        type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [{ offset: 0, color: color }, { offset: 1, color: 'transparent' }]
      },
      opacity: 0.15
    }
  }],
  tooltip: { trigger: 'axis', textStyle: { fontSize: 11 }, padding: 4 }
});

const updatedTime = computed(() => new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' }));
</script>

<template>
  <div class="gd-root">

    <!-- ?�?� Scrolling Ticker ?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?� -->
    <div class="ticker-bar">
      <div class="ticker-scroll-wrap">
        <div class="ticker-scroll" v-if="data?.indices?.length">
          <template v-for="pass in 2" :key="pass">
            <span v-for="idx in data.indices" :key="`${pass}-${idx.symbol}`" class="t-item">
              <span class="t-rgn font-mono">{{ idx.region }}</span>
              <span class="t-nm">{{ idx.name }}</span>
              <span class="t-pr font-mono">{{ fmtPrice(idx.price) }}</span>
              <span :class="['t-ch font-mono', isUp(idx.change_pct)?'up':isDown(idx.change_pct)?'dn':'neu']">
                {{ fmtPct(idx.change_pct) }}
              </span>
            </span>
          </template>
        </div>
        <div class="ticker-scroll ticker-loading" v-else>
          <span>FETCHING GLOBAL MARKET DATA &nbsp;...&nbsp; PLEASE WAIT &nbsp;...&nbsp; FETCHING GLOBAL MARKET DATA &nbsp;...&nbsp; PLEASE WAIT</span>
        </div>
      </div>
    </div>

    <!-- ?�?� Main Panels ?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?� -->
    <div class="gd-body">

      <!-- LEFT COL -->
      <div class="gd-col">

        <!-- Commodity Heatmap -->
        <div class="gd-panel gd-panel--grow">
          <div class="gd-ph">
            <span class="gd-pt">Commodities</span>
          </div>
          <div class="commodity-hm" v-if="data?.commodities?.length">
            <div
              v-for="c in data.commodities" :key="c.symbol"
              class="hm-cell"
              :style="`background: ${heatBg(c.change_pct)}`"
            >
              <span class="hm-name">{{ c.name }}</span>
              <span class="hm-price font-mono">{{ fmtPrice(c.price) }}</span>
              <span :class="['hm-chg font-mono', isUp(c.change_pct)?'up':isDown(c.change_pct)?'dn':'neu']">
                {{ fmtPct(c.change_pct) }}
              </span>
              <span class="hm-unit">{{ c.unit }}</span>
            </div>
          </div>
          <div class="hm-skeleton" v-else>
            <div v-for="i in 8" :key="i" class="skel-cell shimmer"></div>
          </div>
        </div>

        <!-- Global Indices with ECharts Treemap -->
        <div class="gd-panel gd-panel--grow" :class="{ 'panel-fullscreen': isIndicesExpanded }" style="display: flex; flex-direction: column;">
          <div class="gd-ph">
            <span class="gd-pt">Global Indices</span>
            <button class="expand-btn-small" @click="isIndicesExpanded = !isIndicesExpanded" title="Toggle Fullscreen">
              {{ isIndicesExpanded ? '▲' : '▼' }}
            </button>
          </div>
          <div style="flex: 1; width: 100%; position: relative;">
            <v-chart
              v-if="treemapOption"
              :option="treemapOption"
              autoresize
              style="width: 100%; height: 100%; position: absolute; top: 0; left: 0;"
            />
            <div class="list-skel" v-else style="padding: 12px; height: 100%;">
              <div v-for="i in 10" :key="i" class="skel-row shimmer"></div>
            </div>
          </div>
        </div>

      </div>

      <!-- RIGHT COL -->
      <div class="gd-col">

        <!-- FX with visualization bars -->
        <div class="gd-panel gd-panel--grow">
          <div class="gd-ph">
            <span class="gd-pt">Foreign Exchange</span>
          </div>
          <div class="fx-list" v-if="data?.fx?.length">
            <div v-for="fx in data.fx" :key="fx.symbol" class="fx-row">
              <div class="fx-left">
                <span class="fx-flag">{{ fx.flag }}</span>
                <span class="fx-name font-mono">{{ fx.name }}</span>
              </div>
              <div class="fx-bar-area zero-centered">
                <div class="fx-bar-track-left">
                  <div v-if="isDown(fx.change_pct)" class="fx-bar-fill dn-fill" :style="`width: ${relBarWidth(fx.change_pct, maxFxPct)}%`"></div>
                </div>
                <!-- line separator -->
                <div class="fx-bar-mid-line"></div>
                <div class="fx-bar-track-right">
                  <div v-if="isUp(fx.change_pct)" class="fx-bar-fill up-fill" :style="`width: ${relBarWidth(fx.change_pct, maxFxPct)}%`"></div>
                </div>
              </div>
              <div class="fx-right">
                <span class="fx-price font-mono">{{ fmtPrice(fx.price) }}</span>
                <span :class="['fx-chg font-mono', isUp(fx.change_pct)?'up':isDown(fx.change_pct)?'dn':'neu']">
                  {{ fmtPct(fx.change_pct) }}
                </span>
              </div>
            </div>
          </div>
          <div v-else class="list-skel">
            <div v-for="i in 8" :key="i" class="skel-row shimmer"></div>
          </div>
        </div>

        <!-- Macro Indicators with gauge bars -->
        <div class="gd-panel gd-panel--grow">
          <div class="gd-ph">
            <span class="gd-pt">Macro Indicators</span>
          </div>
          <div class="macro-list" v-if="data?.macro?.length">
            <div v-for="item in data.macro" :key="item.id" class="macro-row">
              <div class="macro-left font-mono">
                <div
                  class="macro-dot"
                  :style="`background: ${macroLevelColor[macroLevel(item)]}; box-shadow: 0 0 6px ${macroLevelColor[macroLevel(item)]}`"
                ></div>
                <div class="macro-txt">
                  <span class="macro-name">{{ item.name }}</span>
                  <span class="macro-id">{{ item.id }}</span>
                </div>
              </div>
              <div class="macro-chart-wrap">
                <v-chart
                  v-if="item.history && item.history.length > 0"
                  :option="sparklineOption(item.history, macroLevelColor[macroLevel(item)])"
                  autoresize
                />
                <div v-else class="spark-none">--</div>
              </div>
              <div class="macro-vals font-mono">
                <span class="macro-val">{{ item.value !== null ? `${item.value}${item.unit}` : '--' }}</span>
                <span
                  :class="['macro-chg', item.change !== null && item.change > 0 ? 'up' : item.change !== null && item.change < 0 ? 'dn' : 'neu']"
                >{{ item.change !== null ? `${item.change > 0 ? '+' : ''}${item.change}` : '' }}</span>
              </div>
            </div>
          </div>
          <div v-else class="list-skel">
            <div v-for="i in 6" :key="i" class="skel-row shimmer"></div>
          </div>

          <!-- Error -->
          <div v-if="errorMsg" class="gd-err">{{ errorMsg }}</div>
        </div>

      </div>
    </div>

  </div>
</template>

<style scoped>
/* ?�?�?� Root ?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?� */
.gd-root {
  height: 100%;
  display: flex;
  flex-direction: column;
  position: relative;
}

.gd-status-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 12px;
  background: rgba(0, 0, 0, 0.2);
  border-bottom: 1px solid rgba(255, 255, 255, 0.03);
  flex-shrink: 0;
}

.sync-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 10px;
  font-weight: 700;
  font-family: var(--font-mono);
  color: var(--text-dim);
}

.sync-dot {
  width: 5px;
  height: 5px;
  background: var(--live-color, #22c55e);
  border-radius: 50%;
  transition: all 0.3s;
}

.is-syncing .sync-dot {
  background: var(--accent-blue, #3b82f6);
  box-shadow: 0 0 8px var(--accent-blue);
  animation: sync-pulse 0.8s infinite;
}

.is-syncing .sync-text {
  color: var(--accent-blue);
}

.last-time {
  font-size: 10px;
  color: #ffffff;
  font-family: var(--font-mono);
}

@keyframes sync-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.3); }
}

.gd-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 16px;
}

/* ?�?�?� Ticker ?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?� */
.ticker-bar {
  display: flex;
  align-items: center;
  height: 30px;
  background: var(--surface);
  border-bottom: 1px solid var(--border-strong);
  overflow: hidden;
  flex-shrink: 0;
}

.ticker-label-pill {
  font-size: var(--text-xs);
  font-weight: 800;
  letter-spacing: 1.5px;
  color: #ffffff;
  background: var(--accent-blue);
  padding: 0 12px;
  height: 100%;
  display: flex;
  align-items: center;
  flex-shrink: 0;
  font-family: var(--font-mono);
}

.ticker-scroll-wrap {
  flex: 1;
  overflow: hidden;
  position: relative;
}

.ticker-scroll {
  display: flex;
  align-items: center;
  white-space: nowrap;
  width: max-content;
  animation: ticker-scroll 80s linear infinite;
}
.ticker-scroll:hover { animation-play-state: paused; }

.ticker-loading {
  font-size: var(--text-xs);
  color: #ffffff;
  font-family: var(--font-mono);
  letter-spacing: 0.5px;
}

@keyframes ticker-scroll {
  from { transform: translateX(0); }
  to   { transform: translateX(-50%); }
}

.t-item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 0 14px;
  border-right: 1px solid var(--border-subtle);
  font-size: var(--text-xs);
}

.t-rgn {
  font-size: var(--text-xs);
  color: #ffffff;
  background: rgba(255,255,255,0.06);
  border: 1px solid var(--border);
  padding: 0 3px;
  border-radius: 2px;
  min-width: 20px;
  text-align: center;
}
.t-nm { color: #ffffff; font-size: var(--text-sm); }
  .t-pr { color: #ffffff; font-size: var(--text-sm); font-weight: 600; }
  .t-ch { font-size: var(--text-sm); }
/* ?�?�?� Body ?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?� */
.gd-body {
  flex: 1;
  display: flex;
  gap: 12px;
  overflow: hidden; /* contain inner scrolling */
}

/* Base state: 2 columns */
.gd-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
}

/* Fullscreen Panel overlay */
.panel-fullscreen {
  position: fixed !important;
  top: 16px;
  left: 16px;
  right: 16px;
  bottom: 16px;
  z-index: 9999;
  background: #0a0f1a !important; /* solid color to prevent bleed */
  box-shadow: 0 0 50px rgba(0,0,0,0.8);
  border: 1px solid var(--border);
  border-radius: 8px;
  /* Override any flex limitations from parents */
  width: auto !important;
  height: auto !important;
  max-width: none !important;
  max-height: none !important;
}

/* ?�?�?� Panel ?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?� */
.gd-panel {
  background: var(--panel-bg);
  border: 1.5px solid #2a4a72;
  border-radius: 8px;
  box-shadow: var(--panel-shadow), inset 0 1px 0 rgba(255,255,255,0.04);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

.gd-panel--grow { flex: 1; }

.gd-ph {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 9px 12px 8px;
  background: linear-gradient(180deg, var(--surface) 0%, rgba(15,30,50,0.8) 100%);
  border-bottom: 1px solid #2a4570;
  flex-shrink: 0;
}

.gd-ph-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.gd-pt {
  font-size: var(--text-sm);
  font-weight: 700;
  color: #ffffff;
  text-transform: uppercase;
  letter-spacing: 1px;
  white-space: nowrap;
}

.gd-meta-hint {
  font-size: var(--text-xs);
  color: #38bdf8;
  background: rgba(56,189,248,0.1);
  border: 1px solid rgba(56,189,248,0.25);
  padding: 2px 5px;
  border-radius: 4px;
  white-space: nowrap;
}

.gd-meta {
  font-size: var(--text-xs);
  color: #ffffff;
  font-family: var(--font-mono);
}

/* ?�?�?� Commodity Heatmap ?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?� */
.commodity-hm {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 4px;
  padding: 8px;
  flex-shrink: 0;
}

.hm-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 95px;
  padding: 4px;
  border-radius: 6px;
  border: 1px solid rgba(255,255,255,0.06);
  gap: 1px;
  transition: filter 0.2s;
  cursor: default;
  overflow: hidden;
}

.hm-name  { font-size: 11px; font-weight: 700; color: #ffffff; text-align: center; line-height: 1.1; white-space: nowrap; }
.hm-price { font-size: 13px; font-weight: 700; color: #ffffff; line-height: 1.1; }
.hm-chg   { font-size: 12px; font-weight: 700; line-height: 1.1; }
.hm-unit  { font-size: 10px; color: #ffffff; line-height: 1.1; white-space: nowrap; }
.hm-skeleton {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 4px;
  padding: 8px;
}
.skel-cell { height: 76px; border-radius: 6px; }

/* ?�?�?� Index List with bars ?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?� */
.idx-list {
  overflow-y: auto;
  flex: 1;
  padding: 4px 0;
}

.idx-row {
  display: grid;
  grid-template-columns: 120px 1fr 120px;
  align-items: center;
  padding: 6px 12px;
  border-bottom: 1px solid var(--border-subtle);
  transition: background 0.12s;
  gap: 8px;
}
.idx-row:hover { background: rgba(59,130,246,0.04); }

.idx-left { display: flex; align-items: center; gap: 7px; }
.idx-rgn {
  font-size: var(--text-xs); color: #ffffff;
  background: rgba(255,255,255,0.05);
  border: 1px solid var(--border);
  padding: 1px 4px; border-radius: 2px;
  min-width: 22px; text-align: center;
  flex-shrink: 0;
}
.idx-name { font-size: var(--text-base); color: #ffffff; font-weight: 500; }

/* Mini bar in the middle */
.idx-bar-area { display: flex; align-items: center; }
.idx-bar-track {
  height: 5px;
  width: 100%;
  background: rgba(255,255,255,0.06);
  border-radius: 3px;
  overflow: hidden;
}
.idx-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.5s ease;
}
.up-fill { background: linear-gradient(90deg, rgba(239,68,68,0.4), #ef4444); }
.dn-fill { background: linear-gradient(90deg, rgba(34,197,94,0.4), #22c55e); }

.idx-right { display: flex; flex-direction: column; align-items: flex-end; gap: 1px; }
.idx-price { font-size: var(--text-base); font-weight: 700; color: #ffffff; }
.idx-chg   { font-size: var(--text-sm); }

.gd-meta {
  font-size: var(--text-xs);
  color: #ffffff;
}

.expand-btn-small {
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.1);
  color: #ffffff;
  border-radius: 4px;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: var(--text-xs);
  transition: all 0.2s;
  padding: 0;
}
.expand-btn-small:hover {
  background: rgba(255,255,255,0.15);
  color: #ffffff;
}

/* ?�?�?� FX List ?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?� */
.fx-list { overflow-y: auto; flex: 1; padding: 4px 0; }

.fx-row {
  display: grid;
  grid-template-columns: 135px 1fr 85px;
  align-items: center;
  padding: 7px 8px;
  border-bottom: 1px solid var(--border-subtle);
  transition: background 0.12s;
  gap: 8px;
}
.fx-row:hover { background: rgba(59,130,246,0.04); }

.fx-left { display: flex; align-items: center; gap: 7px; }
.fx-flag { font-size: var(--text-sm); line-height: 1; }
.fx-name { font-size: var(--text-base); color: #ffffff; font-weight: 600; }

.fx-bar-area { display: flex; align-items: center; width: 100%; }

.fx-bar-track-left {
  flex: 1;
  height: 5px;
  background: rgba(255,255,255,0.03);
  display: flex;
  justify-content: flex-end; /* Grows from right(center) to left */
  border-radius: 2px 0 0 2px;
}
.fx-bar-track-right {
  flex: 1;
  height: 5px;
  background: rgba(255,255,255,0.03);
  display: flex;
  justify-content: flex-start; /* Grows from left(center) to right */
  border-radius: 0 2px 2px 0;
}
.fx-bar-mid-line {
  height: 12px;
  width: 1px;
  background: rgba(255,255,255,0.3);
  margin: 0 1px;
}

.dn-fill {
  height: 100%;
  border-radius: 2px 0 0 2px;
  transition: width 0.5s ease;
  background: linear-gradient(270deg, rgba(34,197,94,0.1), #22c55e);
}
.up-fill {
  height: 100%;
  border-radius: 0 2px 2px 0;
  transition: width 0.5s ease;
  background: linear-gradient(90deg, rgba(239,68,68,0.1), #ef4444);
}

.fx-right { display: flex; flex-direction: column; align-items: flex-end; gap: 1px; }
.fx-price { font-size: var(--text-base); font-weight: 700; color: #ffffff; }
.fx-chg   { font-size: var(--text-sm); }

/* ?�?�?� Macro Indicators ?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?� */
.macro-list { overflow-y: auto; flex: 1; padding: 4px 0; }

.macro-row {
  display: grid;
  grid-template-columns: 135px 1fr 85px;
  align-items: center;
  padding: 8px 8px;
  border-bottom: 1px solid var(--border-subtle);
  transition: background 0.12s;
  gap: 8px;
}
.macro-row:hover { background: rgba(59,130,246,0.04); }

.macro-left { display: flex; align-items: center; gap: 8px; min-width: 0; }
.macro-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  animation: pulse-dot 3s infinite;
}
.macro-txt { display: flex; flex-direction: column; gap: 1px; min-width: 0; }
.macro-name { font-size: var(--text-base); color: #ffffff; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; line-height: 1.2; }
.hm-name, .hm-price, .hm-chg, .hm-unit {
  line-height: 1.2;
}

.macro-id { font-size: 11px; color: #ffffff; opacity: 0.7; }

.macro-chart-wrap { height: 35px; position: relative; }
.spark-none { font-size: var(--text-xs); color: #ffffff; padding-top: 10px; text-align: center; }

.macro-vals { display: flex; flex-direction: column; align-items: flex-end; gap: 1px; }
.macro-val  { font-size: 15px; font-weight: 700; color: #ffffff; }
.macro-chg  { font-size: 12px; }

/* ?�?�?� Index Group (continents) ?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?� */
.idx-group {
  border: 1px solid rgba(255,255,255,0.05);
  border-radius: 6px;
  padding: 6px;
  background: rgba(0,0,0,0.1);
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.idx-group-title {
  font-size: var(--text-xs);
  color: #ffffff;
  margin-bottom: 2px;
  padding-left: 2px;
}
.idx-group-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 4px;
}

/* ?�?�?� Colors ?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?� */
.up  { color: #ef4444; }
.dn  { color: #22c55e; }
.neu { color: var(--text-dim); }

/* ?�?�?� Skeleton ?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?� */
.list-skel { padding: 6px 10px; display: flex; flex-direction: column; gap: 6px; }
.skel-row  { height: 28px; border-radius: 4px; }

.shimmer {
  background: linear-gradient(90deg, var(--surface) 25%, var(--surface-hover) 50%, var(--surface) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite ease-in-out;
}

@keyframes shimmer {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.4; }
}

/* ?�?�?� Error ?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?�?� */
.gd-err {
  margin: 8px;
  padding: 8px 12px;
  background: rgba(239,68,68,0.07);
  border: 1px solid rgba(239,68,68,0.2);
  border-radius: 6px;
  font-size: var(--text-xs);
  color: #ef4444;
}
</style>


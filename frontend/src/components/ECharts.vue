<template>
  <div class="chart-container">
    <div ref="chartRef" class="chart"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps<{
  type: 'line' | 'bar' | 'pie' | 'mix'
  data: any
  title?: string
}>()

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

onMounted(() => {
  if (chartRef.value) {
    chart = echarts.init(chartRef.value)
    updateChart()
    window.addEventListener('resize', handleResize)
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
})

function handleResize() {
  chart?.resize()
}

function updateChart() {
  if (!chart) return

  const isDark = true
  const textColor = '#888'
  const gridColor = 'rgba(255,255,255,0.05)'

  let option: echarts.EChartsOption

  if (props.type === 'line') {
    option = {
      title: props.title ? { text: props.title, left: 'center', textStyle: { color: '#eee', fontSize: 14 } } : undefined,
      tooltip: { trigger: 'axis' },
      legend: { data: props.data.series?.map(s => s.name) || [], textStyle: { color: textColor }, bottom: 0 },
      grid: { left: '3%', right: '3%', bottom: '15%', containLabel: true },
      xAxis: {
        type: 'category',
        data: props.data.xAxis || [],
        axisLabel: { color: textColor },
        axisLine: { lineStyle: { color: gridColor } },
      },
      yAxis: {
        type: 'value',
        axisLabel: { color: textColor },
        splitLine: { lineStyle: { color: gridColor } },
      },
      series: props.data.series?.map(s => ({
        name: s.name,
        type: 'line',
        data: s.data,
        smooth: true,
        lineStyle: { width: 3 },
        itemStyle: { color: s.color || '#a78bfa' },
        areaStyle: s.area ? {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: (s.color || '#a78bfa') + '80' },
            { offset: 1, color: (s.color || '#a78bfa') + '00' },
          ]),
        } : undefined,
      })),
    }
  } else if (props.type === 'bar') {
    option = {
      title: props.title ? { text: props.title, left: 'center', textStyle: { color: '#eee', fontSize: 14 } } : undefined,
      tooltip: { trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: props.data.xAxis || [],
        axisLabel: { color: textColor, rotate: 30 },
        axisLine: { lineStyle: { color: gridColor } },
      },
      yAxis: {
        type: 'value',
        axisLabel: { color: textColor },
        splitLine: { lineStyle: { color: gridColor } },
      },
      series: props.data.series?.map(s => ({
        name: s.name,
        type: 'bar',
        data: s.data,
        barWidth: '40%',
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: s.color || '#a78bfa' },
            { offset: 1, color: (s.color || '#a78bfa') + '60' },
          ]),
          borderRadius: [4, 4, 0, 0],
        },
      })),
    }
  } else if (props.type === 'pie') {
    option = {
      title: props.title ? { text: props.title, left: 'center', textStyle: { color: '#eee', fontSize: 14 } } : undefined,
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      legend: { orient: 'vertical', left: 'left', textStyle: { color: textColor }, bottom: 0 },
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#0a0a1a',
          borderWidth: 2,
        },
        label: { show: false },
        emphasis: {
          label: { show: true, fontSize: 14, fontWeight: 'bold', color: '#eee' },
        },
        data: props.data.series?.[0]?.data || [],
      }],
    }
  } else {
    option = {
      title: props.title ? { text: props.title, left: 'center', textStyle: { color: '#eee', fontSize: 14 } } : undefined,
      tooltip: { trigger: 'axis' },
      legend: { data: props.data.series?.map(s => s.name) || [], textStyle: { color: textColor }, bottom: 0 },
      grid: { left: '3%', right: '3%', bottom: '15%', containLabel: true },
      xAxis: {
        type: 'category',
        data: props.data.xAxis || [],
        axisLabel: { color: textColor },
        axisLine: { lineStyle: { color: gridColor } },
      },
      yAxis: {
        type: 'value',
        axisLabel: { color: textColor },
        splitLine: { lineStyle: { color: gridColor } },
      },
      series: props.data.series?.map(s => ({
        name: s.name,
        type: s.chartType || 'line',
        data: s.data,
        smooth: s.smooth !== false,
        barWidth: s.barWidth || '40%',
        lineStyle: { width: 3 },
        itemStyle: { color: s.color || '#a78bfa' },
        areaStyle: s.area ? {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: (s.color || '#a78bfa') + '80' },
            { offset: 1, color: (s.color || '#a78bfa') + '00' },
          ]),
        } : undefined,
      })),
    }
  }

  chart.setOption(option)
}

watch(() => props.data, () => {
  updateChart()
}, { deep: true })
</script>

<style scoped>
.chart-container {
  width: 100%;
  height: 300px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.05);
  border-radius: 12px;
  padding: 16px;
}

.chart {
  width: 100%;
  height: 100%;
}
</style>

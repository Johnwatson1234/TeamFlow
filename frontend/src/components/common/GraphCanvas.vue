<template>
  <div ref="chartRef" class="graph-canvas"></div>
</template>

<script setup lang="ts">
import * as echarts from 'echarts'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps<{
  nodes: { id: string; label: string; type: string }[]
  edges: { source: string; target: string; label?: string }[]
}>()

const chartRef = ref<HTMLDivElement>()
let chart: echarts.ECharts | null = null

const colorMap: Record<string, string> = {
  member: 'var(--chart-node-member)',
  task: 'var(--chart-node-task)',
  document: 'var(--chart-node-document)',
  message: 'var(--chart-node-message)',
  commit: 'var(--chart-node-commit)',
  review: 'var(--chart-node-review)',
}

const cssVar = (name: string, fallback: string) => {
  if (typeof window === 'undefined') return fallback
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback
}

const render = () => {
  if (!chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value)
  const axis = cssVar('--chart-axis', '#6b7c93')
  const edge = 'rgba(148, 163, 184, 0.5)'
  chart.setOption({
    tooltip: {
      backgroundColor: 'rgba(15, 23, 42, 0.92)',
      borderWidth: 0,
      textStyle: { color: '#f8fafc' },
    },
    series: [
      {
        type: 'graph',
        layout: 'force',
        roam: true,
        draggable: true,
        edgeSymbol: ['none', 'arrow'],
        edgeSymbolSize: 8,
        force: {
          repulsion: 300,
          edgeLength: 110,
        },
        label: {
          show: true,
          color: axis,
          fontSize: 13,
          distance: 8,
        },
        lineStyle: {
          color: edge,
          width: 2.2,
          curveness: 0.18,
          opacity: 0.9,
        },
        data: props.nodes.map((item) => ({
          id: item.id,
          name: item.label,
          value: item.type,
          symbolSize: item.type === 'member' ? 56 : 44,
          itemStyle: {
            color: cssVar(colorMap[item.type] || '--primary', '#4f46e5'),
            borderColor: '#ffffff',
            borderWidth: 2,
            shadowBlur: 14,
            shadowColor: 'rgba(15, 23, 42, 0.12)',
          },
        })),
        links: props.edges.map((item) => ({
          source: item.source,
          target: item.target,
          label: { show: Boolean(item.label), formatter: item.label },
        })),
      },
    ],
  })
}

onMounted(() => {
  render()
  window.addEventListener('resize', render)
})

watch(() => [props.nodes, props.edges], render, { deep: true })

onBeforeUnmount(() => {
  window.removeEventListener('resize', render)
  chart?.dispose()
})
</script>

<style scoped>
.graph-canvas {
  width: 100%;
  height: clamp(320px, 60vh, 640px);
  border: 1px solid rgba(219, 231, 243, 0.9);
  border-radius: 18px;
  background: var(--chart-bg);
}
</style>

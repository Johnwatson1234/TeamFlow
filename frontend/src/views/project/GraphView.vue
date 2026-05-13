<template>
  <div class="graph-page">
    <div class="page-header">
      <div><h1 class="page-title">Git Graph 协作图谱</h1><p class="page-subtitle">{{ nodes.length }} 个协作事件节点</p></div>
      <el-button @click="fetchGraph" :loading="loading"><el-icon><Refresh /></el-icon> 刷新</el-button>
    </div>
    <div class="graph-container">
      <div class="graph-legend">
        <div v-for="l in legends" :key="l.type" class="legend-item">
          <div class="legend-dot" :style="{ background: l.color }"></div>
          <span>{{ l.label }}</span>
        </div>
      </div>
      <div ref="graphEl" class="graph-canvas"></div>
      <!-- Node detail panel -->
      <div v-if="selectedNode" class="node-detail">
        <div class="detail-header">
          <h3>{{ selectedNode.event_type }}</h3>
          <el-button text @click="selectedNode = null"><el-icon><Close /></el-icon></el-button>
        </div>
        <div class="detail-content">
          <div class="detail-row"><span class="label">摘要</span><span>{{ selectedNode.summary }}</span></div>
          <div class="detail-row"><span class="label">操作人</span><span>{{ selectedNode.actor?.nickname }}</span></div>
          <div class="detail-row"><span class="label">目标类型</span><span>{{ selectedNode.target_type }}</span></div>
          <div class="detail-row"><span class="label">时间</span><span>{{ formatDate(selectedNode.created_at) }}</span></div>
          <div class="detail-row"><span class="label">贡献权重</span><span>{{ selectedNode.contribution_weight }}</span></div>
          <div class="detail-row"><span class="label">证据强度</span><span class="tag" :class="evidClass(selectedNode.evidence_level)">{{ selectedNode.evidence_level }}</span></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { collabApi } from '@/api'
import dayjs from 'dayjs'

const route = useRoute()
const projectId = computed(() => Number(route.params.id))
const loading = ref(false)
const graphEl = ref<HTMLElement>()
const nodes = ref<any[]>([])
const edges = ref<any[]>([])
const selectedNode = ref<any>(null)

const legends = [
  { type: 'TaskCreated', color: '#4F46E5', label: '任务创建' },
  { type: 'DocEdited', color: '#8B5CF6', label: '文档编辑' },
  { type: 'CodeCommitted', color: '#06B6D4', label: '代码提交' },
  { type: 'ReviewPassed', color: '#22C55E', label: '任务完成' },
  { type: 'RiskAlerted', color: '#EF4444', label: '风险预警' },
  { type: 'CommentAdded', color: '#F59E0B', label: '评论讨论' },
]

const nodeColors: Record<string, string> = {
  TaskCreated: '#4F46E5', TaskAssigned: '#6366F1', ProgressUpdated: '#818CF8',
  DocEdited: '#8B5CF6', CommentAdded: '#F59E0B', FileUploaded: '#06B6D4',
  CodeCommitted: '#0891B2', ReviewPassed: '#22C55E', RiskAlerted: '#EF4444', Merged: '#D97706',
}

function formatDate(dt: string) { return dayjs(dt).format('YYYY/MM/DD HH:mm') }
function evidClass(l: string) { return { high: 'tag-success', medium: 'tag-warning', low: 'tag-danger' }[l] || 'tag-info' }

async function fetchGraph() {
  loading.value = true
  try {
    const res: any = await collabApi.graph(projectId.value)
    nodes.value = res.nodes
    edges.value = res.edges
    await nextTick()
    renderGraph()
  } catch { ElMessage.error('加载图谱失败') } finally { loading.value = false }
}

function renderGraph() {
  if (!graphEl.value) return
  const canvas = graphEl.value
  canvas.innerHTML = ''

  if (!nodes.value.length) {
    canvas.innerHTML = '<div style="text-align:center;padding:80px;color:#94A3B8">暂无协作事件，开始任务后将自动生成图谱节点</div>'
    return
  }

  // Simple SVG-based graph visualization
  const W = canvas.clientWidth || 800
  const H = Math.max(400, nodes.value.length * 60)

  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg')
  svg.setAttribute('width', String(W))
  svg.setAttribute('height', String(H))
  svg.style.cursor = 'default'

  // Layout nodes in lanes by user
  const userLanes: Record<string, number> = {}
  let laneCount = 0
  const LANE_W = 140
  const PADDING = 60

  nodes.value.forEach(n => {
    const uid = n.actor?.id
    if (uid && !(uid in userLanes)) {
      userLanes[uid] = laneCount++
    }
  })

  const nodePos: Record<string, { x: number; y: number }> = {}
  const laneY: Record<number, number> = {}

  nodes.value.forEach(n => {
    const uid = n.actor?.id || 0
    const lane = userLanes[uid] || 0
    const x = PADDING + lane * LANE_W + LANE_W / 2
    const y = (laneY[lane] || PADDING) + 70
    laneY[lane] = y
    nodePos[n.id] = { x, y }
  })

  // Draw lane lines
  for (let i = 0; i < laneCount; i++) {
    const x = PADDING + i * LANE_W + LANE_W / 2
    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line')
    line.setAttribute('x1', String(x))
    line.setAttribute('y1', String(PADDING))
    line.setAttribute('x2', String(x))
    line.setAttribute('y2', String(H - 20))
    line.setAttribute('stroke', '#E2E8F0')
    line.setAttribute('stroke-width', '2')
    line.setAttribute('stroke-dasharray', '4,4')
    svg.appendChild(line)
  }

  // Draw edges
  edges.value.forEach(e => {
    const from = nodePos[e.source]
    const to = nodePos[e.target]
    if (!from || !to) return
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path')
    const cp = `M${from.x},${from.y} C${from.x},${(from.y + to.y) / 2} ${to.x},${(from.y + to.y) / 2} ${to.x},${to.y}`
    path.setAttribute('d', cp)
    path.setAttribute('stroke', '#CBD5E1')
    path.setAttribute('stroke-width', '1.5')
    path.setAttribute('fill', 'none')
    svg.appendChild(path)
  })

  // Draw nodes
  nodes.value.forEach(n => {
    const pos = nodePos[n.id]
    if (!pos) return
    const color = nodeColors[n.event_type] || '#64748B'

    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g')
    g.style.cursor = 'pointer'
    g.onclick = () => { selectedNode.value = n }

    // Circle
    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle')
    circle.setAttribute('cx', String(pos.x))
    circle.setAttribute('cy', String(pos.y))
    circle.setAttribute('r', '14')
    circle.setAttribute('fill', color)
    circle.setAttribute('stroke', 'white')
    circle.setAttribute('stroke-width', '2.5')

    // Label
    const text = document.createElementNS('http://www.w3.org/2000/svg', 'text')
    text.setAttribute('x', String(pos.x + 18))
    text.setAttribute('y', String(pos.y + 4))
    text.setAttribute('font-size', '11')
    text.setAttribute('fill', '#475569')
    text.textContent = (n.summary || '').substring(0, 20)

    g.appendChild(circle)
    g.appendChild(text)
    svg.appendChild(g)
  })

  canvas.appendChild(svg)
}

watch(projectId, fetchGraph)
onMounted(fetchGraph)
</script>

<style scoped>
.graph-page { padding: 28px 32px; }
.graph-container { display: flex; gap: 20px; position: relative; }
.graph-legend {
  display: flex; flex-direction: column; gap: 8px; padding: 16px;
  background: white; border: 1px solid var(--border); border-radius: var(--radius);
  height: fit-content; min-width: 140px; box-shadow: var(--shadow-sm);
}
.legend-item { display: flex; align-items: center; gap: 8px; font-size: 12px; }
.legend-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }

.graph-canvas {
  flex: 1; background: white; border: 1px solid var(--border); border-radius: var(--radius);
  min-height: 500px; overflow: auto; box-shadow: var(--shadow-sm);
}

.node-detail {
  width: 280px; background: white; border: 1px solid var(--border); border-radius: var(--radius);
  box-shadow: var(--shadow-lg); height: fit-content;
}
.detail-header { display: flex; align-items: center; justify-content: space-between; padding: 14px 16px; border-bottom: 1px solid var(--border); }
.detail-header h3 { font-size: 14px; font-weight: 600; }
.detail-content { padding: 14px 16px; }
.detail-row { display: flex; flex-direction: column; margin-bottom: 12px; }
.detail-row .label { font-size: 11px; color: var(--text-muted); margin-bottom: 3px; }
.detail-row span:not(.label) { font-size: 13px; }
</style>

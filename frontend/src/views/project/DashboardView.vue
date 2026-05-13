<template>
  <div class="dashboard-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">项目仪表盘</h1>
        <p class="page-subtitle" v-if="dash">{{ dash.project?.name }}</p>
      </div>
      <div class="header-actions">
        <el-button @click="scanRisks" :loading="scanning" id="btn-scan-risks">
          <el-icon><Warning /></el-icon> 扫描风险
        </el-button>
        <el-button type="primary" @click="recalculate" :loading="recalculating">
          <el-icon><Refresh /></el-icon> 刷新贡献分
        </el-button>
      </div>
    </div>

    <div v-if="loading" class="loading-wrap">
      <el-skeleton :rows="5" animated />
    </div>

    <template v-else-if="dash">
      <!-- Stat cards -->
      <div class="stats-grid">
        <div class="stat-card" v-for="stat in statCards" :key="stat.label">
          <div class="stat-icon" :style="{ background: stat.color + '20', color: stat.color }">
            <el-icon size="22"><component :is="stat.icon" /></el-icon>
          </div>
          <div class="stat-body">
            <div class="stat-value">{{ stat.value }}</div>
            <div class="stat-label">{{ stat.label }}</div>
          </div>
          <div class="stat-trend" v-if="stat.sub">{{ stat.sub }}</div>
        </div>
      </div>

      <!-- Main content area -->
      <div class="dashboard-grid">
        <!-- Left: ECG + recent events -->
        <div class="dashboard-left">
          <!-- Project ECG chart -->
          <div class="card">
            <div class="card-header">
              <span class="card-title">项目心电图 <span class="tag tag-ai">ECG</span></span>
            </div>
            <div ref="ecgChart" class="chart-container"></div>
          </div>

          <!-- Recent events timeline -->
          <div class="card mt-4">
            <div class="card-header">
              <span class="card-title">最新协作事件</span>
              <router-link :to="`/projects/${projectId}/graph`" class="view-all">查看全部 →</router-link>
            </div>
            <div class="events-list" v-if="dash.recent_events.length">
              <div v-for="ev in dash.recent_events.slice(0,8)" :key="ev.id" class="event-item">
                <div class="event-avatar" :style="{ background: avatarColor(ev.actor?.nickname) }">
                  {{ ev.actor?.nickname?.[0]?.toUpperCase() || '?' }}
                </div>
                <div class="event-body">
                  <div class="event-summary">{{ ev.summary }}</div>
                  <div class="event-meta">
                    <span class="event-actor">{{ ev.actor?.nickname }}</span>
                    <span class="event-time">{{ formatTime(ev.created_at) }}</span>
                  </div>
                </div>
                <span class="event-type-badge" :class="eventClass(ev.event_type)">{{ eventLabel(ev.event_type) }}</span>
              </div>
            </div>
            <div v-else class="empty-hint">暂无协作事件</div>
          </div>
        </div>

        <!-- Right: risks + members -->
        <div class="dashboard-right">
          <!-- Risk alerts -->
          <div class="card">
            <div class="card-header">
              <span class="card-title">风险预警</span>
              <router-link :to="`/projects/${projectId}/risk`" class="view-all">详情 →</router-link>
            </div>
            <div v-if="dash.risk_alerts.length" class="risk-list">
              <div v-for="r in dash.risk_alerts" :key="r.id" class="risk-item" :class="r.risk_level">
                <el-icon :color="riskColor(r.risk_level)"><Warning /></el-icon>
                <div class="risk-body">
                  <div class="risk-reason">{{ r.reason }}</div>
                  <div class="risk-suggest">{{ r.suggestion }}</div>
                </div>
                <span class="risk-level-badge" :class="r.risk_level">{{ r.risk_level === 'high' ? '高' : r.risk_level === 'medium' ? '中' : '低' }}</span>
              </div>
            </div>
            <div v-else class="empty-hint" style="color:#22C55E">
              <el-icon><CircleCheck /></el-icon> 暂无风险预警，项目健康！
            </div>
          </div>

          <!-- Member contributions -->
          <div class="card mt-4">
            <div class="card-header">
              <span class="card-title">成员贡献排名</span>
              <router-link :to="`/projects/${projectId}/contribution`" class="view-all">详情 →</router-link>
            </div>
            <div class="member-list">
              <div v-for="(m, i) in dash.member_contributions" :key="m.user_id" class="member-contrib">
                <div class="member-rank" :class="`rank-${Number(i) + 1}`">{{ Number(i) + 1 }}</div>
                <div class="avatar avatar-sm" :style="{ background: avatarColor(m.nickname) }">
                  {{ m.nickname?.[0]?.toUpperCase() }}
                </div>
                <div class="member-info">
                  <div class="member-name">{{ m.nickname }}</div>
                  <div class="member-role">{{ m.role }}</div>
                </div>
                <div class="member-score">
                  <div class="score-value">{{ m.total_score.toFixed(0) }}</div>
                  <div class="score-bar">
                    <div class="score-fill" :style="{ width: m.total_score + '%', background: avatarColor(m.nickname) }"></div>
                  </div>
                </div>
              </div>
              <div v-if="!dash.member_contributions.length" class="empty-hint">暂无贡献数据，点击刷新</div>
            </div>
          </div>

          <!-- Radar chart -->
          <div class="card mt-4">
            <div class="card-header">
              <span class="card-title">项目健康雷达</span>
            </div>
            <div ref="radarChart" class="chart-container-sm"></div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { projectApi, collabApi } from '@/api'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'
dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const route = useRoute()
const projectId = computed(() => Number(route.params.id))
const loading = ref(false)
const scanning = ref(false)
const recalculating = ref(false)
const dash = ref<any>(null)
const ecgChart = ref<HTMLElement>()
const radarChart = ref<HTMLElement>()
let ecgInstance: any = null
let radarInstance: any = null

const statCards = computed(() => {
  if (!dash.value) return []
  return [
    { label: '任务完成率', value: dash.value.completion_rate + '%', icon: 'CircleCheck', color: '#22C55E', sub: `${dash.value.completed_tasks}/${dash.value.total_tasks}` },
    { label: '进行中任务', value: dash.value.in_progress_tasks, icon: 'Loading', color: '#4F46E5' },
    { label: '延期任务', value: dash.value.overdue_tasks, icon: 'Clock', color: '#EF4444' },
    { label: '项目成员', value: dash.value.member_count, icon: 'User', color: '#06B6D4' },
    { label: '协作文档', value: dash.value.doc_count, icon: 'Document', color: '#8B5CF6' },
    { label: '协作事件', value: dash.value.event_count, icon: 'Share', color: '#F59E0B' },
  ]
})

function avatarColor(name?: string) {
  const colors = ['#4F46E5', '#7C3AED', '#0891B2', '#059669', '#D97706', '#DC2626']
  if (!name) return colors[0]
  return colors[name.charCodeAt(0) % colors.length]
}

function formatTime(dt: string) { return dayjs(dt).fromNow() }

function eventLabel(t: string) {
  const map: Record<string, string> = {
    TaskCreated: '创建', TaskAssigned: '分配', ProgressUpdated: '更新', DocEdited: '文档',
    CommentAdded: '评论', FileUploaded: '文件', CodeCommitted: '代码', ReviewPassed: '完成',
    RiskAlerted: '风险', Merged: '合并',
  }
  return map[t] || t
}

function eventClass(t: string) {
  const map: Record<string, string> = {
    TaskCreated: 'tag-primary', TaskAssigned: 'tag-info', ProgressUpdated: 'tag-info',
    DocEdited: 'tag-ai', CommentAdded: 'tag-info', FileUploaded: 'tag-info',
    CodeCommitted: 'tag-primary', ReviewPassed: 'tag-success', RiskAlerted: 'tag-danger', Merged: 'tag-success',
  }
  return map[t] || 'tag-info'
}

function riskColor(level: string) {
  return level === 'high' ? '#EF4444' : level === 'medium' ? '#F59E0B' : '#22C55E'
}

async function fetchDashboard() {
  loading.value = true
  try {
    const res: any = await projectApi.dashboard(projectId.value)
    dash.value = res
    await nextTick()
    initCharts()
  } catch {
    ElMessage.error('加载仪表盘失败')
  } finally {
    loading.value = false
  }
}

function initCharts() {
  if (ecgChart.value) {
    ecgInstance = echarts.init(ecgChart.value)
    // Generate ECG-like data from events
    const events = dash.value?.recent_events || []
    const now = Date.now()
    const data = Array.from({length: 30}, (_, i) => {
      const day = new Date(now - (29 - i) * 86400000)
      const cnt = events.filter((e: any) => {
        const d = new Date(e.created_at)
        return d.toDateString() === day.toDateString()
      }).length
      return [day.toISOString().split('T')[0], cnt]
    })
    ecgInstance.setOption({
      grid: { top: 10, right: 10, bottom: 30, left: 40 },
      xAxis: { type: 'category', data: data.map(d => d[0].slice(5)), axisLabel: { fontSize: 10 } },
      yAxis: { type: 'value', minInterval: 1, axisLabel: { fontSize: 10 } },
      series: [{
        type: 'line', data: data.map(d => d[1]),
        smooth: true, symbol: 'none',
        lineStyle: { color: '#4F46E5', width: 2 },
        areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(79,70,229,0.3)' }, { offset: 1, color: 'rgba(79,70,229,0)' }] } }
      }],
      tooltip: { trigger: 'axis' }
    })
  }
  if (radarChart.value) {
    radarInstance = echarts.init(radarChart.value)
    const d = dash.value
    const total = d?.total_tasks || 1
    radarInstance.setOption({
      radar: {
        indicator: [
          { name: '进度', max: 100 }, { name: '活跃度', max: 100 },
          { name: '文档', max: 100 }, { name: '沟通', max: 100 },
          { name: '代码', max: 100 }, { name: '无风险', max: 100 }
        ],
        shape: 'polygon', splitNumber: 4,
        axisName: { color: '#64748B', fontSize: 11 }
      },
      series: [{
        type: 'radar',
        data: [{
          value: [
            d?.completion_rate || 0,
            Math.min(d?.event_count * 5, 100) || 0,
            Math.min(d?.doc_count * 10, 100) || 0,
            Math.min(d?.message_count * 2, 100) || 0,
            50, // code placeholder
            Math.max(100 - (d?.risk_alerts?.length || 0) * 20, 0)
          ],
          areaStyle: { color: 'rgba(79,70,229,0.2)' },
          lineStyle: { color: '#4F46E5' },
          itemStyle: { color: '#4F46E5' }
        }]
      }]
    })
  }
}

async function scanRisks() {
  scanning.value = true
  try {
    await collabApi.scanRisks(projectId.value)
    ElMessage.success('风险扫描完成')
    fetchDashboard()
  } catch { ElMessage.error('扫描失败') } finally { scanning.value = false }
}

async function recalculate() {
  recalculating.value = true
  try {
    await collabApi.recalculate(projectId.value)
    ElMessage.success('贡献分已更新')
    fetchDashboard()
  } catch { ElMessage.error('更新失败') } finally { recalculating.value = false }
}

watch(projectId, fetchDashboard)
onMounted(fetchDashboard)
</script>

<style scoped>
.dashboard-page { padding: 28px 32px; }
.page-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 24px; }
.header-actions { display: flex; gap: 10px; }
.loading-wrap { padding: 20px; }

.stats-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 14px;
  margin-bottom: 24px;
}
@media (max-width: 1400px) { .stats-grid { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 900px) { .stats-grid { grid-template-columns: repeat(2, 1fr); } }

.stat-card {
  background: white; border: 1px solid var(--border); border-radius: var(--radius);
  padding: 16px; display: flex; align-items: center; gap: 12px;
  box-shadow: var(--shadow-sm); transition: transform 0.2s;
}
.stat-card:hover { transform: translateY(-2px); }

.stat-icon { width: 44px; height: 44px; border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.stat-value { font-size: 22px; font-weight: 800; color: var(--text); line-height: 1; }
.stat-label { font-size: 12px; color: var(--text-muted); margin-top: 2px; }
.stat-trend { font-size: 11px; color: var(--text-light); margin-left: auto; }

.dashboard-grid { display: grid; grid-template-columns: 1fr 360px; gap: 20px; }
@media (max-width: 1100px) { .dashboard-grid { grid-template-columns: 1fr; } }

.card { background: white; border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; box-shadow: var(--shadow-sm); }
.card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.card-title { font-size: 14px; font-weight: 600; display: flex; align-items: center; gap: 8px; }
.view-all { font-size: 12px; color: var(--primary); text-decoration: none; }
.view-all:hover { text-decoration: underline; }

.chart-container { height: 160px; }
.chart-container-sm { height: 200px; }

.events-list { display: flex; flex-direction: column; gap: 10px; }
.event-item { display: flex; align-items: flex-start; gap: 10px; padding: 8px 0; border-bottom: 1px solid var(--border); }
.event-item:last-child { border-bottom: none; }
.event-avatar { width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; color: white; flex-shrink: 0; margin-top: 2px; }
.event-body { flex: 1; min-width: 0; }
.event-summary { font-size: 13px; color: var(--text); line-height: 1.4; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.event-meta { display: flex; gap: 8px; margin-top: 3px; }
.event-actor { font-size: 11px; color: var(--text-muted); }
.event-time { font-size: 11px; color: var(--text-light); }
.event-type-badge { font-size: 10px; padding: 2px 6px; border-radius: 8px; flex-shrink: 0; }
.empty-hint { text-align: center; color: var(--text-muted); font-size: 13px; padding: 20px 0; display: flex; align-items: center; justify-content: center; gap: 6px; }

.risk-list { display: flex; flex-direction: column; gap: 8px; }
.risk-item { display: flex; align-items: flex-start; gap: 10px; padding: 10px 12px; border-radius: var(--radius-sm); background: var(--bg); border-left: 3px solid; }
.risk-item.high { border-left-color: #EF4444; background: #FEF2F2; }
.risk-item.medium { border-left-color: #F59E0B; background: #FFFBEB; }
.risk-item.low { border-left-color: #22C55E; background: #F0FDF4; }
.risk-body { flex: 1; }
.risk-reason { font-size: 12.5px; font-weight: 500; color: var(--text); }
.risk-suggest { font-size: 11.5px; color: var(--text-muted); margin-top: 2px; }
.risk-level-badge { font-size: 10px; padding: 2px 7px; border-radius: 8px; font-weight: 600; flex-shrink: 0; }
.risk-level-badge.high { background: #FEE2E2; color: #DC2626; }
.risk-level-badge.medium { background: #FEF3C7; color: #D97706; }
.risk-level-badge.low { background: #DCFCE7; color: #16A34A; }

.member-list { display: flex; flex-direction: column; gap: 8px; }
.member-contrib { display: flex; align-items: center; gap: 8px; }
.member-rank { width: 20px; font-size: 12px; font-weight: 800; color: var(--text-light); flex-shrink: 0; }
.member-rank.rank-1 { color: #F59E0B; }
.member-rank.rank-2 { color: #94A3B8; }
.member-rank.rank-3 { color: #B45309; }
.member-info { flex: 1; min-width: 0; }
.member-name { font-size: 13px; font-weight: 600; }
.member-role { font-size: 11px; color: var(--text-muted); }
.member-score { text-align: right; flex-shrink: 0; }
.score-value { font-size: 13px; font-weight: 700; color: var(--primary); }
.score-bar { width: 60px; height: 4px; background: var(--border); border-radius: 2px; margin-top: 3px; }
.score-fill { height: 100%; border-radius: 2px; transition: width 0.5s; }
</style>

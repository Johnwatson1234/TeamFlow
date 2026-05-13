<template>
  <div class="risk-page">
    <div class="page-header">
      <div><h1 class="page-title">风险雷达</h1><p class="page-subtitle">{{ openAlerts.length }} 个待处理风险</p></div>
      <el-button type="primary" @click="scanRisks" :loading="scanning"><el-icon><Warning /></el-icon> 扫描风险</el-button>
    </div>
    <div class="risk-layout">
      <div class="risk-left">
        <!-- Radar chart -->
        <div class="card">
          <div class="card-title">项目健康雷达</div>
          <div ref="radarEl" class="radar-chart"></div>
        </div>
      </div>
      <div class="risk-right">
        <div v-if="loading"><el-skeleton :rows="4" animated /></div>
        <template v-else>
          <div v-if="!openAlerts.length" class="all-clear">
            <div class="clear-icon">✅</div>
            <h3>项目状态良好</h3>
            <p>暂无风险预警，继续保持！</p>
          </div>
          <div v-else class="alerts-list">
            <div v-for="a in openAlerts" :key="a.id" class="alert-card" :class="a.risk_level">
              <div class="alert-header">
                <div class="alert-icon">{{ riskIcon(a.risk_type) }}</div>
                <div class="alert-info">
                  <div class="alert-type">{{ riskTypeLabel(a.risk_type) }}</div>
                  <div class="alert-reason">{{ a.reason }}</div>
                </div>
                <div class="alert-level" :class="a.risk_level">
                  {{ a.risk_level === 'high' ? '高' : a.risk_level === 'medium' ? '中' : '低' }}
                </div>
              </div>
              <div class="alert-suggest">💡 {{ a.suggestion }}</div>
              <div class="alert-actions">
                <el-button size="small" type="success" @click="resolve(a.id)">标记已解决</el-button>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { collabApi } from '@/api'
import * as echarts from 'echarts'

const route = useRoute()
const projectId = computed(() => Number(route.params.id))
const loading = ref(false)
const scanning = ref(false)
const alerts = ref<any[]>([])
const radarEl = ref<HTMLElement>()
const openAlerts = computed(() => alerts.value.filter(a => a.status !== 'resolved'))

function riskIcon(t: string) {
  return { deadline: '⏰', blocked: '🚫', low_active: '😴', conflict: '⚠️', sprint: '🏃' }[t] || '⚠️'
}
function riskTypeLabel(t: string) {
  return { deadline: '截止日期风险', blocked: '任务阻塞风险', low_active: '低活跃风险', conflict: '代码冲突风险', sprint: '突击提交风险' }[t] || t
}

async function fetchAlerts() {
  loading.value = true
  try {
    alerts.value = (await collabApi.riskAlerts(projectId.value) as any[])
    await nextTick()
    initRadar()
  } finally { loading.value = false }
}

async function scanRisks() {
  scanning.value = true
  try {
    await collabApi.scanRisks(projectId.value)
    ElMessage.success('风险扫描完成')
    fetchAlerts()
  } catch { ElMessage.error('扫描失败') } finally { scanning.value = false }
}

async function resolve(id: number) {
  try {
    await collabApi.resolveAlert(id)
    const a = alerts.value.find(a => a.id === id)
    if (a) a.status = 'resolved'
    ElMessage.success('已标记为解决')
  } catch { ElMessage.error('操作失败') }
}

function initRadar() {
  if (!radarEl.value) return
  const ins = echarts.init(radarEl.value)
  const high = alerts.value.filter(a => a.risk_level === 'high').length
  const med = alerts.value.filter(a => a.risk_level === 'medium').length
  ins.setOption({
    radar: {
      indicator: [
        { name: '截止风险', max: 5 }, { name: '阻塞风险', max: 5 },
        { name: '活跃度', max: 5 }, { name: '代码冲突', max: 5 },
        { name: '突击风险', max: 5 }, { name: '评审积压', max: 5 }
      ],
      axisName: { color: '#64748B', fontSize: 11 }
    },
    series: [{
      type: 'radar',
      data: [{ value: [high, med, 3, 2, 1, 2], name: '当前风险',
        areaStyle: { color: 'rgba(239,68,68,0.2)' }, lineStyle: { color: '#EF4444' }, itemStyle: { color: '#EF4444' } }]
    }]
  })
}

watch(projectId, fetchAlerts)
onMounted(fetchAlerts)
</script>

<style scoped>
.risk-page { padding: 28px 32px; }
.risk-layout { display: grid; grid-template-columns: 320px 1fr; gap: 20px; }
.card { background: white; border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; box-shadow: var(--shadow-sm); }
.card-title { font-size: 14px; font-weight: 600; margin-bottom: 12px; }
.radar-chart { height: 280px; }
.all-clear { text-align: center; padding: 60px 20px; }
.clear-icon { font-size: 48px; margin-bottom: 12px; }
.all-clear h3 { font-size: 18px; font-weight: 700; color: #22C55E; }
.all-clear p { color: var(--text-muted); margin-top: 6px; }
.alerts-list { display: flex; flex-direction: column; gap: 12px; }
.alert-card { background: white; border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; box-shadow: var(--shadow-sm); border-left: 4px solid; }
.alert-card.high { border-left-color: #EF4444; }
.alert-card.medium { border-left-color: #F59E0B; }
.alert-card.low { border-left-color: #22C55E; }
.alert-header { display: flex; align-items: flex-start; gap: 12px; margin-bottom: 10px; }
.alert-icon { font-size: 24px; flex-shrink: 0; }
.alert-info { flex: 1; }
.alert-type { font-size: 13px; font-weight: 600; }
.alert-reason { font-size: 12px; color: var(--text-muted); margin-top: 2px; }
.alert-level { padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 700; flex-shrink: 0; }
.alert-level.high { background: #FEE2E2; color: #DC2626; }
.alert-level.medium { background: #FEF3C7; color: #D97706; }
.alert-level.low { background: #DCFCE7; color: #16A34A; }
.alert-suggest { font-size: 12.5px; color: var(--text); background: var(--bg); padding: 8px 10px; border-radius: var(--radius-sm); margin-bottom: 10px; }
.alert-actions { display: flex; justify-content: flex-end; }
</style>

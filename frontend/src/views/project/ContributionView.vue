<template>
  <div class="contribution-page">
    <div class="page-header">
      <div><h1 class="page-title">贡献审计</h1><p class="page-subtitle">基于多维度证据链的公平评分</p></div>
      <el-button type="primary" @click="recalculate" :loading="recalculating"><el-icon><Refresh /></el-icon> 重新计算</el-button>
    </div>

    <div v-if="loading"><el-skeleton :rows="4" animated /></div>

    <template v-else>
      <!-- Radar chart for each member -->
      <div class="members-grid">
        <div v-for="m in members" :key="m.user_id" class="member-card">
          <div class="member-header">
            <div class="avatar" :style="{ background: avatarColor(m.nickname) }">{{ m.nickname?.[0]?.toUpperCase() }}</div>
            <div>
              <div class="member-name">{{ m.nickname }}</div>
              <div class="member-role">{{ m.role }}</div>
            </div>
            <div class="total-score" :style="{ color: scoreColor(m.total_score) }">{{ m.total_score.toFixed(0) }}<small>分</small></div>
          </div>
          <div class="score-breakdown">
            <div v-for="dim in dims(m)" :key="dim.label" class="dim-row">
              <span class="dim-label">{{ dim.label }}</span>
              <div class="dim-bar"><div class="dim-fill" :style="{ width: dim.value + '%', background: dim.color }"></div></div>
              <span class="dim-val">{{ dim.value.toFixed(0) }}</span>
            </div>
          </div>
          <div class="member-stats">
            <div class="stat"><span class="stat-num">{{ m.completed_tasks }}</span><span class="stat-lbl">完成任务</span></div>
            <div class="stat"><span class="stat-num">{{ m.event_count }}</span><span class="stat-lbl">协作事件</span></div>
          </div>
          <div v-if="m.evidences.length" class="evidences">
            <div class="evid-title">最近证据</div>
            <div v-for="e in m.evidences.slice(0,3)" :key="e.created_at" class="evid-item">
              <span class="tag tag-primary">{{ e.evidence_type }}</span>
              <span class="evid-desc">{{ e.description }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Heatmap placeholder -->
      <div class="card mt-4">
        <div class="card-header"><span class="card-title">贡献热力图 <span class="tag tag-ai">Coming Soon</span></span></div>
        <div ref="heatmapEl" class="heatmap-container"></div>
      </div>
    </template>
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
const recalculating = ref(false)
const members = ref<any[]>([])
const heatmapEl = ref<HTMLElement>()

function avatarColor(name?: string) {
  const colors = ['#4F46E5','#7C3AED','#0891B2','#059669','#D97706','#DC2626']
  if (!name) return colors[0]
  return colors[name.charCodeAt(0) % colors.length]
}

function scoreColor(s: number) {
  if (s >= 70) return '#22C55E'
  if (s >= 50) return '#F59E0B'
  return '#EF4444'
}

function dims(m: any) {
  return [
    { label: '任务完成', value: m.task_score, color: '#4F46E5' },
    { label: '文档贡献', value: m.document_score, color: '#8B5CF6' },
    { label: '代码质量', value: m.code_score, color: '#06B6D4' },
    { label: '响应协作', value: m.response_score, color: '#F59E0B' },
    { label: '过程稳定', value: m.stability_score, color: '#22C55E' },
  ]
}

async function fetchContribution() {
  loading.value = true
  try { members.value = (await collabApi.contribution(projectId.value) as any[]) }
  catch { ElMessage.error('加载贡献数据失败') } finally { loading.value = false }
}

async function recalculate() {
  recalculating.value = true
  try {
    await collabApi.recalculate(projectId.value)
    ElMessage.success('贡献分已重新计算')
    fetchContribution()
  } catch { ElMessage.error('计算失败') } finally { recalculating.value = false }
}

watch(projectId, fetchContribution)
onMounted(fetchContribution)
</script>

<style scoped>
.contribution-page { padding: 28px 32px; }
.members-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }
.member-card { background: white; border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; box-shadow: var(--shadow-sm); }
.member-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.member-name { font-size: 15px; font-weight: 700; }
.member-role { font-size: 11px; color: var(--text-muted); }
.total-score { margin-left: auto; font-size: 28px; font-weight: 800; line-height: 1; }
.total-score small { font-size: 12px; font-weight: 400; color: var(--text-muted); }

.score-breakdown { display: flex; flex-direction: column; gap: 8px; margin-bottom: 14px; }
.dim-row { display: flex; align-items: center; gap: 8px; }
.dim-label { font-size: 11px; color: var(--text-muted); min-width: 56px; }
.dim-bar { flex: 1; height: 6px; background: var(--border); border-radius: 3px; overflow: hidden; }
.dim-fill { height: 100%; border-radius: 3px; transition: width 0.5s; }
.dim-val { font-size: 11px; font-weight: 600; min-width: 24px; text-align: right; }

.member-stats { display: flex; gap: 16px; border-top: 1px solid var(--border); padding-top: 12px; margin-bottom: 12px; }
.stat { display: flex; flex-direction: column; align-items: center; }
.stat-num { font-size: 20px; font-weight: 800; color: var(--primary); }
.stat-lbl { font-size: 11px; color: var(--text-muted); }

.evidences { border-top: 1px solid var(--border); padding-top: 10px; }
.evid-title { font-size: 11px; color: var(--text-muted); margin-bottom: 6px; }
.evid-item { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
.evid-desc { font-size: 11px; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.card { background: white; border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; box-shadow: var(--shadow-sm); }
.card-header { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; font-size: 14px; font-weight: 600; }
.heatmap-container { height: 120px; display: flex; align-items: center; justify-content: center; color: var(--text-muted); font-size: 14px; }
</style>

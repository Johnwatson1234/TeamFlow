<template>
  <div class="ai-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">🤖 AI 项目经理</h1>
        <p class="page-subtitle">智能任务拆解、排期建议与周报生成</p>
      </div>
    </div>

    <div class="ai-layout">
      <!-- Input panel -->
      <div class="card ai-input-card">
        <h3 class="section-title">项目信息输入</h3>
        <el-form :model="form" label-position="top">
          <el-form-item label="项目名称">
            <el-input v-model="form.project_name" id="ai-project-name" />
          </el-form-item>
          <el-form-item label="截止日期">
            <el-date-picker v-model="form.deadline" type="date" style="width:100%" />
          </el-form-item>
          <el-form-item label="技术栈">
            <el-input v-model="form.tech_stack" placeholder="Vue 3 + FastAPI + MySQL" />
          </el-form-item>
          <el-form-item label="成员角色">
            <div v-for="(m, i) in form.members" :key="i" class="member-row">
              <el-input v-model="form.members[i]" :placeholder="`成员 ${i+1} 角色`" />
              <el-button text @click="form.members.splice(i,1)"><el-icon><Delete /></el-icon></el-button>
            </div>
            <el-button text @click="form.members.push('')">+ 添加成员</el-button>
          </el-form-item>
        </el-form>
        <el-button type="primary" :loading="generating" @click="generate" id="btn-ai-generate" style="width:100%">
          <el-icon><MagicStick /></el-icon> AI 生成计划
        </el-button>
        <el-button style="width:100%; margin-top:8px" :loading="reportGenerating" @click="generateReport">
          📄 生成项目周报
        </el-button>
      </div>

      <!-- Output panel -->
      <div class="ai-output">
        <div v-if="!result && !generating" class="ai-placeholder">
          <div style="font-size:64px">🤖</div>
          <h3>AI 项目经理就绪</h3>
          <p>输入项目信息后，AI 将自动生成任务树、里程碑和风险建议</p>
        </div>

        <div v-if="generating" class="ai-thinking">
          <el-icon class="thinking-icon"><Loading /></el-icon>
          <span>AI 正在分析项目，生成计划...</span>
        </div>

        <template v-if="result">
          <!-- Milestones -->
          <div class="card mb-4">
            <h3 class="section-title">📍 项目里程碑</h3>
            <div class="milestones">
                <div v-for="(ms, i) in result.milestones" :key="i" class="milestone-item">
                <div class="ms-index">M{{ Number(i) + 1 }}</div>
                <div class="ms-name">{{ ms.name }}</div>
                <div class="ms-date">{{ ms.dueDate }}</div>
              </div>
            </div>
          </div>

          <!-- Tasks -->
          <div class="card mb-4">
            <h3 class="section-title">📋 任务列表</h3>
            <div class="ai-tasks">
              <div v-for="(t, i) in result.tasks" :key="i" class="ai-task">
                <div class="ai-task-header">
                  <span class="task-num">{{ Number(i) + 1 }}</span>
                  <span class="ai-task-title">{{ t.title }}</span>
                  <span class="tag" :class="prioClass(t.priority)">{{ t.priority }}</span>
                  <span class="tag tag-info">{{ t.assigneeRole }}</span>
                </div>
                <div v-if="t.subtasks?.length" class="subtasks">
                  <span v-for="s in t.subtasks" :key="s" class="subtask">• {{ s }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Risks -->
          <div class="card mb-4">
            <h3 class="section-title">⚠️ 风险提示</h3>
            <div v-for="(r, i) in result.risks" :key="i" class="risk-hint">
              <el-icon color="#F59E0B"><Warning /></el-icon>
              {{ r }}
            </div>
          </div>

          <!-- Actions -->
          <el-button type="primary" size="large" @click="confirmPlan" :loading="confirming" :disabled="!result.suggestion_id" id="btn-confirm-plan">
            ✅ 确认并写入任务
          </el-button>
        </template>

        <!-- Weekly report -->
        <div v-if="weeklyReport" class="card mt-4">
          <h3 class="section-title">📊 项目周报</h3>
          <pre class="report-content">{{ weeklyReport }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { aiApi } from '@/api'
import dayjs from 'dayjs'

const route = useRoute()
const projectId = computed(() => Number(route.params.id))
const generating = ref(false)
const confirming = ref(false)
const reportGenerating = ref(false)
const result = ref<any>(null)
const weeklyReport = ref('')

const form = reactive({
  project_name: '',
  deadline: '',
  tech_stack: '',
  members: ['前端开发', '后端开发', '数据库设计', '文档负责人'],
})

function prioClass(p: string) { return { high: 'tag-danger', medium: 'tag-warning', low: 'tag-success' }[p] || 'tag-info' }

async function generate() {
  if (!form.project_name) return ElMessage.warning('请输入项目名称')
  generating.value = true
  result.value = null
  try {
    const deadline = form.deadline ? dayjs(form.deadline as any).format('YYYY-MM-DD') : '待确定'
    const res: any = await aiApi.planning(projectId.value, {
      project_name: form.project_name,
      deadline,
      tech_stack: form.tech_stack,
      members: form.members.filter(Boolean),
    })
    result.value = res
    ElMessage.success('AI 计划生成成功！')
  } catch { ElMessage.error('生成失败，使用模板结果') } finally { generating.value = false }
}

async function confirmPlan() {
  if (!result.value?.suggestion_id) return
  confirming.value = true
  try {
    await aiApi.confirmPlanning(result.value.suggestion_id)
    ElMessage.success('任务已写入项目！')
  } catch { ElMessage.error('写入失败') } finally { confirming.value = false }
}

async function generateReport() {
  reportGenerating.value = true
  try {
    const res: any = await aiApi.weeklyReport(projectId.value)
    weeklyReport.value = res.content
    ElMessage.success('周报生成成功！')
  } catch { ElMessage.error('生成失败') } finally { reportGenerating.value = false }
}
</script>

<style scoped>
.ai-page { padding: 28px 32px; }
.ai-layout { display: grid; grid-template-columns: 320px 1fr; gap: 20px; }
.card { background: white; border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; box-shadow: var(--shadow-sm); }
.section-title { font-size: 15px; font-weight: 700; margin-bottom: 14px; }
.member-row { display: flex; gap: 6px; margin-bottom: 8px; }
.ai-placeholder { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 80px 40px; background: white; border: 1px solid var(--border); border-radius: var(--radius); text-align: center; }
.ai-placeholder h3 { font-size: 18px; font-weight: 700; margin: 12px 0 6px; }
.ai-placeholder p { color: var(--text-muted); }
.ai-thinking { display: flex; align-items: center; gap: 12px; padding: 24px; background: white; border: 1px solid var(--primary); border-radius: var(--radius); color: var(--primary); font-weight: 500; }
.thinking-icon { animation: spin 1s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

.milestones { display: flex; flex-direction: column; gap: 8px; }
.milestone-item { display: flex; align-items: center; gap: 12px; padding: 10px 14px; background: var(--bg); border-radius: var(--radius-sm); }
.ms-index { width: 28px; height: 28px; border-radius: 50%; background: var(--primary); color: white; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; flex-shrink: 0; }
.ms-name { flex: 1; font-weight: 600; font-size: 13px; }
.ms-date { font-size: 12px; color: var(--text-muted); }

.ai-tasks { display: flex; flex-direction: column; gap: 10px; }
.ai-task { padding: 12px 14px; background: var(--bg); border-radius: var(--radius-sm); border-left: 3px solid var(--primary); }
.ai-task-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.task-num { width: 22px; height: 22px; border-radius: 50%; background: var(--primary); color: white; font-size: 11px; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.ai-task-title { flex: 1; font-weight: 600; font-size: 13px; }
.subtasks { display: flex; flex-wrap: wrap; gap: 6px; }
.subtask { font-size: 11px; color: var(--text-muted); }

.risk-hint { display: flex; align-items: flex-start; gap: 8px; padding: 10px 0; border-bottom: 1px solid var(--border); font-size: 13px; color: var(--text); }
.risk-hint:last-child { border-bottom: none; }

.report-content { font-size: 13px; line-height: 1.8; white-space: pre-wrap; color: var(--text); font-family: 'Inter', sans-serif; }
.mb-4 { margin-bottom: 16px; }
.mt-4 { margin-top: 16px; }
</style>

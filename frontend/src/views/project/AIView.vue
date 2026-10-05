<template>
  <div class="ai-page">
    <section class="ai-main">
      <div class="teamflow-card hero-card">
        <div>
          <div class="hero-kicker">Mimo 实时分析工作台</div>
          <h1 class="page-title">AI 助手</h1>
          <div class="page-desc">
            这里的规划、周报、对话和操作都直接由 `mimo-v2.5-pro` 结合当前项目数据实时生成，不再使用本地拼装结果。
          </div>
        </div>
        <div class="hero-actions">
          <el-button :loading="planningLoading" type="primary" @click="generatePlan">生成任务规划</el-button>
          <el-button :loading="reportLoading" @click="generateWeeklyReport">生成周报</el-button>
        </div>
      </div>

      <div class="ai-skills-row">
        <div class="skill-card pink" @click="chatPrompt = '帮我做代码审查'; sendChat()">
          <div class="skill-icon">🧐</div>
          <div class="skill-title">代码审查</div>
          <div class="skill-desc">自动扫描近期提交</div>
        </div>
        <div class="skill-card purple" @click="chatPrompt = '帮我进行需求拆解'; sendChat()">
          <div class="skill-icon">📋</div>
          <div class="skill-title">需求拆解</div>
          <div class="skill-desc">一键将文档转为任务</div>
        </div>
        <div class="skill-card cyan" @click="chatPrompt = '帮我分析项目进度风险'; sendChat()">
          <div class="skill-icon">⚡</div>
          <div class="skill-title">风险诊断</div>
          <div class="skill-desc">识别阻塞点与瓶颈</div>
        </div>
        <div class="skill-card indigo" @click="generateWeeklyReport">
          <div class="skill-icon">📝</div>
          <div class="skill-title">智能周报</div>
          <div class="skill-desc">基于数据生成简报</div>
        </div>
      </div>

      <div class="ai-chat-grid">
        <div class="teamflow-card chat-panel">
          <div class="panel-head">
            <div>
              <div class="section-title">实时对话</div>
              <div class="tiny-muted">AI 会自动携带当前页面和项目上下文</div>
            </div>
            <span class="status-tag teal">SSE</span>
          </div>

          <div ref="messageScroller" class="chat-list app-scroll">
            <div v-for="message in chatMessages" :key="message.localId" :class="['chat-bubble', message.role]">
              <div class="bubble-head">
                <strong>{{ message.role === 'user' ? '你' : 'TeamFlow AI' }}</strong>
                <span class="tiny-muted">{{ message.time }}</span>
              </div>
              <div class="bubble-copy">{{ message.content }}</div>
              <div v-if="message.actions?.length" class="chip-row">
                <span v-for="(item, index) in message.actions" :key="`${message.localId}-${index}`" class="action-chip">
                  {{ actionLabel(item.type) }}
                </span>
              </div>
            </div>
            <div v-if="chatStreaming" class="chat-bubble assistant streaming">
              <div class="bubble-head">
                <strong>TeamFlow AI</strong>
                <span class="tiny-muted">{{ streamStatus || '正在生成' }}</span>
              </div>
              <div class="bubble-copy">{{ streamedReply || '正在分析项目上下文…' }}</div>
            </div>
          </div>

          <div class="ai-composer-wrapper">
            <el-input
              v-model="chatPrompt"
              :rows="3"
              :autosize="{ minRows: 3, maxRows: 8 }"
              type="textarea"
              placeholder="告诉 Mimo 你需要做什么，例如：帮我分析当前的风险点..."
              @keyup.enter.ctrl="sendChat"
            />
            <div class="composer-bar">
              <div class="tiny-muted">Ctrl + Enter 发送，AI 可读取当前上下文</div>
              <el-button :loading="chatStreaming" type="primary" round @click="sendChat">发送</el-button>
            </div>
          </div>
        </div>

        <aside class="teamflow-card context-panel">
          <div class="panel-head">
            <div class="section-title">当前项目上下文</div>
            <span class="status-tag blue">实时</span>
          </div>
          <div class="context-grid">
            <div class="context-card">
              <label>项目名称</label>
              <strong>{{ projectStore.currentProject?.name || '当前项目' }}</strong>
            </div>
            <div class="context-card">
              <label>截止日期</label>
              <strong>{{ projectStore.currentProject?.due_date || '未设置' }}</strong>
            </div>
            <div class="context-card">
              <label>当前路由</label>
              <strong>{{ route.path }}</strong>
            </div>
            <div class="context-card">
              <label>页面上下文</label>
              <strong>{{ contextSummary }}</strong>
            </div>
          </div>

          <div class="side-section">
            <div class="section-title">快捷请求</div>
            <div class="quick-grid">
              <button v-for="item in quickPrompts" :key="item.label" type="button" class="quick-card" @click="chatPrompt = item.prompt">
                {{ item.label }}
              </button>
            </div>
          </div>

          <div v-if="actionResults.length" class="side-section">
            <div class="section-title">最近自动操作</div>
            <div class="result-list">
              <div v-for="(item, index) in actionResults" :key="`${item.type}-${index}`" class="result-row">
                <div>
                  <strong>{{ actionLabel(item.type) }}</strong>
                  <div class="tiny-muted">{{ item.result?.message || '已执行' }}</div>
                </div>
                <span :class="['status-tag', item.status === 'ok' ? 'green' : 'red']">
                  {{ item.status === 'ok' ? '成功' : '失败' }}
                </span>
              </div>
            </div>
          </div>
        </aside>
      </div>

      <div v-if="planResult || weeklyReport" class="result-grid">
        <div v-if="planResult" class="teamflow-card result-panel">
          <div class="panel-head">
            <div class="section-title">AI 任务规划</div>
            <el-button v-if="suggestionId" @click="confirmPlan">确认写入项目</el-button>
          </div>
          <div class="result-summary">{{ planResult.summary }}</div>
          <div class="phase-track">
            <div v-for="phase in planResult.phases || []" :key="`${phase.step}-${phase.title}`" class="phase-card">
              <div class="phase-step">{{ phase.step }}</div>
              <strong>{{ phase.title }}</strong>
              <span class="tiny-muted">{{ phase.date }}</span>
            </div>
          </div>
          <el-table :data="planResult.tasks || []">
            <el-table-column label="任务" prop="name" min-width="180" />
            <el-table-column label="负责人" prop="owner" width="120" />
            <el-table-column label="优先级" prop="priority" width="110" />
            <el-table-column label="截止时间" prop="deadline" width="140" />
          </el-table>
        </div>

        <div v-if="weeklyReport" class="teamflow-card result-panel">
          <div class="panel-head">
            <div class="section-title">AI 周报</div>
            <span class="status-tag teal">实时生成</span>
          </div>
          <div class="report-copy">{{ weeklyReport }}</div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { aiApi, streamAiChat } from '@/api'
import { useAiStore } from '@/stores/ai'
import { useProjectStore } from '@/stores/project'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const aiStore = useAiStore()
const projectStore = useProjectStore()
const userStore = useUserStore()

const chatPrompt = ref('请结合当前项目上下文，总结最值得优先推进的工作，并在合适时直接帮我整理任务。')
const chatStreaming = ref(false)
const streamStatus = ref('')
const streamedReply = ref('')
const messageScroller = ref<HTMLElement | null>(null)
const chatMessages = ref<Array<{ localId: string; role: 'user' | 'assistant'; content: string; time: string; actions?: any[] }>>([])
const actionResults = ref<any[]>([])
const planningLoading = ref(false)
const reportLoading = ref(false)
const suggestionId = ref<number | null>(null)
const planResult = ref<any>(null)
const weeklyReport = ref('')

const quickPrompts = [
  { label: '总结项目现状', prompt: '请总结当前项目状态、关键风险和最需要推进的事项。' },
  { label: '自动拆任务', prompt: '请根据当前项目真实数据生成一版任务规划，并在必要时给出可执行建议。' },
  { label: '推进任务状态', prompt: '如果当前任务列表中有明显滞后的事项，请直接提出并执行合理的非破坏性更新。' },
  { label: '生成周报', prompt: '请结合当前项目数据生成周报，并写入系统留痕。' },
]

const contextSummary = computed(() => {
  const entries = Object.entries(aiStore.pageContext || {}).filter(([, value]) => value !== '' && value !== null && value !== undefined)
  return entries.length ? entries.slice(0, 3).map(([key, value]) => `${key}:${String(value)}`).join(' / ') : 'AI 工作台'
})

const actionLabel = (type: string) => ({
  navigate_page: '页面导航',
  open_task: '打开任务',
  open_document: '打开文档',
  open_file: '打开文件',
  create_task: '创建任务',
  update_task: '更新任务',
  accept_task: '开始任务',
  block_task: '阻塞任务',
  complete_task: '完成任务',
  create_milestone: '创建里程碑',
  generate_weekly_report: '生成周报',
  scan_risks: '风险扫描',
  recalculate_contribution: '重算贡献分析',
}[type] || type)

const scrollToBottom = () => {
  nextTick(() => {
    setTimeout(() => {
      if (messageScroller.value) {
        messageScroller.value.scrollTo({
          top: messageScroller.value.scrollHeight,
          behavior: 'smooth'
        })
      }
    }, 50)
  })
}

const loadConversation = async () => {
  const { data } = await aiApi.conversation(route.params.id as string)
  chatMessages.value = (data.messages || []).map((item: any) => ({
    localId: `server-${item.id}`,
    role: item.sender?.name === 'TeamFlow AI' || item.message_type === 'ai' || item.message_type === 'ai_action' ? 'assistant' : 'user',
    content: item.content,
    time: item.created_at?.slice(11, 16) || '--:--',
    actions: item.metadata?.actions || (item.message_type === 'ai_action' ? [item.metadata] : []),
  }))
  scrollToBottom()
}

const applyUiAction = async (item: any) => {
  const params = item.params || {}
  if (item.type === 'navigate_page' && (params.path || item.result?.path)) {
    await router.push(params.path || item.result.path)
  } else if (item.type === 'open_task' && params.task_id) {
    await router.push(`/projects/${route.params.id}/tasks?taskId=${params.task_id}`)
  } else if (item.type === 'open_document' && params.document_id) {
    await router.push(`/projects/${route.params.id}/documents/${params.document_id}`)
  } else if (item.type === 'open_file' && params.file_id) {
    await router.push(`/projects/${route.params.id}/files?fileId=${params.file_id}`)
  }
}

const sendChat = async () => {
  if (!chatPrompt.value.trim() || chatStreaming.value) return
  const userPrompt = chatPrompt.value.trim()
  chatPrompt.value = ''
  chatMessages.value.push({
    localId: `user-${Date.now()}`,
    role: 'user',
    content: userPrompt,
    time: new Date().toLocaleTimeString().slice(0, 5),
  })
  chatStreaming.value = true
  streamStatus.value = ''
  streamedReply.value = ''
  actionResults.value = []
  scrollToBottom()

  try {
    await streamAiChat(
      route.params.id as string,
      {
        prompt: userPrompt,
        route_name: String(route.name || ''),
        route_path: route.path,
        route_params: route.params,
        query: route.query,
        page_context: {
          ...aiStore.pageContext,
          currentUserId: userStore.user?.id,
        },
        auto_execute: true,
      },
      {
        onStatus(payload) {
          streamStatus.value = payload.message
        },
        onChunk(payload) {
          streamedReply.value += payload.content || ''
          scrollToBottom()
        },
        onAction(payload) {
          actionResults.value = [...actionResults.value, payload]
        },
        async onDone(payload) {
          chatMessages.value.push({
            localId: `assistant-${Date.now()}`,
            role: 'assistant',
            content: payload.reply || streamedReply.value,
            time: new Date().toLocaleTimeString().slice(0, 5),
            actions: payload.actions || [],
          })
          window.dispatchEvent(new CustomEvent('teamflow-ai-refresh', { detail: payload.action_results || [] }))
          for (const item of payload.action_results || []) {
            if (item.status === 'ok' && ['navigate_page', 'open_task', 'open_document', 'open_file'].includes(item.type)) {
              await applyUiAction(item)
            }
          }
          chatStreaming.value = false
          streamedReply.value = ''
          streamStatus.value = ''
          await loadConversation()
        },
        onError(payload) {
          chatStreaming.value = false
          streamedReply.value = ''
          streamStatus.value = ''
          ElMessage.error(payload.message || 'AI 处理失败')
        },
      },
    )
  } catch (error: any) {
    chatStreaming.value = false
    streamedReply.value = ''
    streamStatus.value = ''
    ElMessage.error(error?.message || 'AI 对话失败')
  }
}

const generatePlan = async () => {
  planningLoading.value = true
  try {
    const { data } = await aiApi.planning({
      project_id: Number(route.params.id),
      project_name: projectStore.currentProject?.name || '当前项目',
      user_prompt: chatPrompt.value.trim() || '请结合当前项目数据生成一版可执行任务规划。',
    })
    suggestionId.value = data.id
    planResult.value = data.result
    ElMessage.success('AI 任务规划已生成')
  } finally {
    planningLoading.value = false
  }
}

const confirmPlan = async () => {
  if (!suggestionId.value) return
  await aiApi.confirm(suggestionId.value)
  ElMessage.success('AI 规划已写入项目')
  window.dispatchEvent(new CustomEvent('teamflow-ai-refresh', { detail: [{ type: 'create_task', status: 'ok' }] }))
}

const generateWeeklyReport = async () => {
  reportLoading.value = true
  try {
    const { data } = await aiApi.weeklyReport(route.params.id as string)
    weeklyReport.value = data.content
    ElMessage.success('AI 周报已生成')
  } finally {
    reportLoading.value = false
  }
}

onMounted(async () => {
  aiStore.mergePageContext({ workspace: 'ai-workbench' })
  await loadConversation()
})
</script>

<style scoped>
.ai-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.ai-main {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.hero-card,
.chat-panel,
.context-panel,
.result-panel {
  padding: 20px;
}

.hero-card {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  background:
    radial-gradient(circle at top right, rgba(29, 78, 216, 0.14), transparent 26%),
    radial-gradient(circle at bottom left, rgba(13, 148, 136, 0.1), transparent 20%),
    linear-gradient(180deg, #fbfdff 0%, #eff8f7 100%);
}

.hero-kicker {
  margin-bottom: 10px;
  color: var(--ai-cobalt);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.hero-actions,
.panel-head,
.composer-bar,
.bubble-head,
.result-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.ai-chat-grid,
.result-grid {
  display: grid;
  gap: 18px;
  grid-template-columns: 1.45fr 0.95fr;
}

.chat-panel,
.context-panel {
  display: flex;
  min-height: 0;
  flex-direction: column;
  gap: 14px;
}

.ai-skills-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-top: -4px;
}

.skill-card {
  padding: 18px 20px;
  border-radius: 16px;
  cursor: pointer;
  color: white;
  transition: transform 0.2s, box-shadow 0.2s;
  display: flex;
  flex-direction: column;
}

.skill-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 25px rgba(0,0,0,0.1);
}

.skill-icon {
  font-size: 26px;
  margin-bottom: 10px;
}

.skill-title {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 4px;
}

.skill-desc {
  font-size: 13px;
  opacity: 0.9;
}

.skill-card.pink { background: linear-gradient(135deg, #F472B6 0%, #DB2777 100%); }
.skill-card.purple { background: linear-gradient(135deg, #A78BFA 0%, #7C3AED 100%); }
.skill-card.cyan { background: linear-gradient(135deg, #22D3EE 0%, #0891B2 100%); }
.skill-card.indigo { background: linear-gradient(135deg, #818CF8 0%, #4F46E5 100%); }

.chat-list {
  display: flex;
  min-height: 420px;
  max-height: 620px;
  flex-direction: column;
  gap: 20px;
  overflow: auto;
  padding: 20px;
  background: #F8FAFC;
  border-radius: 16px;
  margin-bottom: 16px;
  scroll-behavior: smooth;
}

.chat-bubble {
  display: flex;
  flex-direction: column;
  max-width: 80%;
  padding: 16px 20px;
  border-radius: 20px;
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04);
}

.chat-bubble.user {
  align-self: flex-end;
  background: linear-gradient(135deg, var(--primary-light) 0%, var(--primary) 100%);
  color: #FFFFFF;
  border-bottom-right-radius: 4px;
}

.chat-bubble.assistant {
  align-self: flex-start;
  background: #FFFFFF;
  border: 1px solid rgba(15, 23, 42, 0.06);
  border-bottom-left-radius: 4px;
}

.chat-bubble.streaming {
  border: 1px dashed rgba(99, 102, 241, 0.4);
}

.bubble-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  font-size: 13px;
  opacity: 0.9;
}

.bubble-copy,
.result-summary,
.report-copy {
  line-height: 1.75;
  white-space: pre-wrap;
}

.ai-composer-wrapper {
  background: #fff;
  border-radius: 20px;
  padding: 16px 18px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.06);
  border: 1px solid rgba(15,23,42,0.05);
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ai-composer-wrapper:focus-within {
  box-shadow: 0 8px 30px rgba(99, 102, 241, 0.12);
  border-color: rgba(99, 102, 241, 0.3);
}

.ai-composer-wrapper :deep(.el-textarea__inner) {
  border: none !important;
  box-shadow: none !important;
  padding: 0;
  resize: none;
  font-size: 15px;
  background: transparent;
  color: var(--text);
}

.context-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.context-card {
  padding: 14px;
  border: 1px solid rgba(29, 78, 216, 0.12);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.86);
}

.context-card label {
  display: block;
  margin-bottom: 6px;
  color: var(--text-muted);
  font-size: 12px;
}

.side-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.quick-grid {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.quick-card {
  padding: 12px 14px;
  border: 1px solid rgba(29, 78, 216, 0.12);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.92);
  color: var(--ai-ink);
  cursor: pointer;
  font: inherit;
  font-weight: 700;
  text-align: left;
}

.result-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.result-row {
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid rgba(15, 23, 42, 0.06);
}

.result-row:last-child {
  border-bottom: 0;
}

.phase-track {
  display: grid;
  gap: 12px;
  margin: 18px 0;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
}

.phase-card {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 14px;
  border: 1px solid rgba(29, 78, 216, 0.12);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.88);
}

.phase-step {
  color: var(--ai-cobalt);
  font-size: 12px;
  font-weight: 800;
}

.chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.action-chip {
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(13, 148, 136, 0.12);
  color: #0f766e;
  font-size: 12px;
  font-weight: 700;
}

@media (max-width: 1200px) {
  .ai-chat-grid,
  .result-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .hero-card,
  .hero-actions,
  .panel-head,
  .composer-bar {
    align-items: flex-start;
    flex-direction: column;
  }

  .context-grid,
  .quick-grid {
    grid-template-columns: 1fr;
  }

  .chat-bubble.user,
  .chat-bubble.assistant {
    margin: 0;
  }
}
</style>

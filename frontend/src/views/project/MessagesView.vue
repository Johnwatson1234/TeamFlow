<template>
  <div class="messages-page teamflow-card" v-loading="loading">

    <aside class="conversation-pane">
      <div class="pane-head" style="margin-bottom: 12px;">
        <div class="section-title">会话列表</div>
        <el-button class="new-conversation-btn" type="primary" @click="createDialog = true">新建会话</el-button>
      </div>
      <div style="margin-bottom: 16px;">
        <el-input v-model="searchQuery" placeholder="搜索会话..." clearable>
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
      <div class="conversation-list app-scroll">
        <button
          v-for="item in filteredConversations"
          :key="item.id"
          type="button"
          :class="['conversation-item', { active: currentConversation?.id === item.id }]"
          @click="selectConversation(item)"
        >
          <div :class="['conversation-icon', item.conversation_type || 'group']">
            {{ item.conversation_type === 'ai_assistant' ? 'AI' : item.conversation_type === 'task' ? '#' : '群' }}
          </div>
          <div class="conversation-copy">
            <strong>{{ item.name }}</strong>
            <div class="tiny-muted">{{ item.latest_message?.content || '暂无消息' }}</div>
          </div>
        </button>
      </div>
    </aside>

    <section class="thread-pane" v-if="currentConversation">
      <div class="thread-head">
        <div>
          <div class="thread-title">{{ currentConversation.name }}</div>
          <div class="page-desc">
            <span v-if="currentConversation.conversation_type === 'ai_assistant'">这里会直接调用 Mimo 实时生成回复与动作结果</span>
            <span v-else-if="thread.task_context">关联任务：#{{ thread.task_context.id }} {{ thread.task_context.title }}</span>
          </div>
        </div>
        <div class="thread-actions">
          <el-button plain @click="router.push(`/projects/${projectId}/ai`)">AI 分析</el-button>
          <el-button v-if="thread.task_context" type="primary" plain @click="openTask(thread.task_context.id)">查看任务</el-button>
        </div>
      </div>

      <div ref="messageScroller" class="thread-messages app-scroll">
        <div v-for="message in thread.messages" :key="message.id" class="message-row" :class="{ mine: message.sender?.id === userStore.user?.id }">
          <img :src="message.sender?.avatar" alt="avatar" />
          <div class="message-body">
            <div class="message-meta">
              <strong>{{ message.sender?.name }}</strong>
              <span class="tiny-muted">{{ message.created_at?.slice(11, 16) }}</span>
            </div>

            <div v-if="message.message_type === 'code'" class="code-block">{{ message.content }}</div>
            <div v-else-if="message.message_type === 'task'" class="task-card" @click="openReferencedTask(message)">
              <strong>{{ message.metadata?.task_title || message.content }}</strong>
              <div class="tiny-muted">点击打开任务详情</div>
            </div>
            <div v-else-if="message.message_type === 'file_analysis'" class="analysis-card">
              <div class="analysis-head">
                <span class="status-tag teal">AI 文件分析</span>
                <strong>{{ message.metadata?.file_name || '未命名资源' }}</strong>
              </div>
              <div class="analysis-grid">
                <div><label>规模</label><span>{{ message.metadata?.scale || '--' }}</span></div>
                <div><label>等级</label><span>{{ message.metadata?.grade || '--' }}</span></div>
                <div><label>工作量</label><span>{{ message.metadata?.workload || '--' }}</span></div>
              </div>
              <div class="analysis-copy">{{ message.content }}</div>
              <div v-if="message.metadata?.risks?.length" class="analysis-list">
                <strong>风险点</strong>
                <div v-for="item in message.metadata.risks" :key="item" class="tiny-muted">{{ item }}</div>
              </div>
              <div v-if="message.metadata?.suggestions?.length" class="analysis-list">
                <strong>建议动作</strong>
                <div v-for="item in message.metadata.suggestions" :key="item" class="tiny-muted">{{ item }}</div>
              </div>
            </div>
            <div v-else-if="message.message_type === 'ai_action'" class="action-result-card">
              <strong>{{ message.content || 'AI 已执行动作' }}</strong>
              <div class="tiny-muted">{{ message.metadata?.type || 'ai_action' }}</div>
            </div>
            <div v-else class="text-bubble">{{ message.content }}</div>
          </div>
        </div>

        <div v-if="streaming" class="message-row">
          <img src="https://api.dicebear.com/7.x/bottts/svg?seed=teamflow-ai&backgroundColor=0f172a,1d4ed8,0f766e" alt="avatar" />
          <div class="message-body">
            <div class="message-meta">
              <strong>TeamFlow AI</strong>
              <span class="tiny-muted">{{ streamStatus || '实时生成中' }}</span>
            </div>
            <div class="text-bubble">{{ streamedReply || '正在分析当前页面与会话上下文…' }}</div>
          </div>
        </div>
      </div>

      <div class="composer-panel">
        <div class="composer-tabs">
          <button
            v-for="item in editorModes"
            :key="item.key"
            type="button"
            :class="['composer-tab', { active: editorMode === item.key }]"
            @click="editorMode = item.key"
          >
            {{ item.label }}
          </button>
          <el-upload
            class="composer-upload"
            action="#"
            :auto-upload="false"
            :show-file-list="false"
            accept=".txt,.md,.pdf,.ppt,.pptx"
            :on-change="handleFileUpload"
          >
            <button type="button" class="composer-tab upload-tab">
              <el-icon><Paperclip /></el-icon> 上传文件
            </button>
          </el-upload>
        </div>

        <div v-if="editorMode === 'task'" class="helper-row">
          <el-select v-model="taskReferenceId" filterable placeholder="选择任务">
            <el-option v-for="task in taskOptions" :key="task.id" :label="`#${task.id} ${task.title}`" :value="task.id" />
          </el-select>
          <el-button plain @click="insertTaskReference">插入任务引用</el-button>
        </div>

        <div v-if="editorMode === 'code'" class="helper-row">
          <el-select v-model="codeLanguage" placeholder="代码语言">
            <el-option label="TypeScript" value="TypeScript" />
            <el-option label="Python" value="Python" />
            <el-option label="SQL" value="SQL" />
            <el-option label="Java" value="Java" />
          </el-select>
          <el-button plain @click="insertCodeTemplate">插入代码模板</el-button>
        </div>

        <div v-if="editorMode === 'file'" class="helper-row">
          <el-select v-model="selectedAnalysisSource" filterable placeholder="选择要分析的文档或文件">
            <el-option
              v-for="item in analysisSources"
              :key="item.key"
              :label="item.label"
              :value="item.key"
            />
          </el-select>
          <el-button type="primary" plain :loading="analysisLoading" @click="analyzeFile">启动 AI 分析</el-button>
        </div>

        <el-input
          v-model="messageForm.content"
          :rows="4"
          type="textarea"
          :placeholder="composerPlaceholder"
          @keydown.enter.exact.prevent="sendMessage"
        />
        <div class="composer-actions">
          <div class="tiny-muted">{{ helperText }}</div>
          <el-button :loading="streaming" type="primary" @click="sendMessage">发送</el-button>
        </div>
      </div>
    </section>

    <aside class="context-pane" v-if="thread.task_context">
      <div class="section-title">任务上下文</div>
      <div class="context-card">
        <strong>#{{ thread.task_context.id }} {{ thread.task_context.title }}</strong>
        <div class="context-grid">
          <div><label>负责人</label><span>{{ thread.task_context.assignee?.name || '待分配' }}</span></div>
          <div><label>优先级</label><span>{{ thread.task_context.priority }}</span></div>
          <div><label>截止日期</label><span>{{ thread.task_context.due_date }}</span></div>
          <div><label>进度</label><span>{{ thread.task_context.progress }}%</span></div>
        </div>
      </div>
      <div class="activity-list">
        <div v-for="item in activities" :key="item.id" class="activity-item">
          <img :src="item.actor?.avatar" alt="avatar" />
          <div>
            <div>{{ item.content }}</div>
            <div class="tiny-muted">{{ item.created_at }}</div>
          </div>
        </div>
      </div>
    </aside>

    <el-dialog v-model="createDialog" title="新建会话" width="min(520px, 92vw)">
      <el-form :model="conversationForm" label-position="top">
        <el-form-item label="会话名称"><el-input v-model="conversationForm.name" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialog = false">取消</el-button>
        <el-button type="primary" @click="createConversation">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { Paperclip, Search } from '@element-plus/icons-vue'
import { computed, nextTick, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { aiApi, conversationApi, documentApi, fileApi, streamAiChat, taskApi } from '@/api'
import { useAiStore } from '@/stores/ai'
import { useUserStore } from '@/stores/user'

type EditorMode = 'text' | 'code' | 'task' | 'file'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const aiStore = useAiStore()

const projectId = computed(() => route.params.id as string)
const loading = ref(false)
const analysisLoading = ref(false)
const searchQuery = ref('')
const conversations = ref<any[]>([])

const filteredConversations = computed(() => {
  if (!searchQuery.value) return conversations.value
  const q = searchQuery.value.toLowerCase()
  return conversations.value.filter(item => item.name.toLowerCase().includes(q))
})

const currentConversation = ref<any>(null)
const thread = reactive<any>({ messages: [], task_context: null })
const activities = ref<any[]>([])
const taskOptions = ref<any[]>([])
const fileOptions = ref<any[]>([])
const documentOptions = ref<any[]>([])
const createDialog = ref(false)
const conversationForm = reactive({ name: '' })
const messageForm = reactive({ content: '' })
const editorMode = ref<EditorMode>('text')
const taskReferenceId = ref<number | null>(null)
const codeLanguage = ref('TypeScript')
const selectedAnalysisSource = ref('')
const streaming = ref(false)
const streamStatus = ref('')
const streamedReply = ref('')
const messageScroller = ref<HTMLElement | null>(null)

const editorModes: Array<{ key: EditorMode; label: string }> = [
  { key: 'text', label: '文字' },
  { key: 'code', label: '代码' },
  { key: 'task', label: '任务引用' },
  { key: 'file', label: 'AI 文件分析' },
]

const analysisSources = computed(() => [
  ...documentOptions.value.map((item) => ({ key: `document:${item.id}`, label: `文档 · ${item.title}` })),
  ...fileOptions.value.map((item) => ({ key: `file:${item.id}`, label: `文件 · ${item.name}` })),
])

const composerPlaceholder = computed(() => {
  if (currentConversation.value?.conversation_type === 'ai_assistant') {
    return '直接和 AI 对话，它会结合当前页面上下文回复并自动执行允许的操作'
  }
  if (editorMode.value === 'code') return '输入代码片段，Enter 发送，Shift + Enter 换行'
  if (editorMode.value === 'task') return '可补充任务说明或备注'
  if (editorMode.value === 'file') return '可补充本次文件分析的关注点，例如：质量、风险、工作量'
  return '输入消息内容'
})

const helperText = computed(() => {
  if (currentConversation.value?.conversation_type === 'ai_assistant') {
    return 'AI 助手会读取当前路由、当前会话和页面上下文'
  }
  if (editorMode.value === 'file') return selectedAnalysisSource.value ? '将调用后端真实文件/文档分析接口' : '先选择要分析的文档或文件'
  if (editorMode.value === 'task') return taskReferenceId.value ? '将以任务引用消息发送' : '先选择一个任务'
  if (editorMode.value === 'code') return `将以 ${codeLanguage.value} 代码消息发送`
  return '普通项目会话消息'
})

const syncPageContext = () => {
  aiStore.mergePageContext({
    selectedConversationId: currentConversation.value?.id || null,
    selectedAnalysisSource: selectedAnalysisSource.value || '',
    editorMode: editorMode.value,
  })
}

const scrollToBottom = async () => {
  await nextTick()
  if (messageScroller.value) {
    messageScroller.value.scrollTop = messageScroller.value.scrollHeight
  }
}

const load = async () => {
  loading.value = true
  try {
    const [_, conversationRes, taskRes, docRes, fileRes] = await Promise.all([
      aiApi.conversation(projectId.value),
      conversationApi.list(projectId.value),
      taskApi.list(projectId.value),
      documentApi.list(projectId.value),
      fileApi.list(projectId.value),
    ])
    conversations.value = conversationRes.data
    taskOptions.value = taskRes.data
    documentOptions.value = docRes.data
    fileOptions.value = fileRes.data

    const preferredId = Number(route.query.conversationId || 0)
    const preferred = conversations.value.find((item) => item.id === preferredId) || currentConversation.value || conversations.value[0]
    if (preferred) {
      await selectConversation(preferred)
    }
  } finally {
    loading.value = false
  }
}

const selectConversation = async (item: any) => {
  currentConversation.value = item
  await conversationApi.read(item.id).catch(() => null)
  const { data } = await conversationApi.messages(item.id)
  Object.assign(thread, data)
  if (data.task_context) {
    const activityRes = await taskApi.activities(data.task_context.id)
    activities.value = activityRes.data
  } else {
    activities.value = []
  }
  syncPageContext()
  await scrollToBottom()
}

const createConversation = async () => {
  if (!conversationForm.name.trim()) {
    ElMessage.warning('请输入会话名称')
    return
  }
  await conversationApi.create(projectId.value, {
    name: conversationForm.name,
    conversation_type: 'project_group',
  })
  conversationForm.name = ''
  createDialog.value = false
  await load()
}

const insertTaskReference = () => {
  const task = taskOptions.value.find((item) => item.id === taskReferenceId.value)
  if (!task) {
    ElMessage.warning('请先选择任务')
    return
  }
  messageForm.content = `关联任务 #${task.id} ${task.title}`
}

const insertCodeTemplate = () => {
  messageForm.content = codeLanguage.value === 'TypeScript'
    ? 'const data = await api.getTaskDetail(taskId)\nconsole.log(data)'
    : codeLanguage.value === 'Python'
      ? 'def build_task_context(task_id: int):\n    return task_service.detail(task_id)\n'
      : codeLanguage.value === 'SQL'
        ? 'SELECT id, title, status\nFROM tasks\nWHERE project_id = ?;'
        : '@GetMapping("/task/detail")\npublic Result<TaskDetail> detail(){\n    return Result.success(taskService.detail());\n}'
}

const analyzeFile = async () => {
  if (!selectedAnalysisSource.value) {
    ElMessage.warning('请先选择文档或文件')
    return
  }
  analysisLoading.value = true
  try {
    const [kind, rawId] = selectedAnalysisSource.value.split(':')
    const payload: Record<string, unknown> = {
      conversation_id: currentConversation.value?.id,
      prompt: messageForm.content.trim(),
    }
    if (kind === 'document') payload.document_id = Number(rawId)
    if (kind === 'file') payload.file_id = Number(rawId)
    await aiApi.fileAnalysis(projectId.value, payload)
    messageForm.content = ''
    await selectConversation(currentConversation.value)
    ElMessage.success('AI 已完成实时文件分析')
  } finally {
    analysisLoading.value = false
  }
}

const sendAiConversationMessage = async () => {
  if (!messageForm.content.trim() || streaming.value) {
    ElMessage.warning('请输入消息内容')
    return
  }
  const userPrompt = messageForm.content.trim()
  messageForm.content = ''
  streaming.value = true
  streamStatus.value = ''
  streamedReply.value = ''
  thread.messages.push({
    id: Date.now(),
    message_type: 'text',
    content: userPrompt,
    created_at: new Date().toISOString(),
    sender: userStore.user,
  })
  await scrollToBottom()

  try {
    await streamAiChat(
      projectId.value,
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
        onDone(payload) {
          streaming.value = false
          streamedReply.value = ''
          streamStatus.value = ''
          window.dispatchEvent(new CustomEvent('teamflow-ai-refresh', { detail: payload.action_results || [] }))
          selectConversation(currentConversation.value)
        },
        onError(payload) {
          streaming.value = false
          streamedReply.value = ''
          streamStatus.value = ''
          ElMessage.error(payload.message || 'AI 对话失败')
        },
      },
    )
  } catch (error: any) {
    streaming.value = false
    streamedReply.value = ''
    streamStatus.value = ''
    ElMessage.error(error?.message || 'AI 对话失败')
  }
}

const sendMessage = async () => {
  if (!currentConversation.value) return
  if (currentConversation.value.conversation_type === 'ai_assistant') {
    await sendAiConversationMessage()
    return
  }
  if (editorMode.value === 'file') {
    await analyzeFile()
    return
  }

  let payload: Record<string, unknown> | null = null
  if (editorMode.value === 'task') {
    const task = taskOptions.value.find((item) => item.id === taskReferenceId.value)
    if (!task) {
      ElMessage.warning('请先选择任务')
      return
    }
    payload = {
      content: `关联任务 #${task.id} ${task.title}${messageForm.content.trim() ? `\n备注：${messageForm.content.trim()}` : ''}`,
      message_type: 'task',
      metadata: { task_id: task.id, task_title: task.title },
    }
  } else if (editorMode.value === 'code') {
    if (!messageForm.content.trim()) {
      ElMessage.warning('请输入代码内容')
      return
    }
    payload = {
      content: messageForm.content,
      message_type: 'code',
      code_language: codeLanguage.value,
    }
  } else {
    if (!messageForm.content.trim()) {
      ElMessage.warning('请输入消息内容')
      return
    }
    payload = {
      content: messageForm.content,
      message_type: 'text',
    }
  }

  await conversationApi.sendMessage(currentConversation.value.id, payload)
  messageForm.content = ''
  if (editorMode.value === 'task') {
    taskReferenceId.value = null
  }
  await selectConversation(currentConversation.value)
}

const handleFileUpload = (uploadFile: any) => {
  ElMessage.success(`已附加文件：${uploadFile.name} (支持在系统中预览)`)
  messageForm.content += `\n[文件: ${uploadFile.name}]`
}

const openTask = async (taskId: number) => {
  await router.push(`/projects/${projectId.value}/tasks?taskId=${taskId}`)
}

const openReferencedTask = async (message: any) => {
  const taskId = message.metadata?.task_id || thread.task_context?.id
  if (taskId) {
    await openTask(taskId)
  }
}

const handleAiRefresh = async () => {
  await load()
}

watch([currentConversation, selectedAnalysisSource, editorMode], syncPageContext)

onMounted(async () => {
  window.addEventListener('teamflow-ai-refresh', handleAiRefresh as EventListener)
  await load()
})

onUnmounted(() => {
  window.removeEventListener('teamflow-ai-refresh', handleAiRefresh as EventListener)
})
</script>

<style scoped>
.messages-page {
  display: flex;
  gap: 20px;
  height: calc(100dvh - 112px);
}

.conversation-pane {
  width: 320px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #F8FAFC 0%, #FFFFFF 100%);
  border-radius: 20px;
  border: 1px solid rgba(15, 23, 42, 0.06);
  box-shadow: 0 8px 32px rgba(15, 23, 42, 0.06);
  padding: 18px;
}

.thread-pane {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  background: #FFFFFF;
  border-radius: 20px;
  border: 1px solid rgba(15, 23, 42, 0.06);
  box-shadow: 0 12px 48px rgba(15, 23, 42, 0.08);
  position: relative;
}

.context-pane {
  width: 320px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: #FFFFFF;
  border-radius: 20px;
  border: 1px solid rgba(15, 23, 42, 0.06);
  box-shadow: 0 8px 32px rgba(15, 23, 42, 0.06);
  padding: 18px;
}

.thread-head,
.thread-messages {
  padding: 20px 24px;
}

.pane-head,
.thread-head,
.thread-actions,
.composer-actions,
.analysis-head,
.result-row,
.banner-actions,
.helper-row,
.message-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.conversation-list,
.thread-messages {
  display: flex;
  flex: 1;
  min-height: 0;
  flex-direction: column;
  gap: 12px;
  overflow: auto;
}

.conversation-item {
  display: grid;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border: 1px solid transparent;
  border-radius: 16px;
  background: transparent;
  cursor: pointer;
  grid-template-columns: 44px 1fr;
  text-align: left;
  transition: all 0.2s;
}

.conversation-item:hover {
  background: rgba(15, 23, 42, 0.04);
}

.conversation-item.active {
  background: linear-gradient(to right, #EEF2FF 0%, #FFFFFF 100%);
  border-color: rgba(99, 102, 241, 0.3);
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.12);
}

.conversation-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 16px;
  color: #fff;
  font-weight: 800;
  font-size: 18px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
  transition: transform 0.2s, box-shadow 0.2s;
}

.conversation-item:hover .conversation-icon {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
}

.conversation-icon.ai_assistant {
  background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
  text-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.conversation-icon.task {
  background: linear-gradient(135deg, #38BDF8 0%, #3B82F6 100%);
  font-size: 22px;
}

.conversation-icon.group,
.conversation-icon.project_group {
  background: linear-gradient(135deg, #34D399 0%, #10B981 100%);
}

.conversation-icon.system {
  background: linear-gradient(135deg, #FBBF24 0%, #D97706 100%);
}

.thread-title {
  font-size: 22px;
  font-weight: 800;
}

.thread-messages {
  margin-top: 16px;
}

.message-row {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.message-row.mine {
  flex-direction: row-reverse;
}

.message-row img,
.activity-item img {
  width: 40px;
  height: 40px;
  border-radius: 50%;
}

.message-body {
  max-width: 78%;
}

.message-meta {
  gap: 10px;
  justify-content: flex-start;
  margin-bottom: 8px;
}

.text-bubble,
.code-block,
.task-card,
.analysis-card,
.action-result-card {
  padding: 12px 16px;
  border-radius: 12px;
  background: #F8FAFC;
  border: 1px solid rgba(15, 23, 42, 0.04);
  box-shadow: 0 2px 12px rgba(15, 23, 42, 0.02);
  line-height: 1.6;
  white-space: pre-wrap;
  color: var(--text);
}

.message-row.mine .text-bubble,
.message-row.mine .task-card,
.message-row.mine .analysis-card,
.message-row.mine .action-result-card {
  background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%);
  border: none;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2);
  color: #fff;
}

.message-row.mine .text-bubble {
  border-top-right-radius: 4px;
}

.message-row:not(.mine) .text-bubble {
  border-top-left-radius: 4px;
}

.code-block {
  background: #0f172a;
  color: #dbeafe;
  font-family: Consolas, 'Courier New', monospace;
}

.task-card {
  cursor: pointer;
  background: linear-gradient(180deg, #eef5ff 0%, #f6fcfb 100%);
}

.analysis-card {
  background: linear-gradient(180deg, #f8fbff 0%, #ffffff 100%);
}

.analysis-grid,
.context-grid {
  display: grid;
  gap: 12px;
  margin: 12px 0;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.analysis-grid label,
.context-grid label {
  display: block;
  margin-bottom: 6px;
  color: var(--text-muted);
  font-size: 12px;
}

.analysis-copy {
  margin-top: 12px;
}

.analysis-list {
  margin-top: 12px;
}

.composer-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin: 16px 24px 24px;
  padding: 18px 20px;
  border-radius: 24px;
  border: 2px solid rgba(99, 102, 241, 0.15);
  background: #FFFFFF;
  box-shadow: 0 12px 40px rgba(99, 102, 241, 0.08);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.composer-panel:focus-within {
  border-color: #6366F1;
  box-shadow: 0 16px 48px rgba(99, 102, 241, 0.18);
  transform: translateY(-4px);
}

.composer-panel :deep(.el-textarea__inner) {
  border: none !important;
  box-shadow: none !important;
  padding: 0;
  resize: none;
  font-size: 15px;
  color: var(--text);
  background: transparent;
}

.composer-tabs {
  display: flex;
  gap: 18px;
  align-items: center;
}

.composer-tab {
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  font: inherit;
  font-weight: 600;
  transition: color 0.2s;
}

.composer-tab:hover {
  color: var(--text);
}

.composer-tab.active {
  color: var(--ai-cobalt);
}

.composer-upload {
  display: inline-flex;
}

.upload-tab {
  display: flex;
  align-items: center;
  gap: 4px;
}

.new-conversation-btn {
  background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%);
  border: none;
  border-radius: 8px;
  color: white;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.2);
  transition: all 0.2s ease;
}

.new-conversation-btn:hover {
  background: linear-gradient(135deg, #4F46E5 0%, #3730A3 100%);
  box-shadow: 0 6px 16px rgba(79, 70, 229, 0.3);
  color: white;
}

.helper-row {
  gap: 10px;
}

.helper-row :deep(.el-select) {
  flex: 1;
}

.context-card {
  padding: 16px;
  border: 1px solid rgba(15, 23, 42, 0.06);
  border-radius: 18px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 18px;
}

.activity-item {
  display: flex;
  gap: 10px;
}

@media (max-width: 1200px) {
  .context-pane {
    display: none;
  }
}

@media (max-width: 768px) {
  .messages-page {
    flex-direction: column;
    height: auto;
  }
  .conversation-pane, .thread-pane, .context-pane {
    width: 100%;
  }

  .ai-banner,
  .thread-head,
  .banner-actions,
  .composer-actions,
  .helper-row {
    align-items: flex-start;
    flex-direction: column;
  }

  .message-row,
  .message-row.mine {
    flex-direction: column;
  }

  .message-body {
    max-width: 100%;
  }

  .analysis-grid,
  .context-grid {
    grid-template-columns: 1fr;
  }
}
</style>

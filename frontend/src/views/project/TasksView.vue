<template>
  <div class="tasks-page" v-loading="loading">
    <div class="header-row">
      <div>
        <h1 class="page-title">任务管理</h1>
        <div class="page-desc">管理和跟踪项目任务，推进任务协同与交付</div>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="openCreate()">新建任务</el-button>
      </div>
    </div>

    <div class="filters teamflow-card">
      <el-select v-model="filters.assignee" placeholder="全部成员">
        <el-option label="全部成员" value="" />
        <el-option v-for="m in members" :key="m.user_id" :label="m.name" :value="m.name" />
      </el-select>
      <el-select v-model="filters.milestone" placeholder="全部里程碑">
        <el-option label="全部里程碑" value="" />
        <el-option v-for="m in milestones" :key="m.id" :label="m.name" :value="m.id" />
      </el-select>
      <el-select v-model="filters.priority" placeholder="全部优先级">
        <el-option label="全部优先级" value="" />
        <el-option label="高" value="高" />
        <el-option label="中" value="中" />
        <el-option label="低" value="低" />
      </el-select>
      <el-select v-model="filters.status" placeholder="全部状态">
        <el-option label="全部状态" value="" />
        <el-option v-for="c in columns" :key="c.key" :label="c.label" :value="c.key" />
      </el-select>
      <el-input v-model="filters.keyword" placeholder="搜索任务标题或关键词" />
    </div>

    <div class="kanban-layout">
      <div class="kanban-board">
        <div v-for="column in columns" :key="column.key" class="kanban-column teamflow-card">
          <div class="column-head">
            <span>{{ column.label }}</span>
            <b>{{ grouped[column.key]?.length || 0 }}</b>
          </div>
          <div class="column-list">
            <div v-for="task in grouped[column.key]" :key="task.id" class="task-card" @click="selectTask(task)">
              <div class="task-title">{{ task.title }}</div>
              <div class="task-owner">
                <img v-if="task.assignee" :src="task.assignee.avatar" alt="avatar" />
                <span>{{ task.assignee?.name || '待分配' }}</span>
                <span class="priority" :class="task.priority">{{ task.priority }}</span>
              </div>
              <el-progress :percentage="task.progress" :show-text="false" />
              <div class="task-foot">
                <span>{{ task.due_date }}</span>
                <span>{{ task.progress }}%</span>
              </div>
              <div v-if="task.blocker_reason" class="blocker">阻塞原因：{{ task.blocker_reason }}</div>
            </div>
          </div>
          <div class="action-link add-task" @click="openCreate(column.key)">+ 添加任务</div>
        </div>
      </div>

      </div>

      <el-drawer v-model="detailOpen" title="任务详情" size="min(480px, 100vw)">
        <div v-if="selectedTask" class="task-detail-content">
          <el-tabs v-model="detailTab">
            <el-tab-pane label="基本信息" name="info">
              <div class="detail-title">{{ selectedTask.title }}</div>
              <p class="page-desc">{{ selectedTask.description }}</p>
              <div class="detail-grid">
                <div><label>负责人</label><span>{{ selectedTask.assignee?.name || '待分配' }}</span></div>
                <div><label>优先级</label><span :class="['priority', selectedTask.priority]">{{ selectedTask.priority }}</span></div>
                <div><label>状态</label><span>{{ columns.find(c => c.key === selectedTask.status)?.label || selectedTask.status }}</span></div>
                <div><label>进度</label><span>{{ selectedTask.progress }}%</span></div>
                <div><label>开始日期</label><span>{{ selectedTask.start_date }}</span></div>
                <div><label>截止日期</label><span>{{ selectedTask.due_date }}</span></div>
              </div>
              <div class="related-box">
                <div><label>关联需求</label><a class="action-link" @click="openRelated('requirement')">{{ selectedTask.related_requirement }}</a></div>
                <div><label>关联文档</label><a class="action-link" @click="openRelated('document')">{{ selectedTask.related_document }}</a></div>
                <div><label>关联提交</label><a class="action-link" @click="openRelated('commit')">{{ selectedTask.related_commit }}</a></div>
              </div>
            </el-tab-pane>
            <el-tab-pane label="活动记录" name="activities">
              <div class="activity-list">
                <div v-for="activity in activities" :key="activity.id" class="activity-item">
                  <img :src="activity.actor?.avatar" alt="avatar" />
                  <div>
                    <div>{{ activity.content }}</div>
                    <div class="tiny-muted">{{ activity.created_at }}</div>
                  </div>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
          <div class="detail-actions" style="margin-top: 24px;">
            <el-button @click="showEdit = true">编辑任务</el-button>
            <el-button type="warning" @click="markBlocked">标记阻塞</el-button>
            <el-button type="primary" @click="acceptTask">更新进度</el-button>
          </div>
        </div>
      </el-drawer>

    <div class="teamflow-card milestones-panel">
      <div class="panel-header">
        <div class="section-title">里程碑进度</div>
        <router-link class="action-link" :to="`/projects/${projectId}/milestones`">查看全部里程碑</router-link>
      </div>
      <div class="milestone-track">
        <div v-for="(item, index) in milestones" :key="item.id" class="milestone-item dark" :style="{ background: getMilestoneBg(index) }">
          <div class="milestone-name">{{ item.name }}</div>
          <div class="milestone-status">{{ item.status }}</div>
          <div class="milestone-date">{{ item.due_date }}</div>
        </div>
      </div>
    </div>

    <el-dialog v-model="showEdit" :title="editingTask.id ? '编辑任务' : '新建任务'" width="min(680px, 92vw)">
      <el-form :model="editingTask" label-position="top">
        <el-form-item label="任务标题"><el-input v-model="editingTask.title" /></el-form-item>
        <el-form-item label="任务描述"><el-input v-model="editingTask.description" rows="4" type="textarea" /></el-form-item>
        <div class="grid-2">
          <el-form-item label="优先级">
            <el-select v-model="editingTask.priority">
              <el-option label="高" value="高" />
              <el-option label="中" value="中" />
              <el-option label="低" value="低" />
            </el-select>
          </el-form-item>
          <el-form-item label="截止日期"><el-input v-model="editingTask.due_date" /></el-form-item>
        </div>
        <div class="grid-2">
          <el-form-item label="负责人">
            <el-select v-model="editingTask.assignee_id" clearable>
              <el-option v-for="member in members" :key="member.user_id" :label="member.name" :value="member.user_id" />
            </el-select>
          </el-form-item>
          <el-form-item label="里程碑">
            <el-select v-model="editingTask.milestone_id">
              <el-option v-for="item in milestones" :key="item.id" :label="item.name" :value="item.id" />
            </el-select>
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="showEdit = false">取消</el-button>
        <el-button type="primary" @click="saveTask">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { projectApi, taskApi } from '@/api'
import { useAiStore } from '@/stores/ai'

const route = useRoute()
const router = useRouter()
const aiStore = useAiStore()
const projectId = computed(() => route.params.id as string)
const loading = ref(false)
const tasks = ref<any[]>([])
const milestones = ref<any[]>([])
const activities = ref<any[]>([])
const members = ref<any[]>([])
const selectedTask = ref<any>(null)
const detailOpen = ref(false)
const detailTab = ref('info')
const showEdit = ref(false)
const filters = reactive({ assignee: '', milestone: '', priority: '', status: '', keyword: '' })
const editingTask = reactive<any>({
  id: null,
  title: '',
  description: '',
  priority: '中',
  due_date: '',
  assignee_id: null,
  milestone_id: null,
  status: 'TODO',
  progress: 0,
  start_date: '2024-05-15',
  blocker_reason: '',
  related_requirement: '',
  related_document: '',
  related_commit: '',
})

const getMilestoneBg = (index: number) => {
  const backgrounds = [
    'linear-gradient(135deg, #F472B6 0%, #DB2777 100%)',
    'linear-gradient(135deg, #A78BFA 0%, #7C3AED 100%)',
    'linear-gradient(135deg, #22D3EE 0%, #0891B2 100%)',
    'linear-gradient(135deg, #818CF8 0%, #4F46E5 100%)',
    'linear-gradient(135deg, #34D399 0%, #059669 100%)',
    'linear-gradient(135deg, #FB923C 0%, #EA580C 100%)',
    'linear-gradient(135deg, #FBBF24 0%, #D97706 100%)',
    'linear-gradient(135deg, #FB7185 0%, #E11D48 100%)',
  ]
  return backgrounds[index % backgrounds.length]
}

const columns = [
  { key: 'TODO', label: '待处理' },
  { key: 'IN_PROGRESS', label: '进行中' },
  { key: 'BLOCKED', label: '阻塞中' },
  { key: 'REVIEW', label: '待评审' },
  { key: 'DONE', label: '已完成' },
]

const filteredTasks = computed(() => {
  return tasks.value.filter((task) => {
    const matchAssignee = !filters.assignee || task.assignee?.name === filters.assignee || task.assignee_id === filters.assignee
    const matchMilestone = !filters.milestone || task.milestone_id === filters.milestone || task.milestone?.name === filters.milestone
    const matchPriority = !filters.priority || task.priority === filters.priority
    const matchStatus = !filters.status || task.status === filters.status
    const matchKeyword = !filters.keyword || `${task.title}${task.description}`.includes(filters.keyword)
    return matchAssignee && matchMilestone && matchPriority && matchStatus && matchKeyword
  })
})

const grouped = computed(() =>
  columns.reduce<Record<string, any[]>>((acc, column) => {
    acc[column.key] = filteredTasks.value.filter((task) => task.status === column.key)
    return acc
  }, {}),
)

const load = async () => {
  loading.value = true
  try {
    const [taskRes, milestoneRes, memberRes] = await Promise.all([
      taskApi.list(projectId.value),
      taskApi.milestones(projectId.value),
      projectApi.members(projectId.value),
    ])
    tasks.value = taskRes.data
    milestones.value = milestoneRes.data
    members.value = memberRes.data
    const queryTaskId = Number(route.query.taskId || 0)
    selectedTask.value = tasks.value.find((item) => item.id === queryTaskId) || tasks.value[3] || tasks.value[0]
    if (selectedTask.value) await loadActivities(selectedTask.value.id)
    syncAiContext()
  } finally {
    loading.value = false
  }
}

const loadActivities = async (taskId: number) => {
  const { data } = await taskApi.activities(taskId)
  activities.value = data
}

const selectTask = async (task: any) => {
  selectedTask.value = task
  detailOpen.value = true
  await loadActivities(task.id)
  syncAiContext()
}

const syncAiContext = () => {
  aiStore.setPageContext({
    selectedTaskId: selectedTask.value?.id || null,
    filters: JSON.stringify(filters),
  })
}

const handleAiRefresh = async () => {
  await load()
}

const openCreate = (status = 'TODO') => {
  Object.assign(editingTask, {
    id: null,
    title: '',
    description: '',
    priority: '中',
    due_date: '',
    assignee_id: null,
    milestone_id: milestones.value[0]?.id ?? null,
    status,
    progress: 0,
    start_date: '2024-05-15',
    blocker_reason: '',
    related_requirement: '',
    related_document: '',
    related_commit: '',
  })
  showEdit.value = true
}

const saveTask = async () => {
  if (editingTask.id) {
    await taskApi.update(editingTask.id, editingTask)
    ElMessage.success('任务已更新')
  } else {
    await taskApi.create(projectId.value, editingTask)
    ElMessage.success('任务已创建')
  }
  showEdit.value = false
  await load()
}

const acceptTask = async () => {
  if (!selectedTask.value) return
  await taskApi.accept(selectedTask.value.id)
  ElMessage.success('已开始处理任务')
  await load()
}

const markBlocked = async () => {
  if (!selectedTask.value) return
  await taskApi.block(selectedTask.value.id, { blocker_reason: '等待接口定义完成后继续推进' })
  ElMessage.warning('任务已标记阻塞')
  await load()
}

const openRelated = async (type: 'requirement' | 'document' | 'commit') => {
  if (!selectedTask.value) return
  if (type === 'document') {
    await router.push(`/projects/${projectId.value}/documents`)
    return
  }
  if (type === 'commit') {
    await router.push(`/projects/${projectId.value}/git`)
    return
  }
  ElMessage.info(`关联需求：${selectedTask.value.related_requirement}`)
}

watch(filters, syncAiContext, { deep: true })

onMounted(() => {
  window.addEventListener('teamflow-ai-refresh', handleAiRefresh as EventListener)
  load()
})

onUnmounted(() => {
  window.removeEventListener('teamflow-ai-refresh', handleAiRefresh as EventListener)
})
</script>

<style scoped>
.tasks-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.header-row,
.header-actions,
.column-head,
.panel-header,
.task-owner,
.task-foot,
.detail-head,
.detail-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.filters {
  display: grid;
  gap: 14px;
  padding: 18px;
  grid-template-columns: repeat(5, minmax(0, 1fr));
}

.kanban-layout {
  display: flex;
  flex-direction: column;
}

.kanban-board {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(5, minmax(0, 1fr));
}

.kanban-column {
  display: flex;
  flex-direction: column;
  padding: 16px;
}

.column-head {
  margin-bottom: 12px;
  font-weight: 700;
}

.column-head b {
  display: grid;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  place-items: center;
  background: #eef2ff;
  color: var(--text-muted);
}

.column-list {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 12px;
}

.task-card {
  padding: 14px;
  border: 1px solid #edf1ff;
  border-radius: 16px;
  cursor: pointer;
  transition: 0.2s ease;
}

.task-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 28px rgba(79, 70, 229, 0.08);
}

.task-title {
  min-height: 44px;
  font-weight: 700;
}

.task-owner {
  margin: 10px 0;
  gap: 6px;
  justify-content: flex-start;
}

.task-owner img,
.activity-item img {
  width: 24px;
  height: 24px;
  border-radius: 50%;
}

.priority {
  margin-left: auto;
  font-size: 12px;
}

.priority.高 {
  color: var(--danger);
}

.priority.中 {
  color: var(--warning);
}

.priority.低 {
  color: var(--success);
}

.task-foot {
  margin-top: 8px;
  color: var(--text-muted);
  font-size: 12px;
}

.blocker {
  margin-top: 10px;
  padding: 6px 8px;
  border-radius: 8px;
  background: rgba(239, 68, 68, 0.1);
  color: var(--danger);
  font-size: 12px;
}

.add-task {
  margin-top: 10px;
  text-align: center;
}

.task-detail,
.milestones-panel {
  padding: 18px;
}

.detail-title {
  font-size: 24px;
  font-weight: 700;
}

.detail-grid,
.related-box {
  display: grid;
  gap: 14px;
  margin-top: 20px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.detail-grid label,
.related-box label {
  display: block;
  margin-bottom: 6px;
  color: var(--text-muted);
  font-size: 13px;
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.activity-item {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.milestone-track {
  display: grid;
  gap: 12px;
  margin-top: 18px;
  grid-template-columns: repeat(6, minmax(0, 1fr));
}

.milestone-item {
  padding: 14px;
  border-radius: 14px;
  /* background dynamically applied via inline style */
}

.milestone-name {
  font-weight: 700;
}

.milestone-status {
  margin: 8px 0 6px;
  color: var(--primary);
}

@media (max-width: 1400px) {
  .filters {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .kanban-board {
    overflow-x: auto;
    grid-auto-columns: minmax(240px, 1fr);
    grid-auto-flow: column;
    grid-template-columns: none;
  }

  .milestone-track {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .header-row,
  .header-actions,
  .detail-actions {
    align-items: stretch;
    gap: 10px;
    flex-direction: column;
  }

  .filters,
  .detail-grid,
  .related-box,
  .milestone-track {
    grid-template-columns: 1fr;
  }

  .kanban-column {
    min-width: 240px;
  }

  .detail-head {
    align-items: flex-start;
    gap: 10px;
    flex-direction: column;
  }
}
</style>

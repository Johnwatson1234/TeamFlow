<template>
  <div class="tasks-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">任务看板</h1>
        <p class="page-subtitle">拖拽任务卡片以更新状态</p>
      </div>
      <el-button type="primary" @click="showCreate = true" id="btn-create-task">
        <el-icon><Plus /></el-icon> 新建任务
      </el-button>
    </div>

    <div v-if="loading" class="loading-wrap"><el-skeleton :rows="3" animated /></div>

    <div v-else class="kanban-board">
      <div v-for="col in columns" :key="col.status" class="kanban-col">
        <div class="col-header" :style="{ borderTopColor: col.color }">
          <div class="col-title">
            <span class="status-dot" :class="col.dotClass"></span>
            {{ col.label }}
          </div>
          <span class="col-count">{{ tasksByStatus(col.status).length }}</span>
        </div>
        <div class="col-body">
          <div
            v-for="task in tasksByStatus(col.status)"
            :key="task.id"
            class="task-card"
            :class="{ overdue: isOverdue(task) }"
            @click="openTask(task)"
            :id="`task-${task.id}`"
            draggable="true"
            @dragstart="dragStart(task)"
            @dragover.prevent
            @drop="drop(col.status)"
          >
            <div class="task-priority" :class="task.priority">{{ priorityLabel(task.priority) }}</div>
            <div class="task-title">{{ task.title }}</div>
            <div class="task-desc" v-if="task.description">{{ task.description }}</div>
            <div class="task-progress" v-if="task.status !== 'TODO'">
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: task.progress + '%', background: col.color }"></div>
              </div>
              <span class="progress-text">{{ task.progress }}%</span>
            </div>
            <div class="task-footer">
              <div class="task-assignee" v-if="task.assignee">
                <div class="avatar avatar-sm" :style="{ background: avatarColor(task.assignee?.nickname) }">
                  {{ task.assignee?.nickname?.[0]?.toUpperCase() }}
                </div>
                <span>{{ task.assignee?.nickname }}</span>
              </div>
              <div v-else class="task-unassigned">未分配</div>
              <div class="task-due" v-if="task.due_time" :class="{ overdue: isOverdue(task) }">
                <el-icon size="11"><Clock /></el-icon>
                {{ formatDate(task.due_time) }}
              </div>
            </div>
          </div>
          <!-- Drop zone -->
          <div
            class="drop-zone"
            @dragover.prevent
            @drop="drop(col.status)"
          >拖放任务到此处</div>
        </div>
      </div>
    </div>

    <!-- Task detail drawer -->
    <el-drawer v-model="showDetail" :title="selectedTask?.title" size="40%" :destroy-on-close="true">
      <div v-if="selectedTask" class="task-detail">
        <div class="detail-row">
          <span class="detail-label">状态</span>
          <el-select v-model="editForm.status" @change="updateTask" size="small" id="task-status-sel">
            <el-option v-for="c in columns" :key="c.status" :label="c.label" :value="c.status" />
          </el-select>
        </div>
        <div class="detail-row">
          <span class="detail-label">进度</span>
          <div style="flex:1; display:flex; align-items:center; gap:12px">
            <el-slider v-model="editForm.progress" :step="5" @change="updateTask" style="flex:1" />
            <span>{{ editForm.progress }}%</span>
          </div>
        </div>
        <div class="detail-row">
          <span class="detail-label">优先级</span>
          <el-select v-model="editForm.priority" @change="updateTask" size="small">
            <el-option label="低" value="low" /><el-option label="中" value="medium" />
            <el-option label="高" value="high" /><el-option label="紧急" value="critical" />
          </el-select>
        </div>
        <div class="detail-row">
          <span class="detail-label">负责人</span>
          <el-select v-model="editForm.assignee_id" @change="updateTask" size="small" clearable>
            <el-option v-for="m in members" :key="m.user_id" :label="m.user?.nickname" :value="m.user_id" />
          </el-select>
        </div>
        <div class="detail-row">
          <span class="detail-label">截止时间</span>
          <el-date-picker v-model="editForm.due_time" type="datetime" size="small" @change="updateTask" />
        </div>
        <div class="detail-section">
          <div class="detail-label mb-2">任务描述</div>
          <el-input v-model="editForm.description" type="textarea" :rows="4" @blur="updateTask" />
        </div>
        <div class="detail-actions">
          <el-button type="danger" @click="deleteTask" size="small">删除任务</el-button>
        </div>
      </div>
    </el-drawer>

    <!-- Create task dialog -->
    <el-dialog v-model="showCreate" title="新建任务" width="480px">
      <el-form :model="createForm" label-position="top">
        <el-form-item label="任务标题" required>
          <el-input v-model="createForm.title" id="create-task-title" />
        </el-form-item>
        <el-form-item label="任务描述">
          <el-input v-model="createForm.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="优先级">
              <el-select v-model="createForm.priority" style="width:100%">
                <el-option label="低" value="low" /><el-option label="中" value="medium" />
                <el-option label="高" value="high" /><el-option label="紧急" value="critical" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="负责人">
              <el-select v-model="createForm.assignee_id" style="width:100%" clearable>
                <el-option v-for="m in members" :key="m.user_id" :label="m.user?.nickname" :value="m.user_id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="截止时间">
          <el-date-picker v-model="createForm.due_time" type="datetime" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" id="confirm-create-task">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { taskApi, projectApi } from '@/api'
import dayjs from 'dayjs'

const route = useRoute()
const projectId = computed(() => Number(route.params.id))
const loading = ref(false)
const tasks = ref<any[]>([])
const members = ref<any[]>([])
const showCreate = ref(false)
const showDetail = ref(false)
const selectedTask = ref<any>(null)
const dragging = ref<any>(null)

const createForm = reactive({ title: '', description: '', priority: 'medium', assignee_id: null as any, due_time: null as any })
const editForm = reactive({ status: '', progress: 0, priority: 'medium', assignee_id: null as any, due_time: null as any, description: '' })

const columns = [
  { status: 'TODO', label: '待处理', color: '#94A3B8', dotClass: 'todo' },
  { status: 'IN_PROGRESS', label: '进行中', color: '#4F46E5', dotClass: 'in-progress' },
  { status: 'BLOCKED', label: '阻塞中', color: '#EF4444', dotClass: 'blocked' },
  { status: 'REVIEW', label: '待评审', color: '#F59E0B', dotClass: 'review' },
  { status: 'DONE', label: '已完成', color: '#22C55E', dotClass: 'done' },
]

function tasksByStatus(status: string) { return tasks.value.filter(t => t.status === status) }
function isOverdue(t: any) { return t.due_time && new Date(t.due_time) < new Date() && t.status !== 'DONE' }
function formatDate(dt: string) { return dayjs(dt).format('MM/DD') }
function avatarColor(name?: string) {
  const colors = ['#4F46E5','#7C3AED','#0891B2','#059669','#D97706','#DC2626']
  if (!name) return colors[0]
  return colors[name.charCodeAt(0) % colors.length]
}
function priorityLabel(p: string) { return { low: '低', medium: '中', high: '高', critical: '紧急' }[p] || p }

function dragStart(task: any) { dragging.value = task }
async function drop(status: string) {
  if (!dragging.value || dragging.value.status === status) return
  try {
    await taskApi.update(dragging.value.id, { status })
    const t = tasks.value.find(t => t.id === dragging.value.id)
    if (t) t.status = status
    ElMessage.success('状态已更新')
  } catch { ElMessage.error('更新失败') }
  dragging.value = null
}

function openTask(task: any) {
  selectedTask.value = task
  Object.assign(editForm, { status: task.status, progress: task.progress, priority: task.priority, assignee_id: task.assignee_id, due_time: task.due_time, description: task.description || '' })
  showDetail.value = true
}

async function updateTask() {
  if (!selectedTask.value) return
  try {
    const updated: any = await taskApi.update(selectedTask.value.id, editForm)
    const idx = tasks.value.findIndex(t => t.id === selectedTask.value.id)
    if (idx >= 0) Object.assign(tasks.value[idx], editForm)
  } catch { ElMessage.error('更新失败') }
}

async function deleteTask() {
  if (!selectedTask.value) return
  try {
    await taskApi.delete(selectedTask.value.id)
    tasks.value = tasks.value.filter(t => t.id !== selectedTask.value?.id)
    showDetail.value = false
    ElMessage.success('任务已删除')
  } catch { ElMessage.error('删除失败') }
}

async function handleCreate() {
  if (!createForm.title) return ElMessage.warning('请输入任务标题')
  try {
    const res: any = await taskApi.create(projectId.value, createForm)
    tasks.value.unshift(res)
    showCreate.value = false
    ElMessage.success('任务创建成功')
  } catch { ElMessage.error('创建失败') }
}

async function fetchAll() {
  loading.value = true
  try {
    const [ts, ms] = await Promise.all([taskApi.list(projectId.value), projectApi.members(projectId.value)])
    tasks.value = ts as any[]
    members.value = ms as any[]
  } finally { loading.value = false }
}

watch(projectId, fetchAll)
onMounted(fetchAll)
</script>

<style scoped>
.tasks-page { padding: 28px 32px; }
.loading-wrap { padding: 20px; }

.kanban-board { display: flex; gap: 14px; overflow-x: auto; padding-bottom: 16px; min-height: calc(100vh - 160px); }

.kanban-col { flex: 1; min-width: 220px; max-width: 280px; }
.col-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 14px; background: white; border-radius: var(--radius) var(--radius) 0 0;
  border: 1px solid var(--border); border-top: 3px solid; margin-bottom: 8px;
}
.col-title { display: flex; align-items: center; font-size: 13px; font-weight: 600; }
.col-count { background: var(--bg-dark); font-size: 11px; font-weight: 700; padding: 2px 7px; border-radius: 10px; color: var(--text-muted); }

.col-body { display: flex; flex-direction: column; gap: 8px; min-height: 100px; }

.task-card {
  background: white; border: 1px solid var(--border); border-radius: var(--radius);
  padding: 12px 14px; cursor: pointer; box-shadow: var(--shadow-sm);
  transition: transform 0.15s, box-shadow 0.15s; position: relative;
}
.task-card:hover { transform: translateY(-2px); box-shadow: var(--shadow); }
.task-card.overdue { border-left: 3px solid #EF4444; }

.task-priority {
  font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 8px; display: inline-block; margin-bottom: 6px;
}
.task-priority.low { background: #F0FDF4; color: #16A34A; }
.task-priority.medium { background: #EEF2FF; color: #4F46E5; }
.task-priority.high { background: #FEF3C7; color: #D97706; }
.task-priority.critical { background: #FEE2E2; color: #DC2626; }

.task-title { font-size: 13px; font-weight: 600; line-height: 1.4; margin-bottom: 4px; }
.task-desc { font-size: 11.5px; color: var(--text-muted); margin-bottom: 8px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }

.task-progress { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.progress-bar { flex: 1; height: 4px; background: var(--border); border-radius: 2px; }
.progress-fill { height: 100%; border-radius: 2px; transition: width 0.3s; }
.progress-text { font-size: 10px; color: var(--text-muted); }

.task-footer { display: flex; align-items: center; justify-content: space-between; }
.task-assignee { display: flex; align-items: center; gap: 5px; font-size: 11.5px; }
.task-unassigned { font-size: 11px; color: var(--text-light); }
.task-due { display: flex; align-items: center; gap: 3px; font-size: 11px; color: var(--text-muted); }
.task-due.overdue { color: #EF4444; }

.drop-zone {
  border: 2px dashed var(--border); border-radius: var(--radius); padding: 12px;
  text-align: center; font-size: 12px; color: var(--text-light); opacity: 0;
  transition: opacity 0.2s;
}
.kanban-col:has(.task-card[draggable]:hover) .drop-zone { opacity: 1; }

.task-detail { padding: 8px 0; }
.detail-row { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.detail-label { font-size: 13px; font-weight: 500; color: var(--text-muted); min-width: 70px; }
.detail-section { margin-bottom: 16px; }
.detail-actions { padding-top: 16px; border-top: 1px solid var(--border); }
</style>

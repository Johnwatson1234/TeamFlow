<template>
  <div class="files-page">
    <div class="header-row">
      <div>
        <h1 class="page-title">文件共享与资料评审</h1>
        <div class="page-desc">上传项目资料、查看评审状态，并让 AI 对真实文件内容做实时分析。</div>
      </div>
    </div>

    <section class="grid-4">
      <StatCard theme="dark" title="文件总数" :value="files.length" footer="项目内共享资源" :icon="FolderOpened" bg="linear-gradient(135deg, #38BDF8 0%, #0284C7 100%)" />
      <StatCard theme="dark" title="待评审" :value="pendingCount" footer="等待团队处理" :icon="Clock" bg="linear-gradient(135deg, #FBBF24 0%, #D97706 100%)" />
      <StatCard theme="dark" title="最近上传" :value="recentUploadCount" footer="近 7 天" :icon="UploadFilled" bg="linear-gradient(135deg, #34D399 0%, #059669 100%)" />
      <StatCard theme="dark" title="已选资源" :value="selectedFile?.name || '--'" footer="当前 AI 可读取上下文" :icon="PieChart" bg="linear-gradient(135deg, #818CF8 0%, #4F46E5 100%)" />
    </section>

    <div class="files-layout">
      <!-- Sidebar Left -->
      <aside class="sidebar-left">
        <div class="teamflow-card mini-card">
          <div class="section-title">分类目录</div>
          <div class="folder-list">
            <button
              v-for="name in folderNames"
              :key="name"
              type="button"
              :class="['folder-item', { active: activeFolder === name }]"
              @click="activeFolder = name"
            >
              {{ name }}
            </button>
          </div>
        </div>

        <div class="teamflow-card mini-card">
          <div class="section-title">上传文件</div>
          <div class="upload-box">
            <el-upload :auto-upload="false" :before-upload="beforeUpload" :on-change="handleUpload" drag :show-file-list="false">
              <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
              <div class="el-upload__text">拖拽或 <em>点击上传</em></div>
            </el-upload>
          </div>
        </div>

        <div class="teamflow-card mini-card">
          <div class="section-title">AI 提示</div>
          <div class="review-track">
            <div class="review-node">AI 会读取真实文件内容</div>
            <div class="review-node">支持常见格式，并可跨页分析</div>
          </div>
        </div>
      </aside>

      <!-- Main Table -->
      <div class="teamflow-card file-table-panel">
        <div class="panel-header" style="margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center;">
          <div class="section-title" style="font-size: 18px;">{{ activeFolder }}</div>
        </div>
        <el-table :data="filteredFiles" @row-click="selectFile" stripe style="width: 100%">
          <el-table-column label="文件名称" prop="name" min-width="200" show-overflow-tooltip />
          <el-table-column label="类型" prop="file_type" width="100" />
          <el-table-column label="关联任务" prop="related_task" width="130" show-overflow-tooltip />
          <el-table-column label="上传者" width="100">
            <template #default="{ row }">{{ row.uploader?.name }}</template>
          </el-table-column>
          <el-table-column label="版本" prop="version_label" width="80" />
          <el-table-column label="更新时间" prop="updated_at" width="160" />
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <span :class="['status-tag', row.review_status === '已通过' ? 'green' : row.review_status === '待评审' ? 'orange' : 'red']">
                {{ row.review_status }}
              </span>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- Preview Sidebar -->
      <aside class="teamflow-card file-preview" v-if="selectedFile">
        <div class="section-title" style="display: flex; justify-content: space-between; align-items: center;">
          <span>文件预览</span>
          <el-popconfirm title="确定要永久删除该文件吗？" @confirm="handleDelete(selectedFile.id)" confirm-button-text="删除" confirm-button-type="danger" cancel-button-text="取消">
            <template #reference>
              <el-button type="danger" link size="small" style="padding: 0; min-height: auto;">删除</el-button>
            </template>
          </el-popconfirm>
        </div>
        <div class="preview-name">{{ selectedFile.name }}</div>
        <span :class="['status-tag', selectedFile.review_status === '已通过' ? 'green' : selectedFile.review_status === '待评审' ? 'orange' : 'red']">{{ selectedFile.review_status }}</span>
        <div class="preview-grid">
          <div><label>上传者</label><span>{{ selectedFile.uploader?.name }}</span></div>
          <div><label>更新时间</label><span>{{ selectedFile.updated_at }}</span></div>
          <div><label>关联任务</label><span>{{ selectedFile.related_task || '未关联' }}</span></div>
          <div><label>存储位置</label><span>{{ selectedFile.storage_path }}</span></div>
        </div>
        <p class="page-desc">{{ selectedFile.description }}</p>
        <div class="section-title" style="margin-top: 24px; font-size: 14px;">讨论记录</div>
        <div class="comment-list">
          <div v-for="item in selectedFile.comments" :key="`${item.author}-${item.time}`" class="comment-item">
            <strong>{{ item.author }}</strong>
            <div class="tiny-muted">{{ item.time }}</div>
            <div style="margin-top: 6px; line-height: 1.5;">{{ item.content }}</div>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Clock, FolderOpened, PieChart, UploadFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import { fileApi } from '@/api'
import StatCard from '@/components/common/StatCard.vue'
import { useAiStore } from '@/stores/ai'

const route = useRoute()
const aiStore = useAiStore()

const projectId = computed(() => route.params.id as string)
const files = ref<any[]>([])
const selectedFile = ref<any>(null)
const activeFolder = ref('需求文档')
const folderNames = ['需求文档', '设计文档', '开发资料', '测试报告', '演示资料']
const folderCategoryMap: Record<string, string[]> = {
  需求文档: ['需求'],
  设计文档: ['设计', '数据库'],
  开发资料: ['接口', '代码', '计划'],
  测试报告: ['测试'],
  演示资料: ['演示', '视频'],
}

const pendingCount = computed(() => files.value.filter((item) => item.review_status === '待评审').length)
const recentUploadCount = computed(() => files.value.slice(0, 7).length)
const filteredFiles = computed(() => {
  const categories = folderCategoryMap[activeFolder.value] || []
  const rows = files.value.filter((item) => categories.includes(item.category))
  return rows.length ? rows : files.value
})

const syncAiContext = () => {
  aiStore.setPageContext({
    selectedFileId: selectedFile.value?.id || null,
    activeFolder: activeFolder.value,
  })
}

const load = async () => {
  const { data } = await fileApi.list(projectId.value)
  files.value = data
  const queryFileId = Number(route.query.fileId || 0)
  selectedFile.value = data.find((item: any) => item.id === queryFileId) || data[0] || null
  syncAiContext()
}

const selectFile = (row: any) => {
  selectedFile.value = row
  syncAiContext()
}

const beforeUpload = () => false

const handleUpload = async (uploadFile: any) => {
  if (!uploadFile.raw) {
    ElMessage.warning('没有检测到可上传的文件')
    return
  }
  const formData = new FormData()
  formData.append('upload', uploadFile.raw)
  formData.append('category', folderCategoryMap[activeFolder.value]?.[0] || '其他')
  formData.append('related_task', selectedFile.value?.related_task || '')
  await fileApi.upload(projectId.value, formData)
  ElMessage.success('文件上传成功')
  await load()
}

const handleDelete = async (id: number) => {
  try {
    await fileApi.remove(id)
    ElMessage.success('文件已删除')
    if (selectedFile.value?.id === id) {
      selectedFile.value = null
    }
    await load()
  } catch (error) {
    // Error is handled by interceptor, but we can catch to prevent unhandled rejection
  }
}

const handleAiRefresh = async () => {
  await load()
}

watch(filteredFiles, (rows) => {
  if (!rows.length) {
    selectedFile.value = null
    syncAiContext()
    return
  }
  if (!selectedFile.value || !rows.some((item) => item.id === selectedFile.value.id)) {
    selectedFile.value = rows[0]
    syncAiContext()
  }
})

watch(activeFolder, syncAiContext)

onMounted(() => {
  window.addEventListener('teamflow-ai-refresh', handleAiRefresh as EventListener)
  load()
})

onUnmounted(() => {
  window.removeEventListener('teamflow-ai-refresh', handleAiRefresh as EventListener)
})
</script>

<style scoped>
.files-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.files-layout {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.sidebar-left {
  width: 260px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.file-table-panel {
  flex: 1;
  min-width: 0;
  padding: 20px;
}

.file-preview {
  width: 320px;
  flex-shrink: 0;
  padding: 20px;
  position: sticky;
  top: 20px;
}

.mini-card {
  padding: 20px;
}

.folder-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 12px;
}

.folder-item {
  display: block;
  width: 100%;
  padding: 12px 16px;
  border: 0;
  border-radius: 12px;
  background: transparent;
  cursor: pointer;
  font: inherit;
  text-align: left;
  transition: all 0.2s;
  color: var(--text-regular);
}

.folder-item:hover {
  background: rgba(15, 23, 42, 0.04);
}

.folder-item.active {
  background: #EEF2FF;
  color: #4F46E5;
  font-weight: 700;
}

.upload-box {
  margin-top: 12px;
}

.upload-box :deep(.el-upload-dragger) {
  padding: 24px 10px;
  border-radius: 12px;
  background: #F8FAFC;
}

.upload-box :deep(.el-icon--upload) {
  font-size: 36px;
  margin-bottom: 8px;
  color: #4F46E5;
}

.review-track,
.comment-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 12px;
}

.review-node,
.comment-item {
  padding: 12px 14px;
  border: 1px solid rgba(15, 23, 42, 0.06);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.92);
  font-size: 13px;
  line-height: 1.5;
}

.preview-name {
  margin: 16px 0 10px;
  font-size: 22px;
  font-weight: 800;
  word-break: break-all;
  overflow-wrap: break-word;
  line-height: 1.4;
}

.preview-grid {
  display: grid;
  gap: 12px;
  margin: 16px 0;
}

.preview-grid label {
  display: block;
  margin-bottom: 6px;
  color: var(--text-muted);
}

@media (max-width: 1200px) {
  .files-layout {
    flex-direction: column;
  }

  .file-table-panel,
  .file-preview {
    width: 100%;
  }

  .file-preview {
    position: static;
  }
}

@media (max-width: 768px) {
  .preview-grid {
    grid-template-columns: 1fr;
  }
}
</style>

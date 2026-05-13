<template>
  <div class="files-page">
    <div class="page-header">
      <div><h1 class="page-title">文件共享</h1><p class="page-subtitle">{{ files.length }} 个文件</p></div>
      <label class="upload-btn" for="file-upload" id="btn-upload">
        <el-icon><Upload /></el-icon> 上传文件
        <input id="file-upload" type="file" multiple style="display:none" @change="handleUpload" />
      </label>
    </div>
    <div v-if="uploading" class="upload-progress"><el-progress :percentage="uploadPct" /></div>
    <div v-if="!files.length && !loading" class="empty-state">
      <div style="font-size:48px">📁</div>
      <p>还没有文件，上传第一个文件</p>
    </div>
    <el-table v-else :data="files" style="width:100%" class="files-table">
      <el-table-column prop="file_name" label="文件名" min-width="200">
        <template #default="{ row }">
          <div class="file-name-cell">
            <span class="file-icon">{{ fileIcon(row.file_type) }}</span>
            <span>{{ row.file_name }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="file_size" label="大小" width="100">
        <template #default="{ row }">{{ formatSize(row.file_size) }}</template>
      </el-table-column>
      <el-table-column label="上传者" width="120">
        <template #default="{ row }">{{ row.uploader?.nickname || '-' }}</template>
      </el-table-column>
      <el-table-column prop="created_at" label="上传时间" width="140">
        <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button text size="small" @click="downloadFile(row)"><el-icon><Download /></el-icon></el-button>
          <el-button text size="small" type="danger" @click="deleteFile(row)"><el-icon><Delete /></el-icon></el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { fileApi } from '@/api'
import dayjs from 'dayjs'

const route = useRoute()
const projectId = computed(() => Number(route.params.id))
const loading = ref(false)
const uploading = ref(false)
const uploadPct = ref(0)
const files = ref<any[]>([])

function formatDate(dt: string) { return dayjs(dt).format('MM/DD HH:mm') }
function formatSize(bytes: number) {
  if (bytes < 1024) return bytes + 'B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + 'KB'
  return (bytes / 1048576).toFixed(1) + 'MB'
}
function fileIcon(type: string) {
  if (!type) return '📎'
  if (type.includes('image')) return '🖼️'
  if (type.includes('pdf')) return '📕'
  if (type.includes('word') || type.includes('document')) return '📝'
  if (type.includes('excel') || type.includes('sheet')) return '📊'
  if (type.includes('zip') || type.includes('rar')) return '🗜️'
  if (type.includes('video')) return '🎬'
  return '📄'
}

async function fetchFiles() {
  loading.value = true
  try { files.value = (await fileApi.list(projectId.value) as any[]) } finally { loading.value = false }
}

async function handleUpload(e: Event) {
  const target = e.target as HTMLInputElement
  if (!target.files?.length) return
  uploading.value = true
  uploadPct.value = 0
  for (let i = 0; i < target.files.length; i++) {
    try {
      const res: any = await fileApi.upload(projectId.value, target.files[i])
      files.value.unshift({ ...res, uploader: null, created_at: new Date().toISOString() })
      uploadPct.value = Math.round(((i + 1) / target.files.length) * 100)
    } catch { ElMessage.error(`上传 ${target.files[i].name} 失败`) }
  }
  uploading.value = false
  ElMessage.success('上传完成')
  fetchFiles()
}

function downloadFile(file: any) { window.open(file.file_url, '_blank') }

async function deleteFile(file: any) {
  try { await fileApi.delete(file.id); files.value = files.value.filter(f => f.id !== file.id); ElMessage.success('已删除') }
  catch { ElMessage.error('删除失败') }
}

watch(projectId, fetchFiles)
onMounted(fetchFiles)
</script>

<style scoped>
.files-page { padding: 28px 32px; }
.upload-btn {
  display: flex; align-items: center; gap: 6px; cursor: pointer;
  padding: 8px 16px; background: var(--primary); color: white;
  border-radius: var(--radius-sm); font-size: 14px; font-weight: 500; transition: opacity 0.2s;
}
.upload-btn:hover { opacity: 0.9; }
.upload-progress { margin-bottom: 16px; }
.empty-state { text-align: center; padding: 60px 20px; display: flex; flex-direction: column; align-items: center; gap: 12px; color: var(--text-muted); }
.files-table { background: white; border-radius: var(--radius); border: 1px solid var(--border); overflow: hidden; }
.file-name-cell { display: flex; align-items: center; gap: 8px; }
.file-icon { font-size: 18px; }
</style>

<template>
  <div class="docs-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">协作文档</h1>
        <p class="page-subtitle">{{ docs.length }} 个文档</p>
      </div>
      <el-button type="primary" @click="showCreate = true" id="btn-create-doc">
        <el-icon><Plus /></el-icon> 新建文档
      </el-button>
    </div>

    <div v-if="loading"><el-skeleton :rows="3" animated /></div>

    <div v-else-if="!docs.length" class="empty-state">
      <div style="font-size:48px">📄</div>
      <p>还没有文档，创建第一个协作文档</p>
      <el-button type="primary" @click="showCreate = true">新建文档</el-button>
    </div>

    <div v-else class="docs-grid">
      <div v-for="doc in docs" :key="doc.id" class="doc-card" @click="openDoc(doc)" :id="`doc-${doc.id}`">
        <div class="doc-icon">📄</div>
        <div class="doc-info">
          <h3 class="doc-title">{{ doc.title }}</h3>
          <div class="doc-meta">
            <span class="tag" :class="permClass(doc.permission)">{{ permLabel(doc.permission) }}</span>
            <span class="doc-date">{{ formatDate(doc.updated_at) }}</span>
          </div>
        </div>
        <div class="doc-actions" @click.stop>
          <el-button text size="small" @click="deleteDoc(doc)"><el-icon><Delete /></el-icon></el-button>
        </div>
      </div>
    </div>

    <el-dialog v-model="showCreate" title="新建文档" width="400px">
      <el-form :model="createForm" label-position="top">
        <el-form-item label="文档标题" required>
          <el-input v-model="createForm.title" id="create-doc-title" />
        </el-form-item>
        <el-form-item label="权限">
          <el-select v-model="createForm.permission" style="width:100%">
            <el-option label="所有人可编辑" value="editable" />
            <el-option label="仅可评论" value="commentable" />
            <el-option label="仅可查看" value="readonly" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" id="confirm-create-doc">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { documentApi } from '@/api'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()
const projectId = computed(() => Number(route.params.id))
const loading = ref(false)
const docs = ref<any[]>([])
const showCreate = ref(false)
const createForm = reactive({ title: '', permission: 'editable' })

function formatDate(dt: string) { return dayjs(dt).format('MM/DD HH:mm') }
function permLabel(p: string) { return { editable: '可编辑', commentable: '可评论', readonly: '只读' }[p] || p }
function permClass(p: string) { return { editable: 'tag-success', commentable: 'tag-warning', readonly: 'tag-info' }[p] || 'tag-info' }
function openDoc(doc: any) { router.push(`/projects/${projectId.value}/documents/${doc.id}`) }

async function fetchDocs() {
  loading.value = true
  try { docs.value = (await documentApi.list(projectId.value) as any[]) } finally { loading.value = false }
}

async function handleCreate() {
  if (!createForm.title) return ElMessage.warning('请输入文档标题')
  try {
    const res: any = await documentApi.create(projectId.value, createForm)
    docs.value.unshift(res)
    showCreate.value = false
    router.push(`/projects/${projectId.value}/documents/${res.id}`)
  } catch { ElMessage.error('创建失败') }
}

async function deleteDoc(doc: any) {
  await ElMessageBox.confirm(`确认删除文档《${doc.title}》？`, '删除确认', { type: 'warning' })
  try {
    await documentApi.delete(doc.id)
    docs.value = docs.value.filter(d => d.id !== doc.id)
    ElMessage.success('文档已删除')
  } catch { ElMessage.error('删除失败') }
}

watch(projectId, fetchDocs)
onMounted(fetchDocs)
</script>

<style scoped>
.docs-page { padding: 28px 32px; }
.empty-state { text-align: center; padding: 60px 20px; display: flex; flex-direction: column; align-items: center; gap: 12px; color: var(--text-muted); }

.docs-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 14px; }
.doc-card {
  background: white; border: 1px solid var(--border); border-radius: var(--radius);
  padding: 16px; display: flex; align-items: center; gap: 12px; cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s; box-shadow: var(--shadow-sm);
}
.doc-card:hover { transform: translateY(-2px); box-shadow: var(--shadow); }
.doc-icon { font-size: 28px; }
.doc-info { flex: 1; min-width: 0; }
.doc-title { font-size: 14px; font-weight: 600; margin-bottom: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.doc-meta { display: flex; align-items: center; gap: 8px; }
.doc-date { font-size: 11px; color: var(--text-light); }
.doc-actions { flex-shrink: 0; }
</style>

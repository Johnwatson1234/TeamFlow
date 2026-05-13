<template>
  <div class="editor-page">
    <div class="editor-header">
      <el-button text @click="router.back()"><el-icon><ArrowLeft /></el-icon> 返回</el-button>
      <div class="editor-title-wrap">
        <el-input v-model="title" class="title-input" @blur="saveTitle" placeholder="文档标题" />
      </div>
      <div class="editor-actions">
        <el-button size="small" @click="saveVersion" :loading="saving">保存版本</el-button>
        <el-button size="small" @click="showVersions = true">版本历史</el-button>
      </div>
    </div>

    <div class="editor-body">
      <div class="editor-pane">
        <textarea
          v-model="content"
          class="editor-textarea"
          placeholder="在这里编写文档内容（支持 Markdown 格式）..."
          id="doc-content-area"
          @keydown.ctrl.s.prevent="saveVersion"
        />
      </div>
      <div class="preview-pane" v-html="previewHtml"></div>
    </div>

    <el-drawer v-model="showVersions" title="版本历史" size="30%">
      <div v-for="v in versions" :key="v.id" class="version-item" @click="loadVersion(v)">
        <div class="version-no">{{ v.version_no }}</div>
        <div class="version-summary">{{ v.summary || '自动保存' }}</div>
        <div class="version-meta">{{ formatDate(v.created_at) }} · +{{ v.valid_added_words }}字</div>
      </div>
      <div v-if="!versions.length" class="empty-hint">暂无历史版本</div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { documentApi } from '@/api'
import { marked } from 'marked'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()
const docId = computed(() => Number(route.params.docId))
const title = ref('')
const content = ref('')
const saving = ref(false)
const showVersions = ref(false)
const versions = ref<any[]>([])

const previewHtml = computed(() => {
  return marked.parse(content.value || '')
})

function formatDate(dt: string) { return dayjs(dt).format('MM/DD HH:mm') }

async function fetchDoc() {
  try {
    const doc: any = await documentApi.get(docId.value)
    title.value = doc.title
    if (doc.current_version_id) {
      const vers: any = await documentApi.versions(docId.value)
      versions.value = vers
      const cur = vers.find((v: any) => v.id === doc.current_version_id)
      if (cur?.snapshot) {
        try { content.value = JSON.parse(cur.snapshot).content || '' } catch { content.value = cur.snapshot }
      }
    }
  } catch { ElMessage.error('加载文档失败') }
}

async function saveTitle() {
  if (title.value) await documentApi.update(docId.value, { title: title.value })
}

async function saveVersion() {
  saving.value = true
  try {
    const snapshot = JSON.stringify({ content: content.value })
    const words = content.value.length
    await documentApi.saveVersion(docId.value, { snapshot, valid_added_words: words, summary: '手动保存' })
    const vers: any = await documentApi.versions(docId.value)
    versions.value = vers
    ElMessage.success('版本保存成功')
  } catch { ElMessage.error('保存失败') } finally { saving.value = false }
}

function loadVersion(v: any) {
  try { content.value = JSON.parse(v.snapshot).content || '' } catch { content.value = v.snapshot || '' }
  showVersions.value = false
  ElMessage.success(`已加载版本 ${v.version_no}`)
}

onMounted(fetchDoc)
</script>

<style scoped>
.editor-page { display: flex; flex-direction: column; height: 100vh; background: white; }
.editor-header {
  display: flex; align-items: center; gap: 12px; padding: 12px 20px;
  border-bottom: 1px solid var(--border); background: white; position: sticky; top: 0; z-index: 10;
}
.editor-title-wrap { flex: 1; }
.title-input :deep(.el-input__wrapper) { box-shadow: none !important; border: none !important; }
.title-input :deep(.el-input__inner) { font-size: 18px; font-weight: 700; }
.editor-actions { display: flex; gap: 8px; }
.editor-body { flex: 1; display: flex; overflow: hidden; border-top: 1px solid var(--border); }
.editor-pane { flex: 1; border-right: 1px solid var(--border); display: flex; }
.editor-textarea {
  flex: 1; padding: 30px; font-size: 15px; line-height: 1.6;
  border: none; outline: none; resize: none; font-family: 'Consolas', 'Monaco', monospace;
  color: var(--text); background: #fafafa;
}
.preview-pane {
  flex: 1; padding: 30px; overflow-y: auto; background: white;
  color: var(--text); line-height: 1.6; font-size: 15px;
}
.preview-pane :deep(h1), .preview-pane :deep(h2), .preview-pane :deep(h3) { margin-top: 24px; margin-bottom: 16px; font-weight: 700; }
.preview-pane :deep(p) { margin-bottom: 16px; }
.preview-pane :deep(code) { background: #f1f5f9; padding: 2px 4px; border-radius: 4px; font-family: monospace; }
.preview-pane :deep(pre) { background: #f1f5f9; padding: 16px; border-radius: 8px; overflow-x: auto; margin-bottom: 16px; }
.preview-pane :deep(ul), .preview-pane :deep(ol) { padding-left: 20px; margin-bottom: 16px; }
.version-item:hover { background: var(--bg); }
.version-no { font-weight: 600; font-size: 13px; }
.version-summary { font-size: 12px; color: var(--text-muted); margin: 2px 0; }
.version-meta { font-size: 11px; color: var(--text-light); }
.empty-hint { text-align: center; color: var(--text-muted); padding: 20px; }
</style>

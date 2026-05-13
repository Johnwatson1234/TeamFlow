<template>
  <div class="messages-page">
    <div class="page-header">
      <h1 class="page-title">即时消息</h1>
    </div>
    <div class="chat-container">
      <!-- Messages list -->
      <div class="messages-list" ref="msgList">
        <div v-if="loading" class="loading-center"><el-skeleton :rows="3" animated /></div>
        <div v-else-if="!messages.length" class="empty-chat">
          <div style="font-size:48px">💬</div>
          <p>还没有消息，发送第一条消息开始讨论！</p>
        </div>
        <div v-for="msg in messages" :key="msg.id" class="message-item" :class="{ 'my-message': msg.sender_id === me?.id }">
          <div class="msg-avatar" v-if="msg.sender_id !== me?.id">
            <div class="avatar avatar-sm" :style="{ background: avatarColor(msg.sender?.nickname) }">
              {{ msg.sender?.nickname?.[0]?.toUpperCase() }}
            </div>
          </div>
          <div class="msg-bubble-wrap">
            <div class="msg-sender" v-if="msg.sender_id !== me?.id">{{ msg.sender?.nickname }}</div>
            <div class="msg-bubble" :class="msg.message_type">
              <code v-if="msg.message_type === 'code'">{{ msg.content }}</code>
              <span v-else>{{ msg.content }}</span>
            </div>
            <div class="msg-time">{{ formatTime(msg.created_at) }}</div>
          </div>
        </div>
      </div>
      <!-- Input area -->
      <div class="input-area">
        <div class="input-toolbar">
          <el-radio-group v-model="msgType" size="small">
            <el-radio-button value="text">文字</el-radio-button>
            <el-radio-button value="code">代码</el-radio-button>
          </el-radio-group>
        </div>
        <div class="input-row">
          <el-input
            v-model="inputText"
            :type="msgType === 'code' ? 'textarea' : 'text'"
            :rows="msgType === 'code' ? 3 : 1"
            placeholder="输入消息，Enter 发送..."
            @keyup.enter.exact="sendMessage"
            id="msg-input"
          />
          <el-button type="primary" @click="sendMessage" :disabled="!inputText.trim()" id="btn-send">
            <el-icon><Promotion /></el-icon>
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { messageApi } from '@/api'
import { useUserStore } from '@/stores/user'
import dayjs from 'dayjs'

const route = useRoute()
const userStore = useUserStore()
const projectId = computed(() => Number(route.params.id))
const me = computed(() => userStore.user)
const loading = ref(false)
const messages = ref<any[]>([])
const inputText = ref('')
const msgType = ref('text')
const msgList = ref<HTMLElement>()
const onlineUsers = ref<number[]>([])
let ws: WebSocket | null = null

function avatarColor(name?: string) {
  const colors = ['#4F46E5','#7C3AED','#0891B2','#059669','#D97706','#DC2626']
  if (!name) return colors[0]
  return colors[name.charCodeAt(0) % colors.length]
}

function formatTime(dt: string) { return dayjs(dt).format('HH:mm') }

function initWebSocket() {
  const token = localStorage.getItem('token')
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host === 'localhost:5173' ? 'localhost:8000' : window.location.host
  
  ws = new WebSocket(`${protocol}//${host}/api/ws/${projectId.value}?token=${token}`)

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    if (data.type === 'message') {
      messages.value.push(data.data)
      nextTick(() => scrollToBottom())
    } else if (data.type === 'user_online' || data.type === 'user_offline') {
      onlineUsers.value = data.online_users
    }
  }

  ws.onclose = () => {
    console.log('WebSocket closed, retrying...')
    setTimeout(initWebSocket, 3000)
  }
}

async function fetchMessages() {
  loading.value = true
  try {
    const res: any = await messageApi.list(projectId.value)
    // 接口返回的是最新的在前面，我们要反转显示
    messages.value = Array.isArray(res) ? [...res].reverse() : []
    await nextTick()
    scrollToBottom()
  } finally { loading.value = false }
}

function scrollToBottom() {
  if (msgList.value) msgList.value.scrollTop = msgList.value.scrollHeight
}

async function sendMessage() {
  if (!inputText.value.trim()) return
  const content = inputText.value.trim()
  
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({
      type: 'message',
      content,
      message_type: msgType.value
    }))
    inputText.value = ''
  } else {
    // Fallback to REST
    try {
      const res: any = await messageApi.send(projectId.value, { content, message_type: msgType.value })
      messages.value.push({ ...res, sender: { id: me.value?.id, nickname: me.value?.nickname, avatar_url: me.value?.avatar_url } })
      inputText.value = ''
      await nextTick()
      scrollToBottom()
    } catch { ElMessage.error('发送失败') }
  }
}

watch(projectId, () => {
  if (ws) ws.close()
  fetchMessages()
  initWebSocket()
})

onMounted(() => {
  fetchMessages()
  initWebSocket()
})
</script>

<style scoped>
.messages-page { padding: 28px 32px; height: calc(100vh - 0px); display: flex; flex-direction: column; }
.page-header { margin-bottom: 16px; }
.chat-container { flex: 1; display: flex; flex-direction: column; background: white; border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; }
.messages-list { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 12px; }
.loading-center { padding: 20px; }
.empty-chat { display: flex; flex-direction: column; align-items: center; justify-content: center; flex: 1; color: var(--text-muted); gap: 8px; padding: 40px; }

.message-item { display: flex; gap: 10px; align-items: flex-end; }
.message-item.my-message { flex-direction: row-reverse; }

.msg-bubble-wrap { max-width: 60%; }
.msg-sender { font-size: 11px; color: var(--text-muted); margin-bottom: 4px; padding-left: 2px; }
.message-item.my-message .msg-sender { text-align: right; padding-right: 2px; }

.msg-bubble {
  padding: 10px 14px; border-radius: 14px; font-size: 14px; line-height: 1.5;
  background: var(--bg-dark); color: var(--text);
  border-radius: 18px 18px 18px 4px;
}
.message-item.my-message .msg-bubble {
  background: linear-gradient(135deg, #4F46E5, #7C3AED); color: white;
  border-radius: 18px 18px 4px 18px;
}
.msg-bubble.code { font-family: monospace; font-size: 12px; white-space: pre-wrap; }

.msg-time { font-size: 10px; color: var(--text-light); margin-top: 3px; padding: 0 2px; }
.message-item.my-message .msg-time { text-align: right; }

.input-area { border-top: 1px solid var(--border); padding: 12px 16px; }
.input-toolbar { margin-bottom: 8px; }
.input-row { display: flex; gap: 8px; align-items: flex-end; }
.input-row .el-input { flex: 1; }
</style>

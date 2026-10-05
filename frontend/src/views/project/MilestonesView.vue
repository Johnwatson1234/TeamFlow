<template>
  <div class="teamflow-card milestone-page">
    <div class="panel-header">
      <div>
        <h1 class="page-title">里程碑管理</h1>
        <div class="page-desc">把项目阶段、任务推进和交付节点放在一条时间轴上管理</div>
      </div>
      <el-button type="primary" @click="dialogVisible = true">新建里程碑</el-button>
    </div>
    <div class="timeline-container">
      <div v-for="(item, index) in milestones" :key="item.id" class="timeline-item">
        <div class="timeline-track">
          <div class="timeline-dot"></div>
          <div class="timeline-line" v-if="index !== milestones.length - 1"></div>
        </div>
        <div class="timeline-content teamflow-card">
          <div class="timeline-header">
            <div>
              <div class="timeline-title">阶段 {{ item.order_index + 1 }}: {{ item.name }}</div>
              <div class="timeline-desc tiny-muted">{{ item.description || '当前阶段的核心交付目标与验收标准尚未详细定义。' }}</div>
            </div>
            <div class="status-tag" :class="{ 'blue': item.status === '进行中', 'green': item.status === '已完成', 'orange': item.status === '待开始' }">{{ item.status }}</div>
          </div>
          
          <div class="timeline-metrics">
            <div class="metric-box">
              <label>负责人</label>
              <div class="owner-info">
                 <img :src="item.owner?.avatar || `https://api.dicebear.com/7.x/notionists/svg?seed=${item.id}`" alt="avatar" />
                 <span>{{ item.owner?.name || '张三' }}</span>
              </div>
            </div>
            <div class="metric-box">
              <label>截止日期</label>
              <span>{{ item.due_date || '未设置' }}</span>
            </div>
            <div class="metric-box">
              <label>时间状态</label>
              <span class="status-tag" :class="item.status === '已完成' ? 'green' : 'blue'" style="padding: 2px 8px; font-size: 12px;">{{ item.status === '已完成' ? '按期交付' : '剩余 12 天' }}</span>
            </div>
            <div class="metric-box">
              <label>风险预警</label>
              <span :style="{ color: item.status === '已完成' ? 'var(--text)' : '#ef4444' }">{{ item.status === '已完成' ? '无风险' : '1 个阻塞项' }}</span>
            </div>
          </div>
          
          <div class="timeline-progress-wrap">
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
               <span class="tiny-muted">任务完成度</span>
               <span class="tiny-muted" style="font-weight: 600; color: var(--text);">{{ item.status === '已完成' ? '100%' : (item.status === '待开始' ? '0%' : '65%') }} ({{ item.status === '已完成' ? '12/12' : '8/12' }})</span>
            </div>
            <div class="timeline-progress">
              <div class="progress-bar" :style="{ width: item.status === '已完成' ? '100%' : (item.status === '待开始' ? '0%' : '65%') }"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <el-dialog v-model="dialogVisible" title="新增里程碑" width="min(520px, 92vw)">
      <el-form :model="form" label-position="top">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="截止日期"><el-input v-model="form.due_date" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="createMilestone">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'

import { taskApi } from '@/api'

const route = useRoute()
const projectId = computed(() => route.params.id as string)
const milestones = ref<any[]>([])
const dialogVisible = ref(false)
const form = reactive({ name: '', due_date: '' })

const load = async () => {
  const { data } = await taskApi.milestones(projectId.value)
  milestones.value = data
}

const createMilestone = async () => {
  await taskApi.createMilestone(projectId.value, { ...form, status: '待开始' })
  ElMessage.success('里程碑已创建')
  dialogVisible.value = false
  form.name = ''
  form.due_date = ''
  await load()
}

onMounted(load)
</script>

<style scoped>
.milestone-page {
  padding: 24px 32px;
}

.timeline-container {
  display: flex;
  flex-direction: column;
  margin-top: 32px;
  gap: 0;
}

.timeline-item {
  display: flex;
  gap: 24px;
}

.timeline-track {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 32px;
  flex-shrink: 0;
}

.timeline-dot {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #fff;
  border: 4px solid var(--primary);
  z-index: 2;
  box-shadow: 0 0 0 4px rgba(79, 70, 229, 0.1);
}

.timeline-line {
  flex: 1;
  width: 2px;
  background: var(--border);
  margin: 8px 0;
  min-height: 40px;
}

.timeline-content {
  flex: 1;
  padding: 24px;
  margin-bottom: 32px;
  border-radius: 16px;
  background: #fff;
  transition: transform 0.2s, box-shadow 0.2s;
}

.timeline-content:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
  border-color: rgba(79, 70, 229, 0.3);
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.timeline-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text);
}

.timeline-desc {
  margin-top: 8px;
  line-height: 1.5;
  font-size: 13px;
  max-width: 80%;
}

.timeline-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 24px 48px;
  margin-bottom: 24px;
}

.metric-box {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 120px;
}

.metric-box label {
  font-size: 12px;
  color: var(--text-muted);
}

.metric-box span {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
}

.owner-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.owner-info img {
  width: 20px;
  height: 20px;
  border-radius: 50%;
}

.timeline-progress-wrap {
  margin-top: 24px;
}

.timeline-progress {
  height: 8px;
  background: var(--bg-dark);
  border-radius: 999px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, var(--cyan) 0%, var(--primary) 100%);
  border-radius: 999px;
}

@media (max-width: 768px) {
  .panel-header {
    align-items: flex-start;
    gap: 12px;
    flex-direction: column;
  }

  .timeline-item {
    gap: 16px;
  }

  .timeline-content {
    padding: 16px;
  }

  .timeline-title {
    font-size: 16px;
  }
}
</style>

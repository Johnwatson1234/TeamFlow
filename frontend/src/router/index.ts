import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/projects' },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { public: true },
    },
    {
      path: '/projects',
      name: 'projects',
      component: () => import('@/views/ProjectsView.vue'),
    },
    {
      path: '/projects/:id',
      component: () => import('@/layouts/ProjectLayout.vue'),
      children: [
        {
          path: '',
          name: 'dashboard',
          component: () => import('@/views/project/DashboardView.vue'),
        },
        {
          path: 'tasks',
          name: 'tasks',
          component: () => import('@/views/project/TasksView.vue'),
        },
        {
          path: 'messages',
          name: 'messages',
          component: () => import('@/views/project/MessagesView.vue'),
        },
        {
          path: 'documents',
          name: 'documents',
          component: () => import('@/views/project/DocumentsView.vue'),
        },
        {
          path: 'documents/:docId',
          name: 'document-editor',
          component: () => import('@/views/project/DocumentEditorView.vue'),
        },
        {
          path: 'files',
          name: 'files',
          component: () => import('@/views/project/FilesView.vue'),
        },
        {
          path: 'graph',
          name: 'graph',
          component: () => import('@/views/project/GraphView.vue'),
        },
        {
          path: 'contribution',
          name: 'contribution',
          component: () => import('@/views/project/ContributionView.vue'),
        },
        {
          path: 'risk',
          name: 'risk',
          component: () => import('@/views/project/RiskView.vue'),
        },
        {
          path: 'git',
          name: 'git',
          component: () => import('@/views/project/GitView.vue'),
        },
        {
          path: 'ai',
          name: 'ai',
          component: () => import('@/views/project/AIView.vue'),
        },
        {
          path: 'settings',
          name: 'project-settings',
          component: () => import('@/views/project/SettingsView.vue'),
        },
      ],
    },
  ],
})

router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  if (!to.meta.public && !token) {
    return '/login'
  }
})

export default router

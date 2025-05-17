import { createRouter, createWebHistory } from 'vue-router'
import StaticAnalysis from '../views/staticAnalysis/StaticAnalysis.vue'
import CodeReview from '../views/codeReview/CodeReview.vue'
import ModelConfigView from '../views/modelConfig/ModelConfigView.vue'
import DocumentReviewContainer from '../views/documentReview/DocumentReviewContainer.vue';
import ConfigurationItemTest from '../views/documentReview/configurationItem/ConfigurationItemTest.vue';
import { h } from 'vue';

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/document-review'
    },
    {
      path: '/document-review',
      name: 'document-review',
      component: DocumentReviewContainer,
      redirect: '/document-review/configuration-item',
      children: [
        {
          path: 'configuration-item',
          name: 'configuration-item-test',
          component: ConfigurationItemTest,
          meta: { type: 'configurationItem' }
        },
        {
          path: 'regression',
          name: 'RegressionPlaceholder',
          component: { render() { return h('div', { style: 'padding: 48px; text-align: center; color: #aaa; font-size: 20px;' }, '回归测试页面暂未开放'); } }
        },
      ]
    },
    {
      path: '/static-analysis',
      name: 'static-analysis',
      component: StaticAnalysis
    },
    {
      path: '/code-review',
      name: 'code-review',
      component: CodeReview
    },
    {
      path: '/config',
      name: 'model-config',
      component: ModelConfigView
    }
  ]
})

export default router

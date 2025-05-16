import { createRouter, createWebHistory } from 'vue-router'
import StaticAnalysis from '../views/StaticAnalysis.vue'
import CodeReview from '../views/CodeReview.vue'
import ModelConfigView from '../views/ModelConfigView.vue'
import DocumentReviewContainer from '../views/DocumentReviewContainer.vue'
import ConfigurationItemTest from '../views/ConfigurationItemTest.vue'
import RegressionTest from '../views/RegressionTest.vue'

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
          name: 'regression-test',
          component: RegressionTest,
          meta: { type: 'regression' }
        }
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

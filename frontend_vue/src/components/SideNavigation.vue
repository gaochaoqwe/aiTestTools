<template>
  <div class="side-navigation">
    <nav class="side-nav">
      <div class="nav-header">
        <h1>AI测试工具</h1>
      </div>
      <ul class="nav-links">
        <li class="has-submenu">
          <div class="nav-item" :class="{ active: isDocumentReviewActive }" @click="toggleDocumentReviewSubmenu">
            <i class="nav-icon doc-icon"></i>
            <span>文档审查</span>
            <i class="dropdown-icon" :class="{ 'dropdown-open': isDocumentReviewExpanded }"></i>
          </div>
          <ul class="submenu" v-show="isDocumentReviewExpanded">
            <li>
              <router-link to="/document-review/configuration-item" 
                         :class="{ active: currentRoute === '/document-review/configuration-item' }">
                <span>配置项测试</span>
              </router-link>
            </li>
            <li>
              <router-link to="/document-review/regression"
                         :class="{ active: currentRoute === '/document-review/regression' }">
                <span>回归测试</span>
              </router-link>
            </li>
          </ul>
        </li>
        <li>
          <router-link to="/static-analysis" :class="{ active: currentRoute === '/static-analysis' }">
            <i class="nav-icon analysis-icon"></i>
            <span>静态分析</span>
          </router-link>
        </li>
        <li>
          <router-link to="/code-review" :class="{ active: currentRoute === '/code-review' }">
            <i class="nav-icon code-icon"></i>
            <span>代码审查</span>
          </router-link>
        </li>
        <li class="bottom-nav-item">
          <router-link to="/config" :class="{ active: currentRoute === '/config' }">
            <i class="nav-icon config-icon"></i>
            <span>模型配置</span>
          </router-link>
        </li>
      </ul>
    </nav>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();
const currentRoute = computed(() => route.path);

// 兼容原有逻辑
const props = defineProps({
  activeTab: String
});

const emit = defineEmits(['update:activeTab']);

function setActiveTab(tab) {
  emit('update:activeTab', tab);
}

// 审查状态变量
const isDocumentReviewActive = computed(() => {
  return currentRoute.value.startsWith('/document-review');
});

// 默认展开文档审查菜单
const isDocumentReviewExpanded = ref(true);

function toggleDocumentReviewSubmenu() {
  isDocumentReviewExpanded.value = !isDocumentReviewExpanded.value;
}
</script>

<style scoped>
.side-navigation {
  width: 220px;
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  background-color: #2c3e50;
  color: #ecf0f1;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #34495e;
  box-shadow: 2px 0 5px rgba(0, 0, 0, 0.1);
  z-index: 100;
}

.side-nav {
  flex: 1;
  padding: 20px;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.nav-header {
  padding: 25px 15px;
  border-bottom: 1px solid #34495e;
  background-color: #1a2530;
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-header h1 {
  margin: 0;
  font-weight: 500;
  font-size: 1.2rem;
  color: #ecf0f1;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
}

.nav-links {
  list-style: none;
  padding: 0;
  margin: 20px 0;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.nav-links li {
  margin-bottom: 5px;
}

.nav-links li a {
  padding: 15px 20px;
  display: flex;
  align-items: center;
  cursor: pointer;
  transition: all 0.3s;
  color: #ecf0f1;
  text-decoration: none;
  width: 100%;
}

.nav-links li a:hover {
  background-color: #34495e;
  transform: translateX(5px);
}

.nav-links li a.active {
  background-color: #3498db;
  position: relative;
  transform: translateX(5px);
  border-radius: 0 4px 4px 0;
}

.nav-links li a.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  width: 4px;
  height: 100%;
  background-color: #2ecc71;
}

.nav-icon {
  width: 22px;
  height: 22px;
  margin-right: 12px;
  display: inline-block;
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
  opacity: 0.8;
  transition: opacity 0.3s;
}

.nav-links li a:hover .nav-icon,
.nav-links li a.active .nav-icon {
  opacity: 1;
}

.doc-icon {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23ecf0f1'%3E%3Cpath d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 1v5h5v10H6V3h7z'/%3E%3C/svg%3E");
}

.analysis-icon {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23ecf0f1'%3E%3Cpath d='M5 9.2h3V19H5V9.2zM10.6 5h2.8v14h-2.8V5zm5.6 8H19v6h-2.8v-6z'/%3E%3C/svg%3E");
}

.code-icon {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23ecf0f1'%3E%3Cpath d='M9.4 16.6L4.8 12l4.6-4.6L8 6l-6 6 6 6 1.4-1.4zm5.2 0l4.6-4.6-4.6-4.6L16 6l6 6-6 6-1.4-1.4z'/%3E%3C/svg%3E");
}

.config-icon {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23ecf0f1'%3E%3Cpath d='M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z'/%3E%3C/svg%3E");
}

.bottom-nav-item {
  margin-top: auto;
  border-top: 1px solid #34495e;
  padding-top: 15px;
  margin-top: 20px;
}

.bottom-nav-item a {
  display: flex;
  align-items: center;
  color: #ecf0f1;
  text-decoration: none;
}

.has-submenu {
  position: relative;
}

.nav-item {
  padding: 15px 20px;
  display: flex;
  align-items: center;
  cursor: pointer;
  transition: all 0.3s;
  color: #ecf0f1;
  text-decoration: none;
  width: 100%;
}

.nav-item:hover {
  background-color: #34495e;
  transform: translateX(5px);
}

.nav-item.active {
  background-color: #3498db;
  position: relative;
  transform: translateX(5px);
  border-radius: 0 4px 4px 0;
}

.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  width: 4px;
  height: 100%;
  background-color: #2ecc71;
}

.dropdown-icon {
  width: 22px;
  height: 22px;
  margin-left: 12px;
  display: inline-block;
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
  opacity: 0.8;
  transition: opacity 0.3s, transform 0.3s;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23ecf0f1'%3E%3Cpath d='M7.41 7.84L12 12.42l4.59-4.58L18 9.25l-6 6-6-6z'/%3E%3C/svg%3E");
}

.dropdown-icon.dropdown-open {
  transform: rotate(180deg);
}

.submenu {
  list-style: none;
  padding: 0 0 0 20px;
  margin: 5px 0;
  background-color: #243342;
  border-left: 1px solid #34495e;
  width: 100%;
}

.submenu li {
  margin-bottom: 5px;
}

.submenu li a {
  padding: 10px 15px;
  display: flex;
  align-items: center;
  cursor: pointer;
  transition: all 0.3s;
  color: #ecf0f1;
  text-decoration: none;
  width: 100%;
  font-size: 0.9rem;
}

.submenu li a:hover {
  background-color: #34495e;
  transform: translateX(5px);
}

.submenu li a.active {
  background-color: #3498db;
  position: relative;
  transform: translateX(5px);
  border-radius: 0 4px 4px 0;
}

.submenu li a.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  width: 4px;
  height: 100%;
  background-color: #2ecc71;
}
</style>

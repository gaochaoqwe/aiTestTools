<template>
  <div class="app-container">
    <!-- 侧边导航栏 -->
    <SideNavigation :activeTab="activeTab" @update:activeTab="activeTab = $event" />
    
    <!-- 主内容区域 -->
    <div class="main-content">
      <header>
        <h1>AI测试工具</h1>
      </header>

      <main>
        <router-view></router-view>
      </main>
      
      <footer>
        <p>AI测试工具 &copy; 2025</p>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import SideNavigation from './components/SideNavigation.vue';

// 当前激活的标签页
const activeTab = ref('document-review');
</script>

<style>
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: 'Arial', sans-serif;
  line-height: 1.6;
  color: #333;
  background-color: #f8f9fa;
}

.app-container {
  display: flex;
  min-height: 100vh;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  margin-left: 220px; /* 与侧边导航宽度一致 */
}

header {
  background-color: #3498db;
  background-image: linear-gradient(to right, #3498db, #2980b9);
  color: white;
  padding: 1.2rem;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

h1 {
  margin: 0;
  font-size: 1.8rem;
  letter-spacing: 1px;
  font-weight: 500;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
}

main {
  flex: 1;
  padding: 1.5rem;
  background-color: #f1f5f9;
  overflow: auto;
}

footer {
  background-color: #2c3e50;
  background-image: linear-gradient(to right, #2c3e50, #1a2530);
  color: white;
  text-align: center;
  padding: 1rem;
  font-size: 0.9rem;
  box-shadow: 0 -2px 4px rgba(0, 0, 0, 0.1);
}

section {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

h2 {
  color: #2c3e50;
  margin-bottom: 1rem;
  border-bottom: 1px solid #eee;
  padding-bottom: 0.5rem;
}

button {
  background-color: #3498db;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}

button:hover {
  background-color: #2980b9;
}

button:disabled {
  background-color: #bdc3c7;
  cursor: not-allowed;
}

.file-input {
  display: none;
}

.file-label {
  display: inline-block;
  background-color: #3498db;
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.file-label:hover {
  background-color: #2980b9;
}

.upload-area {
  border: 2px dashed #bdc3c7;
  border-radius: 4px;
  padding: 2rem;
  text-align: center;
  margin-bottom: 1rem;
  transition: border-color 0.3s;
}

.upload-area:hover {
  border-color: #3498db;
}

.upload-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  color: #bdc3c7;
}
</style>

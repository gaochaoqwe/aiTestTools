<template>
  <div class="code-review">
    <h2>代码审查</h2>
    <div class="coming-soon">
      <div class="icon">💻</div>
      <h3>功能开发中</h3>
      <p>代码审查功能正在开发中，敬请期待！</p>
    </div>
  </div>
</template>

<script setup>
// 这里将来会添加代码审查功能的逻辑
</script>

<style scoped>
.code-review {
  width: 100%;
  padding: 20px;
}

h2 {
  color: #2c3e50;
  margin-bottom: 20px;
}

.coming-soon {
  background-color: #fff;
  border-radius: 6px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  padding: 50px 20px;
  text-align: center;
  color: #7f8c8d;
}

.icon {
  font-size: 5rem;
  margin-bottom: 20px;
}

h3 {
  font-size: 1.5rem;
  margin-bottom: 15px;
}

p {
  font-size: 1rem;
}
</style>

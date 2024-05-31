<script setup>
import {ref} from 'vue'
const activeName = ref('first')
import user from './components/user/index.vue'
import dataCom from './components/data/index.vue'
</script>

<template>
  <el-tabs v-model="activeName" class="demo-tabs" >
    <el-tab-pane label="数据管理" name="first">
      <data-com></data-com>
    </el-tab-pane>
    <el-tab-pane label="用户管理" name="second"><user></user></el-tab-pane>
  </el-tabs>
</template>
<style lang="scss" scoped>
.demo-tabs{
  padding: 20px;
}
:deep(.el-tabs__nav){
  font-size: 30px;
  width: 100%;
  justify-content: space-around;
}
:deep(.el-tabs__item){
  font-size: 30px;
}
:deep(.el-tabs__active-bar){
  display: none;
}
:deep(.el-tabs__nav-wrap:after){
  display: none;
}

</style>

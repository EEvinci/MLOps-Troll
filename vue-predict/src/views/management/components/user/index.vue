<script setup>
import {ref} from 'vue'
import addEdit from './addEdit.vue'
import page from '@/components/Pagination/index.vue'
import {deleteApi, getUsersApi, searchApi} from "@/api/login.js";
import {ElMessage, ElMessageBox} from "element-plus";
const formInline = ref({
  user: '',})
const total = ref(0)
const queryParams = ref({
  page: 1,
  per_page: 10,
})
const tableData =ref([])
const getList = () => {
  getUsersApi(queryParams.value).then(res => {
    console.log(res)
    total.value =res.total
    tableData.value = res.list
  })
}
getList()
const search = ()=> {
  if (formInline.value.user) {
    searchApi(formInline.value.user).then(res => {
      console.log('resss',res)
      if(res.code === 0 ){
        ElMessage.error('未找到该用户')
        return
      }
      total.value = 1
      tableData.value = [res.user]
    })
  } else {
    queryParams.value.page = 1
    getList()
  }
}



const addEditRef = ref(null)
const openDia = (isAdd,row) => {
  console.log('aaaa',addEditRef.value)
  addEditRef.value.open(isAdd,row)
}
const handleDelete = (row) => {
  ElMessageBox.confirm(`正在删除用户：${row.username}，确认删除？`, "提示", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning"
  }).then(() => {
    deleteApi(row.username).then(() => {
      ElMessage.success("删除成功")
      getList()
    })
  })
}
</script>

<template>
  <div class="tabContainer">
    <el-form :inline="true" :model="formInline" class="demo-form-inline" style="display: flex;justify-content: center">
      <el-form-item label="用户名">
        <el-input v-model="formInline.user" placeholder="请输入用户名"  />
      </el-form-item>


      <el-form-item>
        <el-button type="primary" @click="search">查询</el-button>
      </el-form-item>
    </el-form>
    <el-button type="primary" @click="openDia(true,null)" plain style="margin-bottom: 10px">新增</el-button>
    <el-table :data="tableData" style="width: 100%">
      <el-table-column  prop="username" label="用户名"  />
      <el-table-column prop="role" label="角色" >
        <template v-slot="{row}">
          {{row.role === 'admin' ? '管理员' : '用户'}}
        </template>
      </el-table-column>
      <el-table-column label="操作">
        <template v-slot="{row}">
          <el-button link type="primary" size="small" @click="openDia(false,row)">
            编辑
          </el-button>
          <el-button link type="primary" size="small" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <page  v-show="total > 0"
           style="display: flex;justify-content: center"
           :total="total"
           v-model:page="queryParams.page"
           v-model:limit="queryParams.per_page"
           @pagination="getList"></page>
    <add-edit ref="addEditRef" @refresh="getList"></add-edit>
  </div>

</template>

<style scoped lang="scss">
:deep(.demo-form-inline){
  display: flex;
  align-items: center;
}
</style>

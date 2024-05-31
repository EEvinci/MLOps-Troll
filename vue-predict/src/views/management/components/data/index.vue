<script setup>
import {ref} from 'vue'
import addEdit from './addEdit.vue'
import page from '@/components/Pagination/index.vue'
import {deleteDatasetApi, getDatasApi, searchDatasetApi} from "@/api/login.js";
import {ElMessage, ElMessageBox} from "element-plus";
const formInline = ref({
  user: '',
  id:''
})
const total = ref(0)
const queryParams = ref({
  page: 1,
  per_page: 10,
})
const tableData =ref([])
const getList = () => {
  getDatasApi(queryParams.value).then(res => {
    console.log(res)
    total.value =res.total
    tableData.value = res.data
  })
}
getList()
const search = ()=> {
  if (formInline.value.user || formInline.value.id) {
    queryParams.value = {
      page: 1,
      per_page: 10,
    }
    const params = {
      ...queryParams.value,
      label:formInline.value.user,
      dataset_id:formInline.value.id
    }
    searchDatasetApi(params).then(res => {
      console.log('resss',res)
      if(res.code === 0 ){
        ElMessage.error('未找到内容')
        return
      }
      total.value = res.total
      tableData.value = res.data
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
  ElMessageBox.confirm(`正在删除一条数据，确认删除？`, "提示", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning"
  }).then(() => {
    deleteDatasetApi(row.id).then(() => {
      ElMessage.success("删除成功")
      getList()
    })
  })
}


const formatDate = (dateString)=> {
  const date = new Date(dateString*1000);
  console.log('resss',date)
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  const seconds = String(date.getSeconds()).padStart(2, '0');

  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
}
</script>

<template>
  <div class="tabContainer">
    <el-form :inline="true" :model="formInline" class="demo-form-inline" style="display: flex;justify-content: center">
      <el-form-item label="标签">
        <el-input v-model="formInline.user" placeholder="请输入标签"  />
      </el-form-item>
      <el-form-item label="id">
        <el-input v-model="formInline.id" placeholder="请输入id"  />
      </el-form-item>


      <el-form-item>
        <el-button type="primary" @click="search">查询</el-button>
      </el-form-item>
    </el-form>
    <el-button type="primary" @click="openDia(true,null)" plain style="margin-bottom: 10px">新增</el-button>
    <el-table :data="tableData" style="width: 100%">
      <el-table-column  prop="text" label="文本"  />
      <el-table-column  prop="label" label="标签"  />
      <el-table-column prop="source" label="来源" >
      </el-table-column>
      <el-table-column prop="create_time" label="创建时间" >
        <template v-slot="{row}">
          {{formatDate(row.create_time)}}
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

<style scoped>

</style>

<script setup>
import {ref} from 'vue'
import {Lock, User} from "@element-plus/icons-vue";
import {createDatasetApi, updateDatasetApi} from "@/api/login.js";
import {ElMessage} from "element-plus";
const emit = defineEmits(['refresh'])
const dialogVisible = ref(false)
const title = ref('')
const isAdd = ref(false)
const formData = ref({
  text:'',
  label:'',
  source:''
})
const open = (add,row)=>{
  isAdd.value = !!add
  title.value = add ? '新增数据' : '编辑数据'
  if(row) formData.value = row
  dialogVisible.value = true
}
const close = ()=>{
  formData.value = {
    text:'',
    label:'',
    source:''
  }
  dialogVisible.value = false
}
const confirm = ()=>{
  // if(!formData.value.text) return ElMessage.error('请输入用户名')
  // if(!formData.value.label) return ElMessage.error('请输入密码')
  if(isAdd.value){
    createDatasetApi(formData.value).then(res=>{
      console.log('ress',res)
        ElMessage.success('新增成功')
        emit('refresh')
        close()

    })
  }else{
    updateDatasetApi(formData.value.id,formData.value).then(res=>{
      ElMessage.success('编辑成功',formData.value.username)
      emit('refresh')
      close()
    })
  }
}
defineExpose({
  // 将想要暴露的属性和方法名称
  open
})
</script>

<template>
  <el-dialog
      v-model="dialogVisible"
      :title="title"
      width="500"

  >
    <el-form ref="loginRef" :model="formData"  class="login-form" label-width="70px" label-position="left">
      <el-form-item prop="text" label="文本">
        <el-input
            v-model="formData.text"
            type="text"

            auto-complete="off"

        >

        </el-input>
      </el-form-item>
      <el-form-item prop="label" label="标签">
        <el-input
            v-model="formData.label"
            type="text"

        >
        </el-input>
      </el-form-item>
      <el-form-item prop="source"  label="来源">
         <el-input
          v-model="formData.source"
          type="text"

      >
      </el-input>

      </el-form-item>


    </el-form>
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="close">取消</el-button>
        <el-button type="primary" @click="confirm">
          确认
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<style scoped>

</style>

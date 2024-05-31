<script setup>
import {ref} from 'vue'
import {Lock, User} from "@element-plus/icons-vue";
import {createApi, updateApi} from "@/api/login.js";
import {ElMessage} from "element-plus";
const emit = defineEmits(['refresh'])
const dialogVisible = ref(false)
const title = ref('')
const isAdd = ref(false)
const formData = ref({
  username:'',
  password:'',
  role:'user'
})
const open = (add,row)=>{
  isAdd.value = !!add
  title.value = add ? '新增用户' : '编辑用户'
  if(row) formData.value = row
  dialogVisible.value = true
}
const close = ()=>{
  formData.value = {
    username:'',
    password:'',
    role:'user'
  }
  dialogVisible.value = false
}
const confirm = ()=>{
  if(!formData.value.username) return ElMessage.error('请输入用户名')
  if(!formData.value.password) return ElMessage.error('请输入密码')
  if(isAdd.value){
    createApi(formData.value).then(res=>{
      console.log('ress',res)
      
        ElMessage.success('新增成功')
        emit('refresh')
        close()

    })
  }else{
    updateApi(formData.value.username,formData.value).then(res=>{
      ElMessage.success('编辑成功')
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
      <el-form-item prop="username" label="用户名">
        <el-input
            v-model="formData.username"
            type="text"

            auto-complete="off"
            placeholder="账号"
            :icon="User"
            :disabled="!isAdd"
        >

        </el-input>
      </el-form-item>
      <el-form-item prop="password" label="密码">
        <el-input
            v-model="formData.password"
            type="password"

            auto-complete="off"
            placeholder="密码"
            :icon="Lock"
            show-password
        >
        </el-input>
      </el-form-item>
      <el-form-item prop="code"  label="角色">
        <el-select v-model="formData.role">
          <el-option label="管理员" value="admin"></el-option>
          <el-option label="用户" value="user"></el-option>
        </el-select>

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

<style scoped lang="scss">

</style>

<script setup>
import {ref,onMounted} from 'vue'
import {getModelsApi, predictApi} from "@/api/login.js";
import {useRouter} from "vue-router";
import {ElMessage} from "element-plus";
const router = useRouter();
const toManagement = ()=>{
  router.push('/management')

}

const loading = ref(false)
const queryForm = ref({
  model_name: '',
  model_version: '',
  text:''
})
const modelOpt = ref([])

const versionOpt =ref([])
const getModels = ()=>{
  getModelsApi().then(res=>{

    modelOpt.value = res
    console.log(res,modelOpt.value)
  })
}
getModels()
const modelChange = (item)=>{
  console.log(item,111)
  versionOpt.value = []
  queryForm.value.model_version = ''
  const obj = modelOpt.value.find(i=>i.name === item)
  versionOpt.value = obj.versions

}
const predict =ref('')
const handleClick = ()=>{

  if(!queryForm.value.text) return ElMessage.error('请输入文本')
  if(!queryForm.value.model_name) return ElMessage.error('请选择模型')
  if(!queryForm.value.model_version) return ElMessage.error('请选择版本')
  loading.value = true
  predictApi(queryForm.value).then(res=>{
    loading.value = false
   if(res.label === 1){
     predict.value = '杠精言论'}
   else{
      predict.value = '正常言论'
   }
  })
}
const isAdmin = ref(false)
isAdmin.value = localStorage.getItem('role') === 'admin'


</script>

<template>
  <div class="container">
    <div class="title">
      杠精言论识别检测系统
    </div>
    <div class="cardContainer">
      <div class="model">当前模型: <el-select
          v-model="queryForm.model_name"
          placeholder="请选择"
          size="large"
          style="width: 240px"
          @change="modelChange"
      >
        <el-option
            v-for="item in modelOpt"
            :key="item.name"
            :label="item.name"
            :value="item.name"
        />
      </el-select> 版本： <el-select
          v-model="queryForm.model_version"
          placeholder="请选择"
          size="large"
          style="width: 240px"
      >
        <el-option
            v-for="item in versionOpt"
            :key="item.version"
            :label="item.version"
            :value="item.version"
        />
      </el-select></div>
      <el-input
          class="userInput"
          v-model="queryForm.text"
          style="width: 100%"
          :rows="2"
          type="textarea"
          placeholder="请输入"
      />
      <div class="btn"  @click="handleClick">预测</div>
      <el-card class="result" v-loading="loading">
        <template #header>
          <div class="card-header">
            <span>预测结果</span>
          </div>
        </template>
        <div class="p-res" >
         {{predict}}
        </div>


      </el-card>
    </div>
    <el-button @click="toManagement" class="changeBtn" v-show="isAdmin">切换</el-button>
  </div>


</template>
<style lang="scss" scoped>
.title{
  font-size: 30px;
  font-weight: bold;
  width: 100%;
  text-align: center;
  padding-top: 30px;
}
.container{
  position: relative;
  height: 100%;
  background: #eeede3;
  .changeBtn{
    position: absolute;
    top:20px;
    right: 20px;
  }
}
.cardContainer{
  padding: 30px;
  height: calc(100% - 115px);
  width: 700px;
  border: 1px solid #d0cec2;
  margin: 30px auto 0;
  border-radius: 18px;
}
.model{
  text-align: center;
  margin-bottom: 30px;
}
.btn{
  background: #bf5f3c;
  color: #fff;
  text-align: center;
  border-radius: 4px;
  margin: 10px;
  padding: 5px;
  cursor: pointer;
}
.result{
  margin:0 10px;
  height: calc(100% - 150px);
  .card-header{
    text-align: center;
  }
}
:deep(.el-card__header) {
  padding: 5px 0;
}
:deep(.el-card__body){
  height: calc(100% - 30px);
  background: #eed7d8;
  overflow-y: auto;
  color: #b84e45;
}
</style>

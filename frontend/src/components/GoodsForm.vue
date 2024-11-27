<template>
  <el-form :model="form" label-width="120px">
    <el-form-item label="商品名称">
      <el-input v-model="form.goods_name" />
    </el-form-item>
    <el-form-item label="商品卖点">
      <el-input v-model="form.goods_point" type="textarea" />
    </el-form-item>
    <el-form-item label="活动信息">
      <el-input v-model="form.activity" type="textarea" />
    </el-form-item>
    <el-form-item label="优惠信息">
      <el-input v-model="form.benefit" type="textarea" />
    </el-form-item>
    <el-form-item label="目标人群">
      <el-input v-model="form.target_people" />
    </el-form-item>
    <el-form-item label="用户痛点">
      <el-input v-model="form.user_point" type="textarea" />
    </el-form-item>
    <el-form-item label="口播风格">
      <el-input v-model="form.style" />
    </el-form-item>
    <el-form-item>
      <el-button type="primary" @click="generateContent" :loading="loading">
        生成口播内容
      </el-button>
    </el-form-item>
  </el-form>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../services/api'

const emit = defineEmits(['content-generated'])

const loading = ref(false)
const form = ref({
  goods_name: '女士拖鞋舒适鞋日常步行',
  goods_point: '1.引人注目的色块图案设计，时尚大方\n2.柔软舒适的鞋底，走路无压力\n3.防滑耐磨的材质，安全可靠\n4.轻便易携，适合日常使用',
  activity: '618大促,春季焕新',
  benefit: '买二送一，直播间优惠价格',
  target_people: '25-45岁的年轻女性',
  user_point: '1.长时间走路脚会疼\n2.想要既舒适又时尚的鞋子\n3.担心鞋子容易磨损',
  style: '温柔亲切'
})

const generateContent = async () => {
  if (!form.value.goods_name) {
    ElMessage.warning('请至少输入商品名称')
    return
  }

  try {
    loading.value = true
    // const content = await api.generateContent(form.value)
    const content = '亲爱的女士们，欢迎来到我们的直播间。'
    emit('content-generated', content)
    ElMessage.success('生成成功')
  } catch (error) {
    console.error('生成内容失败:', error)
    ElMessage.error('生成内容失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.goods-form {
  padding: 20px;
  background: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);
}
</style> 
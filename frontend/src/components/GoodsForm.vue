<template>
  <el-card class="goods-form-card">
    <template #header>
      <div class="form-header">
        <span>商品信息</span>
      </div>
    </template>
    
    <el-form :model="form" label-width="100px" class="goods-form">
      <el-form-item label="商品名称">
        <el-input 
          v-model="form.goods_name" 
          placeholder="请输入商品名称"
          :rows="1"
        />
      </el-form-item>
      
      <el-form-item label="商品卖点">
        <el-input 
          v-model="form.goods_point" 
          type="textarea" 
          :rows="4"
          placeholder="请输入商品卖点"
        />
      </el-form-item>
      
      <el-form-item label="活动信息">
        <el-input 
          v-model="form.activity" 
          type="textarea" 
          :rows="1"
          placeholder="请输入活动信息"
        />
      </el-form-item>
      
      <el-form-item label="优惠信息">
        <el-input 
          v-model="form.benefit" 
          type="textarea" 
          :rows="2"
          placeholder="请输入优惠信息"
        />
      </el-form-item>
      
      <el-form-item label="目标人群">
        <el-input 
          v-model="form.target_people" 
          placeholder="请输入目标人群"
        />
      </el-form-item>
      
      <el-form-item label="用户痛点">
        <el-input 
          v-model="form.user_point" 
          type="textarea" 
          :rows="3"
          placeholder="请输入用户痛点"
        />
      </el-form-item>
      
      <el-form-item label="口播风格">
        <el-radio-group 
          v-model="form.style" 
          class="style-radio-group"
          name="style"
        >
          <div 
            v-for="(style, index) in styleOptions" 
            :key="index"
            class="style-option"
          >
            <el-radio :label="index + 1">
              {{ style }}
            </el-radio>
          </div>
        </el-radio-group>
      </el-form-item>
      <el-form-item label="SSML">
        <el-switch 
          v-model="form.is_ssml_open" 
          active-text="开"
          inactive-text="关"
        />
      </el-form-item>
      <el-form-item class="submit-item">
        <el-button 
          type="primary" 
          @click="generateContent" 
          :loading="loading"
          class="submit-btn"
        >
          生成口播内容
        </el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../services/api'

const emit = defineEmits(['content-generated'])

const loading = ref(false)
const styleOptions = [
  '正常风格',
  '董宇辉',
  '李佳琦'
]
const form = ref({
  goods_name: '女士拖鞋舒适鞋日常步行',
  goods_point: '1.引人注目的色块图案设计，时尚大方\n2.柔软舒适的鞋底，走路无压力\n3.防滑耐磨的材质，安全可靠\n4.轻便易携，适合日常使用',
  activity: '618大促,春季焕新',
  benefit: '买二送一，直播间优惠价格',
  target_people: '25-45岁的年轻女性',
  user_point: '1.长时间走路脚会疼\n2.想要既舒适又时尚的鞋子\n3.担心鞋子容易磨损',
  style: 1,
  is_ssml_open: false,
})

const generateContent = async () => {
  if (!form.value.goods_name) {
    ElMessage.warning('请至少输入商品名称')
    return
  }

  try {
    loading.value = true
    const response = await api.generateContent(form.value)
    // 将所有 content 按 rank 排序后拼接
    // 再用变量记住每个 chunk 和对应的 rank
    const chunks = response.contents

    const content = chunks
      .sort((a, b) => a.rank - b.rank)
      .map(item => ({
        content: item.content,
        rank: item.rank,
        continuity_sentences: item.continuity_sentences?.content || ''
      }))

    emit('content-generated', { content })
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
.goods-form-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.08);
  transition: all 0.3s ease;
  min-height: calc(100vh - 108px);
  height: auto;
  display: flex;
  flex-direction: column;
  margin-bottom: 24px;
}

.goods-form-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0,0,0,0.12);
}

.form-header {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
  flex-shrink: 0;
  padding: 16px 20px;
}

.goods-form {
  padding: 20px 0;
  overflow-y: auto;
  flex: 1;
  padding-right: 16px;
  margin-right: -16px;
  min-height: 400px;
}

:deep(.el-form-item) {
  margin-bottom: 18px;
  flex-shrink: 0;
}

:deep(.el-input__wrapper),
:deep(.el-textarea__inner) {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  transition: all 0.3s ease;
}

:deep(.el-input__wrapper:hover),
:deep(.el-textarea__inner:hover) {
  box-shadow: 0 4px 12px rgba(64,158,255,0.1);
}

:deep(.el-input__wrapper:focus-within),
:deep(.el-textarea__inner:focus) {
  box-shadow: 0 4px 12px rgba(64,158,255,0.15);
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: #606266;
}

.submit-btn {
  width: auto;
  min-width: 160px;
  padding: 12px 32px;
  font-size: 14px;
  font-weight: 500;
  background: linear-gradient(90deg, #409EFF 0%, #36cfc9 100%);
  border: none;
  transition: all 0.3s ease;
  margin-top: 40px;
}

.submit-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(64,158,255,0.3);
}

.goods-form::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.goods-form::-webkit-scrollbar-thumb {
  border-radius: 3px;
  background: #c0c4cc;
}

.goods-form::-webkit-scrollbar-track {
  border-radius: 3px;
  background: #f5f7fa;
}

.goods-form :deep(.el-form-item:last-child) {
  margin-bottom: 40px;
}

.style-radio-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: flex-start;
}

.style-option {
  padding: 12px 16px;
  border-radius: 8px;
  background: #f5f7fa;
  transition: all 0.3s ease;
  cursor: pointer;
  width: fit-content;
  min-width: 200px;
}

.style-option:hover {
  background: #ecf5ff;
}

:deep(.el-radio) {
  width: 100%;
  margin-right: 0;
  height: auto;
  display: flex;
  align-items: flex-start;
}

:deep(.el-radio__label) {
  white-space: normal;
  line-height: 1.5;
  padding-left: 12px;
  flex: 1;
}

:deep(.el-radio__input) {
  margin-top: 2px;
}

/* 选中状态的样式 */
:deep(.el-radio.is-checked) + .style-option {
  background: #ecf5ff;
  border-color: #409EFF;
}

/* 在小屏幕下调整间距 */
@media screen and (max-height: 768px) {
  .goods-form-card {
    min-height: auto;
    margin-bottom: 16px;
  }

  .goods-form {
    padding: 16px 0;
  }

  :deep(.el-form-item) {
    margin-bottom: 14px;
  }

  .style-option {
    padding: 8px;
  }
}

.submit-item {
  text-align: center;
}
</style> 
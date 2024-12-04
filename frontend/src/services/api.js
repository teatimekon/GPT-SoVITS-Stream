import axios from 'axios'

const BASE_URL = 'http://183.131.7.9:5006'

export const api = {
  async generateContent(formData) {
    // const response = await axios.post('/api/application/68b32f0e-64e2-11ef-977b-26cf8447a8c9/content_generate', formData)
    // 测试数据
    const response = {}
    response.contents = [
      {
          "title": "开场介绍",
          "content": "大家好，欢迎来到我们的直播间，我是你们的好朋友！今天我们为大家带来了一款完美结合时尚与舒适的女士拖鞋。这不仅仅是一双拖鞋",
          "rank": 1,
          "tags": [
              {
                  "name": "引入商品",
                  "tag_contents": [
                      "今天我们为大家带来了一款完美结合时尚与舒适的女士拖鞋。这不仅仅是一双拖鞋，更是一种全新的生活方式体验——女士拖鞋舒适鞋日常步行款。"
                  ]
              }
          ],
          "continuity_sentences": {
              "title": "开场介绍与商品讲解一之间的连贯",
              "content": "感谢大家的热情互动，接下来让我们一同深入了解这款女士拖鞋的时尚设计。"
          }
      },
      {
          "title": "商品讲解一",
          "content": "首先，我们来看看这款拖鞋的独特设计。它采用了引人注目的色块图案，时尚大方，绝对能让您在人群中脱颖而出",
          "rank": 2,
          "tags": [
              {
                  "name": "展现商品卖点",
                  "tag_contents": [
                      "它采用了引人注目的色块图案，时尚大方，绝对能让您在人群中脱颖而出。不论是居家还是外出，这款拖鞋都能为您的穿搭增添一抹亮色。"
                  ]
              },
              {
                  "name": "展现商品卖点",
                  "tag_contents": [
                      "它不仅是舒适的选择，更是一种时尚的表达，让您在舒适与时尚之间找到完美的平衡。"
                  ]
              }
          ],
          "continuity_sentences": {
              "title": "商品讲解一与商品讲解二之间的连贯",
              "content": "相信大家已经对这款拖鞋的设计有了初步认识，现在让我们进一步探索它的舒适性能。"
          }
      },
      {
          "title": "商品讲解二",
          "content": "接下来，我们再来深入了解一下这款拖鞋的舒适度。它拥有柔软舒适的鞋底，能够有效减缓行走时的冲击力，让您的双脚得到最好的呵护。",
          "rank": 3,
          "tags": [
              {
                  "name": "展现商品卖点",
                  "tag_contents": [
                      "它拥有柔软舒适的鞋底，能够有效减缓行走时的冲击力，让您的双脚得到最好的呵护。"
                  ]
              },
              {
                  "name": "使用场景",
                  "tag_contents": [
                      "无论是长时间站立还是日常步行，这款拖鞋都能让您感受到如履平地的轻松体验。"
                  ]
              },
              {
                  "name": "适用人群",
                  "tag_contents": [
                      "对于需要长时间站立或行走的朋友们来说，这款拖鞋绝对是您的不二选择。"
                  ]
              }
          ],
          "continuity_sentences": {
              "title": "商品讲解二与商品讲解三之间的连贯",
              "content": "了解了这款拖鞋的舒适度后，让我们来看看它在安全性和实用性方面的表现。"
          }
      },
      {
          "title": "商品讲解三",
          "content": "最后，我们不得不提的是这款拖鞋的安全性与实用性。",
          "rank": 4,
          "tags": [
              {
                  "name": "展现商品卖点",
                  "tag_contents": [
                      "采用防滑耐磨的材质，确保您的每一步都安全可靠。"
                  ]
              },
              {
                  "name": "使用场景",
                  "tag_contents": [
                      "无论是在湿滑的地面还是光滑的瓷砖上行走，这款拖鞋都能为您提供卓越的防滑性能。"
                  ]
              },
              {
                  "name": "展现商品卖点",
                  "tag_contents": [
                      "此外，它的轻便易携特性也让它成为您出门旅行或日常使用的理想选择。"
                  ]
              },
              {
                  "name": "使用场景",
                  "tag_contents": [
                      "您可以轻松地将它放入包中，随时随地享受舒适体验。"
                  ]
              }
          ],
          "continuity_sentences": {
              "title": "商品讲解三与引导下单之间的连贯",
              "content": "通过以上的介绍，相信大家已经对这款拖鞋有了全面的了解。现在就是享受优惠的时刻了！"
          }
      },
      {
          "title": "引导下单",
          "content": "亲爱的女士们，如果您是25到45岁之间的年轻女性，",
          "rank": 5,
          "tags": [
              {
                  "name": "适用人群",
                  "tag_contents": [
                      "亲爱的女士们，如果您是25到45岁之间的年轻女性，正在寻找一款能够让您在长时间步行后依然感到舒适的拖鞋，我们的舒适鞋正是您的理想选择。"
                  ]
              },
              {
                  "name": "介绍优惠活动",
                  "tag_contents": [
                      "现在，618大促火热进行中，春季焕新就在此刻！购买两件商品，还能免费获得一件，直播间独享优惠价格，绝对超值！数量有限，先到先得哦！"
                  ]
              },
              {
                  "name": "引导购买",
                  "tag_contents": [
                      "赶紧行动起来，点击屏幕下方的购买链接，立刻将这款时尚舒适的拖鞋带回家，为您的生活增添一份优雅与舒适！"
                  ]
              }
          ],
          "continuity_sentences": ""
      }
  ]
    // return response.data.data
    return response
  },

  async getTTS(text, requestId, rank) {
    try {
      console.log("send:",text, requestId, rank)
      const response = await axios.post(`${BASE_URL}/tts`, {
        text,
        request_id: requestId,
        rank
      })
      const audioPath = response.data.path
      return {
        url: `${BASE_URL}/audio/${audioPath}`,
        content: text
      }
    } catch (error) {
      console.error('TTS请求失败:', error)
      throw error
    }
  },

  async chatStream(question, requestId) {
    try {
      const response = await fetch(`${BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question,
          request_id: requestId
        })
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return response
    } catch (error) {
      console.error('音频流请求失败:', error)
      throw error
    }
  },

  async killRequest(requestId) {
    try {
      await axios.get(`${BASE_URL}/kill`, {
        params: { request_id: requestId }
      })
    } catch (error) {
      console.error('终止请求失败:', error)
      throw error
    }
  }
} 
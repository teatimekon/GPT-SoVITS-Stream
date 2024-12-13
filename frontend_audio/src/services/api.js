import axios from 'axios'

const BASE_URL = 'http://183.131.7.9:5011'
const Echominic_URL = 'http://183.131.7.9:5000'
export const api = {
    async generateContent(formData) {
        // const response = await axios.post('/api/application/68b32f0e-64e2-11ef-977b-26cf8447a8c9/content_generate', formData)
        // 测试数据
        const response = {}
        response.contents =  [{
            "title": "开场介绍",
            "content": "大家好，欢迎来到我们的直播间，我是你们的好朋友！今天为大家带来的不仅仅是一双鞋，而是一种全新的时尚体验——我们的女士拖鞋舒适鞋日常步行！这可不是普通的拖鞋，它将前沿的设计与卓越的舒适感相结合，让您的每一步都如履云端。",
            "rank": 1,
            "tags": [
                {
                    "name": "引入商品",
                    "tag_contents": [
                        "今天为大家带来的不仅仅是一双鞋，而是一种全新的时尚体验——我们的女士拖鞋舒适鞋日常步行！这可不是普通的拖鞋，它将前沿的设计与卓越的舒适感相结合，让您的每一步都如履云端。"
                    ]
                }
            ],
            "continuity_sentences": {
                "title": "商品讲解一",
                "content": "感谢您的提问，相信大家对这款拖鞋的设计已经有了更深入的了解。接下来，让我们继续探索这款拖鞋的更多魅力。"
            }
        },
        {
            "title": "商品讲解一",
            "content": "首先，让我们来聊聊这款拖鞋的设计亮点。女士们，准备好为您的步伐注入一抹时尚的亮色了吗？这款拖鞋采用引人注目的色块图案，结合充满活力和大胆的色彩组合，为任何服装增添现代和时尚的色彩。在不同的色调之间创造一种视觉上吸引人的对比，对那些喜欢用自己的时尚选择来表达自己的人来说，这是完美的选择。无论是搭配休闲牛仔裤，还是夏日的飘逸长裙，这款拖鞋都能让您的整体造型瞬间提升，为您的外表增添一抹亮色。",
            "rank": 2,
            "tags": [
                {
                    "name": "展现商品卖点",
                    "tag_contents": [
                        "这款拖鞋采用引人注目的色块图案，结合充满活力和大胆的色彩组合，为任何服装增添现代和时尚的色彩。在不同的色调之间创造一种视觉上吸引人的对比，对那些喜欢用自己的时尚选择来表达自己的人来说，这是完美的选择。"
                    ]
                },
                {
                    "name": "使用场景",
                    "tag_contents": [
                        "无论是搭配休闲牛仔裤，还是夏日的飘逸长裙，这款拖鞋都能让您的整体造型瞬间提升，为您的外表增添一抹亮色。"
                    ]
                }
            ],
            "continuity_sentences": {
                "title": "商品讲解二",
                "content": "希望我们的回答能帮助到您，现在让我们一起看看这款拖鞋在不同场合中的表现吧。"
            }
        },
        {
            "title": "商品讲解二",
            "content": "接下来，我们来看看这款拖鞋的适用场合。这款百搭设计的拖鞋可以在各种场合佩戴。无论是悠闲的居家时光，还是轻松的外出购物，它都能为您提供无与伦比的舒适感。同时，它也能在稍显正式的场合中不失风采，成为您风格的绝佳补充。对于那些追求时尚和舒适的女士来说，这款拖鞋绝对是您时尚收藏中的必备单品。",
            "rank": 3,
            "tags": [
                {
                    "name": "使用场景",
                    "tag_contents": [
                        "这款百搭设计的拖鞋可以在各种场合佩戴。无论是悠闲的居家时光，还是轻松的外出购物，它都能为您提供无与伦比的舒适感。同时，它也能在稍显正式的场合中不失风采，成为您风格的绝佳补充。"
                    ]
                },
                {
                    "name": "介绍适用人群",
                    "tag_contents": [
                        "对于那些追求时尚和舒适的女士来说，这款拖鞋绝对是您时尚收藏中的必备单品。"
                    ]
                }
            ],
            "continuity_sentences": {
                "title": "商品讲解三",
                "content": "听到您的反馈真是太棒了，现在我们来聊聊这款拖鞋在舒适性上的非凡表现。"
            }
        },
        {
            "title": "商品讲解三",
            "content": "最后，这款女士拖鞋在舒适性上的表现同样出色。我们的拖鞋专为日常步行设计，舒适又时尚。无论您在家中放松，还是在街头漫步，它都能为您提供柔软的步行体验，让每一步都轻松自在。它不仅容易与其他衣橱必备单品混搭，而且其时尚的设计让您无论在何种场合都能保持自信。",
            "rank": 4,
            "tags": [
                {
                    "name": "展现商品卖点",
                    "tag_contents": [
                        "我们的拖鞋专为日常步行设计，舒适又时尚。无论您在家中放松，还是在街头漫步，它都能为您提供柔软的步行体验，让每一步都轻松自在。它不仅容易与其他衣橱必备单品混搭，而且其时尚的设计让您无论在何种场合都能保持自信。"
                    ]
                }
            ],
            "continuity_sentences": {
                "title": "引导下单",
                "content": "感谢您耐心聆听这些介绍，相信您已经迫不及待想要入手了。让我们来看看如何用最优惠的方式将它带回家吧！"
            }
        },
        {
            "title": "引导下单",
            "content": "现在，我知道您们一定迫不及待想要拥有这样一双完美的拖鞋了。好消息是，今天我们直播间有特别优惠，正值618大促，春季焕新活动，买二送一的超值优惠等您来享受，直播间更有专属低价，让您以最划算的价格焕新整个春天！快来为您的鞋柜增添这一款时尚而实用的单品吧！点击屏幕下方的购买链接，立刻将它带回家。数量有限，先到先得哦！赶紧行动起来，让我们一起走出自信，走出风采！",
            "rank": 5,
            "tags": [
                {
                    "name": "引导购买",
                    "tag_contents": [
                        "现在，我知道您们一定迫不及待想要拥有这样一双完美的拖鞋了。好消息是，今天我们直播间有特别优惠，正值618大促，春季焕新活动，买二送一的超值优惠等您来享受，直播间更有专属低价，让您以最划算的价格焕新整个春天！快来为您的鞋柜增添这一款时尚而实用的单品吧！点击屏幕下方的购买链接，立刻将它带回家。数量有限，先到先得哦！赶紧行动起来，让我们一起走出自信，走出风采！"
                    ]
                },
                {
                    "name": "介绍优惠活动",
                    "tag_contents": [
                        "今天我们直播间有特别优惠，正值618大促，春季焕新活动，买二送一的超值优惠等您来享受，直播间更有专属低价，让您以最划算的价格焕新整个春天！"
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

    async chatStream(question, requestId, goodsInfo) {
        try {
            const response = await fetch(`${BASE_URL}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    question,
                    request_id: requestId,
                    goods_info: goodsInfo
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
    },

    async uploadImage(formData) {
        try {
            const response = await axios.post(`${Echominic_URL}/upload_image`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            });
            return response.data;
        } catch (error) {
            console.error('上传图片失败:', error);
            throw error;
        }
    },

    async uploadAudio(formData) {
        try {
            const response = await axios.post(`${Echominic_URL}/upload_audio`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            });
            return response.data;
        } catch (error) {
            console.error('上传音频失败:', error);
            throw error;
        }
    },

    async generateVideo(formData) {
        try {
            const response = await axios.post(`${Echominic_URL}/generate_video`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                },
                
            });
            const videoPath = response.data.video_url

            return {
                url: `${Echominic_URL}/video/${videoPath}`,
              }
        } catch (error) {
            console.error('生成视频失败:', error);
            throw error;
        }
    },
}


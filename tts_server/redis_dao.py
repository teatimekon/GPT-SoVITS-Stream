import redis
import json

class RedisManager:
    def __init__(self, redis_config):
        self.redis_config = redis_config
        self.conn = self.connect()  # 在初始化时建立连接

    def connect(self):
        return redis.Redis(**self.redis_config)

    def close(self):
        if self.conn:
            self.conn.close()

    def set_data(self, key, value):
        # 设置键值对到 Redis，使用 JSON 序列化
        self.conn.set(key, json.dumps(value))

    def get_data(self, key):
        # 获取键对应的值，并使用 JSON 反序列化
        value = self.conn.get(key)
        if value:
            return json.loads(value.decode('utf-8'))
        return None

    def enqueue(self, queue_name, item):
        # 入队操作，将 item 添加到队列的末尾，使用 JSON 序列化
        self.conn.rpush(queue_name, json.dumps(item))

    def dequeue(self, queue_name):
        # 出队操作，从队列的头部移除并返回一个元素，使用 JSON 反序列化
        item = self.conn.lpop(queue_name)
        if item:
            return json.loads(item.decode('utf-8'))
        return None

    def delete_queue(self, queue_name):
        # 删除队列
        self.conn.delete(queue_name)

    def view_queue(self, queue_name):
        # 查看队列中的所有元素，使用 JSON 反序列化
        items = self.conn.lrange(queue_name, 0, -1)
        return [json.loads(item.decode('utf-8')) for item in items]

# 示例 Redis 配置
redis_config = {
    'host': 'localhost',
    'port': 6380,
    'db': 0,
    'password': 'bobbyishandsome'
}

# 示例使用
if __name__ == "__main__":
    redis_manager = RedisManager(redis_config)

    queue_name = "video_url_a608f208-67f3-48b9-ac9c-b3073aa37c88"
    # item1 = {"id": 1, "value": "item1"}
    # item2 = {"id": 2, "value": "item2"}

    # # 入队操作
    # redis_manager.enqueue(queue_name, item1)
    # redis_manager.enqueue(queue_name, item2)

    # 查看队列
    print(f"Queue contents: {redis_manager.view_queue(queue_name)}")

    # # 出队操作
    # print(f"Dequeued item: {redis_manager.dequeue(queue_name)}")
    # print(f"Queue contents after dequeue: {redis_manager.view_queue(queue_name)}")

    # # 删除队列
    # redis_manager.delete_queue(queue_name)
    # print(f"Queue contents after deletion: {redis_manager.view_queue(queue_name)}")

    redis_manager.close()  # 在使用完毕后关闭连接
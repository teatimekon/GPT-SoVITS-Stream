from psycopg2 import connect, sql
from psycopg2.extras import execute_values

class DatabaseManager:
    def __init__(self, db_config):
        self.db_config = db_config
        self.conn = self.connect()  # 在初始化时建立连接
        self.cursor = self.conn.cursor()

    def connect(self):
        return connect(**self.db_config)

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def insert_comments_job(self, job_id, comment, choose_comment, answer, audio_url, video_url):
        # 插入数据到 comments_job 表
        columns = ['job_id', 'comment', 'choose_comment', 'answer', 'audio_url', 'video_url']
        query = sql.SQL("INSERT INTO comments_job ({}) VALUES %s").format(
            sql.SQL(', ').join(map(sql.Identifier, columns))
        )
        data = [(job_id, comment, choose_comment, answer, audio_url, video_url)]
        execute_values(self.cursor, query, data)

        self.conn.commit()

    def get_comments_job_by_id(self, job_id):
        query = """
        SELECT comment, choose_comment, answer, video_url, audio_url, created_at
        FROM comments_job
        WHERE job_id = %s
        ORDER BY created_at DESC
        LIMIT 1;
        """
        self.cursor.execute(query, (job_id,))
        result = self.cursor.fetchone()
        if result:
            comments, choose_comments, answers, video_url, audio_url, created_at = result
            return {
                'comments': comments,
                'choose_comments': choose_comments,
                'answers': answers,
                'video_url': video_url,
                'audio_url': audio_url,
                'created_at': created_at
            }
        return None

# 示例数据库配置
db_config = {
    'dbname': 'maxkb',
    'user': 'postgres',
    'password': 'Password123@postgres',
    'host': '183.131.7.9',
    'port': '5432'
}

# 示例使用
if __name__ == "__main__":
    db_manager = DatabaseManager(db_config)

    job_id = "job123"
    comments = ["评论1", "评论2", "评论3"]
    choose_comments = ["评论1", "评论3"]
    answers = ["答案1", "答案3"]
    audio_urls = ["http://example.com/audio1.mp3", "http://example.com/audio3.mp3"]
    video_urls = ["http://example.com/video1.mp4", "http://example.com/video3.mp4"]

    db_manager.insert_comments_job(job_id, comments, choose_comments, answers, audio_urls, video_urls)
    db_manager.close()  # 在使用完毕后关闭连接
import os
import imaplib
import email
from email.header import decode_header
import pandas as pd
from datetime import datetime, timedelta

# ================= 配置区域 =================
# 1. 从环境变量读取敏感信息（GitHub Secrets 会自动注入这里）
EMAIL_USER = os.environ.get('QQ_EMAIL_USER')  # 你的QQ邮箱地址，如 123456@qq.com
EMAIL_PASS = os.environ.get('QQ_EMAIL_AUTH_CODE')  # 刚才获取的授权码

# 2. 邮件筛选条件
SEARCH_DAYS = 1  # 搜索最近几天的邮件
SUBJECT_KEYWORD = "数据"  # 邮件标题包含的关键词（可选，设为None则不限制）
ATTACHMENT_KEYWORD = ".csv"  # 附件名包含的关键词

# 3. 输出路径
OUTPUT_DIR = "./data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ================= 核心逻辑 =================
def process_emails():
    print(f"[{datetime.now()}] 开始检查邮件...")
    
    # 1. 连接 QQ 邮箱 IMAP 服务器
    try:
        mail = imaplib.IMAP4_SSL("imap.qq.com")
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")  # 选择收件箱
    except Exception as e:
        print(f"❌ 登录失败: {e}")
        return

    # 2. 搜索邮件
    since_date = (datetime.now() - timedelta(days=SEARCH_DAYS)).strftime("%d-%b-%Y")
    search_criteria = f'(SINCE "{since_date}" SUBJECT "{SUBJECT_KEYWORD}")' if SUBJECT_KEYWORD else f'(SINCE "{since_date}")'
    
    status, messages = mail.search(None, search_criteria)
    if status != "OK":
        print("未找到符合条件的邮件。")
        return

    email_ids = messages[0].split()
    print(f"🔍 找到 {len(email_ids)} 封相关邮件")

    # 3. 遍历并下载附件
    for eid in email_ids:
        status, msg_data = mail.fetch(eid, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                
                # 遍历邮件部分查找附件
                for part in msg.walk():
                    if part.get_content_maintype() == "multipart":
                        continue
                    if part.get("Content-Disposition") is None:
                        continue
                    
                    filename = part.get_filename()
                    if filename and ATTACHMENT_KEYWORD in filename.lower():
                        # 解码文件名
                        decoded_filename = decode_header(filename)[0][0]
                        if isinstance(decoded_filename, bytes):
                            decoded_filename = decoded_filename.decode()
                        
                        save_path = os.path.join(OUTPUT_DIR, decoded_filename)
                        
                        # 写入文件
                        with open(save_path, "wb") as f:
                            f.write(part.get_payload(decode=True))
                        print(f"✅ 已保存附件: {decoded_filename}")
                        
                        # 在这里可以加入你的数据处理逻辑
                        # 例如：df = pd.read_csv(save_path); df.to_json(...)

    mail.logout()
    print("🏁 任务完成")

if __name__ == "__main__":
    process_emails()

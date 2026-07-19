import os
import zipfile
import pandas as pd
import json

# 定义目录路径
SOURCE_DIR = 'source_data'      # 存放原始压缩包的地方
EXTRACT_DIR = 'extracted_files' # 临时解压目录
OUTPUT_FILE = 'data.json'       # 最终生成的公开数据文件

# 1. 自动解压附件
os.makedirs(EXTRACT_DIR, exist_ok=True)
for file_name in os.listdir(SOURCE_DIR):
    if file_name.endswith('.zip'):
        zip_path = os.path.join(SOURCE_DIR, file_name)
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(EXTRACT_DIR)
            print(f"✅ 成功解压: {file_name}")
        except Exception as e:
            print(f"❌ 解压失败: {e}")

# 2. 提取、清洗并脱敏数据
processed_data = []

# 遍历解压后的所有文件
for file_name in os.listdir(EXTRACT_DIR):
    file_path = os.path.join(EXTRACT_DIR, file_name)
    
    # 只处理 Excel 或 CSV 文件
    if file_name.endswith(('.xlsx', '.xls', '.csv')):
        try:
            # 读取文件 (根据后缀选择读取方式)
            if file_name.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            # --- 核心逻辑：保留吉祥码，删除敏感信息 ---
            
            # A. 检查是否存在吉祥码列 (支持多种可能的列名)
            code_col = None
            possible_code_names = ['吉祥码', '查询码', '编号', 'Code'] 
            for name in possible_code_names:
                if name in df.columns:
                    code_col = name
                    break
            
            if not code_col:
                print(f"⚠️ 警告: {file_name} 中未找到吉祥码列，已跳过")
                continue

            # B. 定义需要删除的敏感列 (请根据实际情况补充)
            sensitive_cols = [
                '付款人姓名', '姓名', '身份证号', '手机号', 
                '银行卡号', '地址', '备注' 
            ]
            
            # C. 执行脱敏：只保留需要的列，或者删除敏感列
            # 这里采用“白名单”策略更安全：只保留吉祥码和业务信息
            # 假设除了敏感列和吉祥码，其他都是安全的业务数据（如金额、日期）
            cols_to_drop = [col for col in sensitive_cols if col in df.columns]
            df_clean = df.drop(columns=cols_to_drop)
            
            # 将处理好的数据加入列表
            processed_data.append(df_clean)
            print(f"✅ 处理完成: {file_name} (已移除 {len(cols_to_drop)} 个敏感字段)")
            
        except Exception as e:
            print(f"❌ 处理文件 {file_name} 出错: {e}")

# 3. 合并并导出为 JSON
if processed_data:
    final_df = pd.concat(processed_data, ignore_index=True)
    
    # 导出为 JSON，orient='records' 适合前端查询
    final_df.to_json(OUTPUT_FILE, orient='records', force_ascii=False, indent=2)
    print(f"🎉 数据更新成功！共 {len(final_df)} 条记录已写入 {OUTPUT_FILE}")
else:
    print("⚠️ 没有处理任何数据，JSON 文件未更新")

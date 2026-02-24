from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017'))
db = client['fmcg_mastering']
col = db['master_stock_data']

q_nielsen = {
    '$or': [
        {'Facts': {'$regex': '^Sales Value', '$options': 'i'}}, 
        {'FACTS': {'$regex': '^Sales Value', '$options': 'i'}}
    ]
}

merged = list(col.find({**q_nielsen, 'merged_from_docs': {'$gt': 1}}))

reduction = sum(d.get("merged_from_docs", 1) - 1 for d in merged)

print(f"Merged Nielsen Count: {len(merged)}")
print(f"Total Reduction (Reduction from these {len(merged)} products): {reduction}")

# Verify total master stock count for Nielsen
total_nielsen = col.count_documents(q_nielsen)
print(f"Total Nielsen in Master Stock: {total_nielsen}")

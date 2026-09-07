import os
from collections import Counter
from dotenv import load_dotenv
from pymongo import MongoClient
load_dotenv()
try:
    with MongoClient(os.environ['MONGODB_URI'], serverSelectionTimeoutMS=10000) as client:
        col = client['Interview']['MogulsData']
        query = {'$or': [{'athlete.fis_code': {'$in': ['2530720', 2530720]}}, {'athlete.name': {'$regex': 'ANTHONY', '$options': 'i'}}]}
        docs = list(col.find(query))
        print('Matching documents:', len(docs))
        print('Athlete identities:', Counter((d.get('athlete',{}).get('name'), str(d.get('athlete',{}).get('fis_code'))) for d in docs))
        counts = Counter()
        for d in docs:
            for j in d.get('run',{}).get('air',{}).get('jumps',[]):
                counts[(j.get('jump_number'), j.get('type'), j.get('degree_diff'))] += 1
        print('Jump number, type, difficulty frequencies:', counts)
        for d in docs:
            for j in d.get('run',{}).get('air',{}).get('jumps',[]):
                if j.get('jump_number') == 1 and float(j.get('degree_diff', 99)) < 1.1:
                    print('LOW JUMP 1:', str(d['_id']), d.get('event'), d.get('athlete'), j)
except Exception as exc:
    print('Database query failed:', type(exc).__name__)
    raise SystemExit(1)

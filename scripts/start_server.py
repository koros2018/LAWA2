#!/usr/bin/env python3
"""Start LAWA2 backend server"""
import sys
import os
sys.path.insert(0, '/mnt/d/OpenClawData2workspace/Projects/LAWA2')
os.chdir('/mnt/d/OpenClawData2workspace/Projects/LAWA2')

import uvicorn

if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=6290, reload=False)

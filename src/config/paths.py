import os

# Base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Data directories
DATA_DIR = os.path.join(BASE_DIR, 'data')
RAW_DATA_DIR = os.path.join(DATA_DIR, 'raw')
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, 'processed')
FINAL_DATA_DIR = os.path.join(DATA_DIR, 'final')

# Notebooks directory
NOTEBOOKS_DIR = os.path.join(BASE_DIR, 'notebooks')

# Source directories
SRC_DIR = os.path.join(BASE_DIR, 'src')
BACKEND_DIR = os.path.join(SRC_DIR, 'backend')
FRONTEND_DIR = os.path.join(SRC_DIR, 'frontend')

__all__ = [
    'BASE_DIR',
    'DATA_DIR',
    'RAW_DATA_DIR',
    'PROCESSED_DATA_DIR',
    'FINAL_DATA_DIR',
    'NOTEBOOKS_DIR',
    'SRC_DIR',
    'BACKEND_DIR',
    'FRONTEND_DIR',
]
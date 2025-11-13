import os
import glob

# Check model cache location
cache_dir = os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'spleeter')
print(f'Spleeter cache directory: {cache_dir}')
print(f'Exists: {os.path.exists(cache_dir)}')

if os.path.exists(cache_dir):
    # Find model files
    model_files = glob.glob(os.path.join(cache_dir, '**', '*'), recursive=True)
    print(f'\nFound {len(model_files)} total files/dirs in cache')
    
    index_files = glob.glob(os.path.join(cache_dir, '**', '*.index'), recursive=True)
    print(f'Found {len(index_files)} .index model files:')
    for f in index_files:
        size_mb = os.path.getsize(f) / 1024 / 1024
        print(f'  - {f} ({size_mb:.2f} MB)')
    
    data_files = glob.glob(os.path.join(cache_dir, '**', '*.data-*'), recursive=True)
    print(f'\nFound {len(data_files)} .data model files')
else:
    print('Cache directory does not exist!')

# Check pretrained_models in current directory
local_models = 'pretrained_models'
if os.path.exists(local_models):
    print(f'\n\nLocal pretrained_models directory exists:')
    for root, dirs, files in os.walk(local_models):
        level = root.replace(local_models, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f'{indent}{os.path.basename(root)}/')
        subindent = ' ' * 2 * (level + 1)
        for file in files[:10]:  # Limit to first 10 files per dir
            print(f'{subindent}{file}')

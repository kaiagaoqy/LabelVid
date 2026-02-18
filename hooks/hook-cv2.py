# PyInstaller hook for cv2 (OpenCV)
# Fixes recursion error during import

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Collect all cv2 submodules
hiddenimports = collect_submodules('cv2')

# Collect data files
datas = collect_data_files('cv2', include_py_files=True)

# Exclude problematic modules that cause recursion
excludedimports = ['cv2.cv2']

from PyInstaller.utils.hooks import collect_data_files, collect_submodules
datas = collect_data_files('mediapipe', includes=['modules/**'])
hiddenimports = collect_submodules('mediapipe')
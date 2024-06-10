import requests
import os

# 文件路径
bundle_versions_path = 'bundle_versions'  
audio_versions_path = 'audio_versions'  
video_versions_path = 'video_versions' 

# 读取文件内容
def read_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Failed to read file {file_path}: {e}")
        return None

# 提取 .blk 文件名
def get_blk_files(content):
    blk_files = []
    for line in content.splitlines():
        parts = line.split()
        if len(parts) > 0 and parts[0].startswith('blocks/') and parts[0].endswith('.blk'):
            blk_files.append(parts[0].split('/')[-1])
    return blk_files

# 提取 AudioAssets 文件名
def get_audio_files(content):
    audio_files = []
    for line in content.splitlines():
        print(f"Parsing line: {line}")  # 调试信息
        parts = line.split()
        if len(parts) > 0 and parts[0].endswith('.pck'):
            audio_files.append(parts[0])
    return audio_files

# 提取 VideoAssets 文件名
def get_video_files(content):
    video_files = []
    for line in content.splitlines():
        print(f"Parsing line: {line}")  # 调试信息
        parts = line.split()
        if len(parts) > 0 and (parts[0].endswith('.usm') or parts[0].endswith('.srt')):
            video_files.append(parts[0])
    return video_files

# 下载文件函数
def download_file(base_url, file_name, save_dir):
    url = base_url + file_name
    local_path = os.path.join(save_dir, file_name)
    try:
        print(f"Downloading {file_name} from {url}")
        response = requests.get(url)
        response.raise_for_status()
        with open(local_path, 'wb') as f:
            f.write(response.content)
        print(f"Successfully downloaded: {file_name}")
    except Exception as e:
        print(f"Failed to download {file_name}: {e}")

# 主函数
def main(mode):
    print(f"Running in {mode} mode")
    if mode == 'blk':
        base_url = 'https://autopatchcn.yuanshen.com/client_game_res/cjAndroid/output_196129/client/Android/AssetBundles/blocks/'
        content = read_file(bundle_versions_path)
        if content is None:
            print("Failed to read bundle_versions file.")
            return
        files = get_blk_files(content)
        save_dir = 'AssetBundles'
    elif mode == 'audio':
        base_url = 'https://autopatchcn.yuanshen.com/client_game_res/cjAndroid/output_196129/client/Android/AudioAssets/'
        content = read_file(audio_versions_path)
        if content is None:
            print("Failed to read audio_versions file.")
            return
        files = get_audio_files(content)
        save_dir = 'AudioAssets'
    elif mode == 'video':
        base_url = 'https://autopatchcn.yuanshen.com/client_game_res/cjAndroid/output_196129/client/Android/VideoAssets/'
        content = read_file(video_versions_path)
        if content is None:
            print("Failed to read video_versions file.")
            return
        files = get_video_files(content)
        save_dir = 'VideoAssets'
    else:
        print("Invalid mode. Choose 'blk', 'audio', or 'video'.")
        return

    if not files:
        print(f"No files to download for mode: {mode}")
        return

    print(f"Found {len(files)} files to download in {mode} mode.")
    os.makedirs(save_dir, exist_ok=True)
    for file in files:
        download_file(base_url, file, save_dir)

if __name__ == "__main__":
    mode = input("Enter mode ('blk', 'audio', or 'video'): ").strip().lower()
    main(mode)

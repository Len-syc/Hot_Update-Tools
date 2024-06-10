import asyncio
import aiohttp


GREEN_COLOR = "\033[92m"
RED_COLOR = "\033[91m"
RESET_COLOR = "\033[0m"

async def check_url(session, url):
    try:
        async with session.head(url) as response:
            if response.status == 200:
                version = url.split("output_")[-1].split("/")[0] 
                print(f"{GREEN_COLOR}{version} 发现版本{RESET_COLOR}")
                return True
            else:
                version = url.split("output_")[-1].split("/")[0]
                print(f"{RED_COLOR}{version} 未发现，状态码：{response.status}{RESET_COLOR}")
                return False
    except aiohttp.ClientError:
        print(f"{RED_COLOR}连接到 {url} 失败{RESET_COLOR}")
        return False

async def main():
    # 有一些有分区，记得修改
    base_url_templates = [
        "https://autopatchcntx.yuanshen.com/client_game_res/pp01/{}/output_{}/client/Android/res_versions",
        "https://autopatchcn.yuanshen.com/client_game_res/pp01/{}/output_{}/client/StandaloneWindows64/AssetBundles/bundle_versions"
    ]
    
    platform = input("请输入版本：")
    start = int(input("请输入起始版本："))
    end = int(input("请输入结束版本："))

    downloadable_versions = []

    async with aiohttp.ClientSession() as session:
        tasks = []
        for base_url_template in base_url_templates:
            for i in range(start, end + 1):
                url = base_url_template.format(platform, i)
                tasks.append(check_url(session, url))
        
        results = await asyncio.gather(*tasks)
        for idx, result in enumerate(results):
            if result:
                version = idx % (end - start + 1) + start
                downloadable_versions.append(version)
    
    print("可下载的版本：")
    for version in downloadable_versions:
        if "Android" in base_url_templates[0]:
            print(f"{version}：Android")
        elif "StandaloneWindows64" in base_url_templates[1]:
            print(f"{version}：StandaloneWindows64")

if __name__ == "__main__":
    asyncio.run(main())

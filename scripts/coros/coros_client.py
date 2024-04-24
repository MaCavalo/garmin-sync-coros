import argparse
import asyncio
import os
import hashlib
from garmin_sync import Garmin, download_new_activities, gather_with_concurrency
from synced_data_file_logger import load_synced_activity_list, save_synced_activity_list
from coros_sync import Coros

# 设置TCX文件夹路径
TCX_FOLDER = "path/to/tcx/folder"

# 确保TCX文件夹存在
if not os.path.exists(TCX_FOLDER):
    os.mkdir(TCX_FOLDER)

# 同步佳明国际区到TCX
async def sync_garmin_international(secret_string_global):
    # 加载已同步的活动列表
    synced_activity = load_synced_activity_list()

    # 下载新的活动
    future = asyncio.ensure_future(
        download_new_activities(
            secret_string_global,
            "Global",  # 只需关注国际区
            synced_activity,
            False,  # 是否只运行，不同步
            TCX_FOLDER,
            "tcx",  # 使用TCX格式
        )
    )
    await future

    new_ids = future.result()

    # 保存新同步的活动
    synced_activity.extend(new_ids)
    save_synced_activity_list(synced_activity)

    return new_ids

# 上传TCX到高驰
async def upload_tcx_to_coros(coros_account, coros_password):
    coros = Coros(coros_account, hashlib.md5(coros_password.encode()).hexdigest())
    await coros.init()

    # 上传所有TCX文件
    tcx_files = [os.path.join(TCX_FOLDER, f) for f in os.listdir(TCX_FOLDER) if f.endswith(".tcx")]

    await gather_with_concurrency(
        10,
        [coros.upload_activity(file) for file in tcx_files]
    )

# 主程序，执行同步和上传
async def main(secret_string_global, coros_account, coros_password):
    # 第一步：同步佳明国际区的TCX数据
    new_ids = await sync_garmin_international(secret_string_global)

    # 第二步：上传TCX到高驰
    await upload_tcx_to_coros(coros_account, coros_password)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("global_secret_string", help="佳明国际区的认证字符串")
    parser.add_argument("coros_account", help="高驰的账户")
    parser.add_argument("coros_password", help="高驰的密码")
    options = parser.parse_args()

    asyncio.run(main(options.global_secret_string, options.coros_account, options.coros_password))

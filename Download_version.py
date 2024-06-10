#!/usr/bin/python3
import sys
import os
import json
import requests
import logging
import signal
from shutil import copyfileobj
from posixpath import join as urljoin
from argparse import ArgumentParser



# ep；python Download_version.py --branch yspre_cb2plus_live --out ./resources --url https://autopatchcn.yuanshen.com res 479984
CLIENTS = [
  "Android",
  "StandaloneWindows64",
  "iOS",
  "PS5",
  "PS4"
]

RES_BASE_PATH = "client_game_res"
RES_FILES = [
  "res_versions_external",
  "res_versions_medium",
  "res_versions_streaming",
  "release_res_versions_external",
  "release_res_versions_medium",
  "release_res_versions_streaming",
  "base_revision",
  "script_version",
  "AudioAssets/audio_versions",
  "VideoAssets/video_versions",
  "AssetBundles/bundle_versions",
]
RES_PARSEABLE_FILES = [
  "res_versions_external",
  "release_res_versions_external",
  "AudioAssets/audio_versions",
  "VideoAssets/video_versions",
  "AssetBundles/bundle_versions",
]
RES_BASE_SKIPPABLE = [
  "AudioAssets/audio_versions",
  "VideoAssets/video_versions",
  "AssetBundles/bundle_versions",
]
RES_AUDIO_DIFF_FILE = "audio_diff_versions"

SILENCE_BASE_PATH = "client_design_data"
SILENCE_FILES = [
  "AssetBundles/data_versions",
  "AssetBundles/bundle_versions",
]

DATA_BASE_PATH = "client_design_data"
DATA_FILES = [
  "AssetBundles/data_versions",
  "AssetBundles/bundle_versions",
]

DIR_MAPPINGS = {
  ".blk": "AssetBundles",
  ".pck": "AudioAssets",
  ".cuepoint": "VideoAssets",
  ".srt": "VideoAssets",
  ".usm": "VideoAssets"
}
AUDIO_DIFF_DIR = "AudioDiff"

NAME_MAPPINGS = {
  "svc_catalog": "AssetBundles"
}

def logger():
  return logging.getLogger(os.path.basename(__file__))

def sigint_handler(signal, frame):
  logger().info("Interrupted but nothing to clean up yet; exiting cleanly")
  sys.exit(130)

def fetch_file(rel_path, base_url, dst_dir):
  if os.path.exists(f"{dst_dir}/{rel_path}"):
    logger().debug(f"File {rel_path} already exists; skipping")
    return

  logger().info(f"Fetching {rel_path}...")
  try:
    response = requests.get(urljoin(base_url, rel_path), stream=True)
  except Exception as err:
    logger().error(f"Failed to fetch {rel_path}; {err=}")
    return

  if response.status_code != 200:
    logger().error(f"Failed to fetch {rel_path}; status_code={response.status_code}")
    return

  os.makedirs(os.path.dirname(f"{dst_dir}/{rel_path}"), exist_ok=True) # need to create directory

  try:
    signal.signal(signal.SIGINT, signal.default_int_handler) # reset handler so we can catch exception
    with open(f"{dst_dir}/{rel_path}", "wb") as file:
      copyfileobj(response.raw, file, length=16*1024*1024) # write in 16M chunks
  except KeyboardInterrupt:
    logger().warning("Catched KeyboardInterrupt during download process; cleaning up partial files...")
    os.remove(f"{dst_dir}/{rel_path}")
    logger().info("Exiting cleanly")
    sys.exit(130)

  signal.signal(signal.SIGINT, sigint_handler) # restore custom handler

def parse_res_versions(name, rel_path, base_url, dst_dir, is_base):
  logger().info(f"Parsing {name} with {{{rel_path=}, {is_base=}}}")

  if not os.path.exists(f"{dst_dir}/{rel_path}/{name}"):
    logger().error(f"Unable to parse {rel_path}/{name}; file does not exist")
    return

  if is_base and name in RES_BASE_SKIPPABLE:
    logger().debug(f"Skipping {name} because {is_base=}; resources already fetched")
    return

  file = open(f"{dst_dir}/{rel_path}/{name}")
  while True:
    line = file.readline()
    if not line:
      break

    try:
      resource = json.loads(line.strip())

      remote_name = resource.get("remoteName")
      is_patch = resource.get("isPatch")
    except json.decoder.JSONDecodeError:
      resource = line.strip().split(' ')

      remote_name = resource[0]
      try:
        is_patch = True if resource[2] == 'P' else False
      except IndexError:
        is_patch = False

    if is_base == False and is_patch != True:
      continue # revision is not base and file is not marked as updated

    remote_dir = DIR_MAPPINGS.get(os.path.splitext(remote_name)[1]) or NAME_MAPPINGS.get(remote_name) or ""
    fetch_file(urljoin(rel_path, remote_dir, remote_name), base_url, dst_dir)

def parse_data_versions(name, rel_path, base_url, dst_dir):
  logger().info(f"Parsing {name} with {{{rel_path=}}}")

  if not os.path.exists(f"{dst_dir}/{rel_path}/{name}"):
    logger().error(f"Unable to parse {rel_path}/{name}; file does not exist")
    return

  file = open(f"{dst_dir}/{rel_path}/{name}")
  while True:
    line = file.readline()
    if not line:
      break

    try:
      remote_name = json.loads(line.strip()).get("remoteName")
    except json.decoder.JSONDecodeError:
      remote_name = line.strip().split(' ')[0]

    remote_dir = DIR_MAPPINGS.get(os.path.splitext(remote_name)[1]) or NAME_MAPPINGS.get(remote_name) or ""
    fetch_file(urljoin(rel_path, remote_dir, remote_name), base_url, dst_dir)

def parse_audio_versions(name, rel_path, base_url, dst_dir, diff):
  logger().info(f"Parsing {name} with {{{rel_path=}, {diff=}}}")

  if not os.path.exists(f"{dst_dir}/{rel_path}/{name}"):
    logger().error(f"Unable to parse {rel_path}/{name}; file does not exist")
    return

  file = open(f"{dst_dir}/{rel_path}/{name}")
  while True:
    line = file.readline()
    if not line:
      break

    try:
      remote_name = json.loads(line.strip()).get("remoteName")
    except json.decoder.JSONDecodeError:
      remote_name = line.strip().split(' ')[0]

    remote_dir = f"{AUDIO_DIFF_DIR}_{diff}"
    fetch_file(urljoin(rel_path, remote_dir, remote_name), base_url, dst_dir)

def main(args):
  logger().info(f"Initialized with {args=}")

  if args.command == 'res':
    for client in CLIENTS:
      for name in RES_FILES:
        fetch_file(f"{RES_BASE_PATH}/{args.branch}/output_{args.revision}/client/{client}/{name}", args.url, args.out)
        if name in RES_PARSEABLE_FILES:
          parse_res_versions(name, f"{RES_BASE_PATH}/{args.branch}/output_{args.revision}/client/{client}", args.url, args.out, args.base)
      if args.audio:
        fetch_file(f"{RES_BASE_PATH}/{args.branch}/output_{args.revision}/client/{client}/{RES_AUDIO_DIFF_FILE}_{args.audio}", args.url, args.out)
        parse_audio_versions(f"{RES_AUDIO_DIFF_FILE}_{args.audio}", f"{RES_BASE_PATH}/{args.branch}/output_{args.revision}/client/{client}", args.url, args.out, args.audio)
  elif args.command == 'data':
    for name in DATA_FILES:
      fetch_file(f"{DATA_BASE_PATH}/{args.branch}/output_{args.revision}/client/StandaloneWindows64/{name}", args.url, args.out)
      parse_data_versions(name, f"{DATA_BASE_PATH}/{args.branch}/output_{args.revision}/client/StandaloneWindows64", args.url, args.out)
  elif args.command == 'silence':
    for name in SILENCE_FILES:
      fetch_file(f"{SILENCE_BASE_PATH}/{args.branch}/output_{args.revision}/client_silence/StandaloneWindows64/{name}", args.url, args.out)
      parse_data_versions(name, f"{SILENCE_BASE_PATH}/{args.branch}/output_{args.revision}/client_silence/StandaloneWindows64", args.url, args.out)

if __name__ == "__main__":
  parser = ArgumentParser(description="Fetches hot-patch resources for given version")
  parser.add_argument("--branch", type=str, required=True, help="Branch name (eg. 3.2_live)")
  parser.add_argument("--out", "-o", help="Output directory (defaults to ./resources)", type=str, default="./resources")
  parser.add_argument("--url", "-u", help="Base URL to download from, including protocol (defaults to https://autopatchhk.yuanshen.com)", type=str, default="https://autopatchhk.yuanshen.com")
  parser.add_argument("--verbose", "-v", help="Be more verbose", action="store_true")
  subparsers = parser.add_subparsers(help='Type of resource to fetch', required=True, dest='command')

  res_parser = subparsers.add_parser('res')
  res_parser.add_argument("revision", type=str, help="Resource reversion in format of {$revision}_{$suffix}")
  res_parser.add_argument("--base", "-b", help="Whether given revision is base (will attempt to fetch all resources)", action="store_true")
  res_parser.add_argument("--audio", "-a", help="Audio diff in format of {$current}-{$previous}")

  data_parser = subparsers.add_parser('data')
  data_parser.add_argument("revision", type=str, help="Client data reversion in format of {$revision}_{$suffix}")

  silence_parser = subparsers.add_parser('silence')
  silence_parser.add_argument("revision", type=str, help="Client silence reversion in format of {$revision}_{$suffix}")

  args = parser.parse_args()

  logger().setLevel(logging.DEBUG if args.verbose else logging.INFO)
  handler = logging.StreamHandler()
  handler.setFormatter(logging.Formatter("[%(asctime)s] <%(levelname)s> %(message)s"))
  logger().addHandler(handler)

  signal.signal(signal.SIGINT, sigint_handler)

  sys.exit(main(args))

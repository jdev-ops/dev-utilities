import glob
import json
import os
import subprocess
import sys
from pathlib import Path
from shutil import *
from typing import Annotated

import typer
from decouple import Config, RepositoryEnv
from decouple import config as decouple_config
from slugify import slugify

# import pprint
from yaml import load

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

import logging
import traceback

import cattrs
from rich import print

from dev_utilities.containers import *

CONFIG_WORKING_DIR = os.environ.get("CONFIG_WORKING_DIR", ".")

if os.environ.get("CONFIG_PATH"):
    config = Config(RepositoryEnv(os.environ["CONFIG_PATH"]))
elif Path(f"{CONFIG_WORKING_DIR}/.env.local").is_file():
    config = Config(RepositoryEnv(f"{CONFIG_WORKING_DIR}/.env.local"))
else:
    config = decouple_config

DEV_ENV_DOCKER_SETUP_CONFIG_FILE_DIR = config(
    "DEV_ENV_DOCKER_SETUP_CONFIG_FILE_DIR",
)

PORT_START_ENUM = config("PORT_START_ENUM", cast=int, default=2222)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(f"{os.environ['HOME']}/.docker-setup/debug.log"),
        # logging.StreamHandler(sys.stdout),
    ],
    force=True,
)


def deserialize[T](path: Path, clazz: T, ctx: dict[str, any]) -> T | None:
    try:
        content = load(open(path), Loader=Loader)
        return converter.structure(content, clazz)
    except:
        logging.error(traceback.format_exc())
        logging.error(f"Ctx: {ctx}")
        return None


def read_all_content(path: Path, ctx: dict[str, any]) -> str | None:
    try:
        environment = open(path)
        return environment.read()
    except:
        logging.error(traceback.format_exc())
        logging.error(f"Ctx: {ctx}")
        return None


def load_boxes() -> dict[str, Machine]:
    data_file = Path(DEV_ENV_DOCKER_SETUP_CONFIG_FILE_DIR) / "config.yaml"
    if data_file.is_file():
        logging.info(f"Deserializing {data_file} to Boxes")
        root = deserialize(data_file, Boxes, locals())
        if root:
            return {
                b.name: Machine(PORT_START_ENUM + index, b.image, b.host)
                for index, b in enumerate(root.boxes)
            }
    return {}


def boxes_names():
    projects = load_boxes()
    print("\n".join(projects.keys()))
    return 0


import time

import docker
from docker.types import Mount


def run_box(box_name: Annotated[str, typer.Argument()]) -> int:
    possible_values = load_boxes()
    box = possible_values.get(box_name.strip())
    client = docker.DockerClient(base_url="unix://run/user/1000/docker.sock")
    # https://docker-py.readthedocs.io/en/stable/containers.html
    box_name = box_name.strip()
    name = f"{slugify(box_name)}"
    volume_name = f"{name}-volume"

    try:
        # https://docker-py.readthedocs.io/en/stable/volumes.html
        client.volumes.get(volume_name)
    except docker.errors.NotFound:
        client.volumes.create(
            name=volume_name,
            driver="local",
        )

    # https://docker-py.readthedocs.io/en/stable/api.html#docker.types.Mount
    state_volume = Mount(
        source=volume_name, target="/home/app/.local/state", type="volume"
    )
    apps_volume = Mount(
        source=f"{os.environ.get('HOME')}/appslnx/",
        target="/home/app/appslnx",
        type="bind",
    )
    try:
        client.containers.get(name)
    except docker.errors.NotFound:
        client.containers.run(
            name=name,
            hostname=box.host,
            image=box.image,
            mounts=[state_volume, apps_volume],
            detach=True,
            auto_remove=True,
            dns=["10.5.0.3", "8.8.8.8"],
            network="dev-network",
            labels={
                "custom.type": "pdi",
                "custom.name": box_name,
                # other labels can be added here
            },
            ports={
                "22/tcp": box.port,
                "8088/tcp": None,
            },
        )
        time.sleep(2)  # wait for the container to start
    # TODO: check if box is None (better error handling)
    print(box.port)
    return 0

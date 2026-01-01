from pathlib import Path
import sys
import subprocess

from dev_utilities.ux import GumUX, RofiUX


def get_paths(parts):
    if len(parts) == 1:
        return [[parts[0]]]
    result = [list(parts)]
    rest = get_paths(parts[:-1])
    result.extend(rest)
    return result


def path_is_project(path: Path, projects_markers: dict) -> bool:
    for marker in projects_markers["dirs"]:
        if (path / marker).is_dir():
            return True
    for marker in projects_markers["files"]:
        if (path / marker).is_file():
            return True
    return False


def get_all_bookmark_files(bookmarks_dir: Path, path: Path) -> list[str]:
    if (path / bookmarks_dir).is_dir():
        return [f.name for f in (path / bookmarks_dir).rglob("*") if f.is_file()]
    return []


from typing import Union
from pydantic import BaseModel
from fastapi import FastAPI, Request


class CreateLoadRequest(BaseModel):
    current_file: str | None = None
    client: str = "emacsd-lsp"


import uvicorn

app = FastAPI()

# @app.post("/log")
# async def log_everything(request: Request):
#     body = await request.body()
#     headers = dict(request.headers)
# print("Headers:", headers)
# print("Body:", body.decode())

class EmacsBookmarksManager:
    def __init__(self, ux,
                 prefix_path,
                 bookmarks_dir,
                 projects_markers,
                 empty_bookmark,
                 ):
        self.ux = ux
        self.prefix_path = prefix_path
        self.bookmarks_dir = bookmarks_dir
        self.projects_markers = projects_markers
        self.bookmarks_dir_path = Path(bookmarks_dir)
        self.empty_bookmark = empty_bookmark

    def save_current_bookmarks_via_emacsclient(self, client):
        # cmd = f"emacsclient -e '(bookmark-write bookmark-default-file t)'"
        o = None
        # clients = ["emacsd-lsp", "emacsd-bridge" ]
        cmd = f"emacsclient --socket-name={client} -e '(bookmark-write-file bookmark-default-file)'"
        o = subprocess.check_output([cmd], text=True, shell=True).strip()
        return o

    def load_bookmarks_via_emacsclient(self, path, client):
        import time
        o = None
        cmd = f"emacsclient --socket-name={client} -e '(setq bookmark-default-file \"{path}\")'"
        o = subprocess.check_output([cmd], text=True, shell=True).strip()
        time.sleep(1)
        cmd = f"emacsclient --socket-name={client} -e '(bookmark-load bookmark-default-file t)'"
        o = subprocess.check_output([cmd], text=True, shell=True).strip()
        return o

    def create_bookmarks(self, path, client):
        path = path.removeprefix(self.prefix_path)
        path = Path(path)
        parts = path.parts[:-1]
        fls = dict()
        locations_options = []
        for p in get_paths(parts):
            current_path = Path(self.prefix_path, *p)
            if path_is_project(current_path, self.projects_markers):
                l = get_all_bookmark_files(self.bookmarks_dir_path, current_path)
                if len(l) > 0:
                    fls[(current_path / self.bookmarks_dir_path).as_posix()] = set(l)
                locations_options.append(current_path.as_posix())
        options = []
        for vls in fls.values():
            options.extend(list(vls))

        # print(f"before place: len(locations_options)={len(locations_options)}, locations_options={locations_options}")
        place = self.ux.choose(options=locations_options)
        # print("before name")
        if len(options) == 1:
            options.append("----")
        name = self.ux.choose(options=options)
        for k, v in fls.items():
            if name in v:
                return {"result": f"There is already one bookmark file with that name"}
        print(f"place: {place}, name: {name}")
        (place /self. bookmarks_dir_path).mkdir(parents=True, exist_ok=True)
        new_bookmarks_path = place / self. bookmarks_dir_path / name
        open(new_bookmarks_path, "w").write(empty_bookmark)
        self.save_current_bookmarks_via_emacsclient(client)
        self.load_bookmarks_via_emacsclient(new_bookmarks_path.as_posix(), client)
        return {"result": f"ok"}

    def load_bookmarks(self, path, client):
        path = path.removeprefix(self.prefix_path)
        path = Path(path)
        parts = path.parts[:-1]
        fls = dict()
        for p in get_paths(parts):
            current_path = Path(self.prefix_path, *p)
            if path_is_project(current_path, self.projects_markers):
                l = get_all_bookmark_files(self.bookmarks_dir_path, current_path)
                if len(l) > 0:
                    fls[(current_path / self.bookmarks_dir_path).as_posix()] = set(l)
        options = []
        for vls in fls.values():
            options.extend(list(vls))

        case = self.ux.choose(options=options)
        for k, v in fls.items():
            if case in v:
                new_bookmarks_path = Path(k) / case
                self.save_current_bookmarks_via_emacsclient(client)
                self.load_bookmarks_via_emacsclient(new_bookmarks_path.as_posix(), client)
                return {"result": f"ok"}

        return {"result": f"error"}

empty_bookmark = """
;;;; Emacs Bookmark Format Version 1;;;; -*- coding: utf-8-emacs; mode: lisp-data -*-
;;; This format is meant to be slightly human-readable;
;;; nevertheless, you probably don't want to edit it.
;;; -*- End Of Bookmark File Format Version Stamp -*-
()
""".strip()
ux = RofiUX()
prefix_path = "/home/z/"
bookmarks_dir = ".bookmarks"
projects_markers = {
    "dirs": {".git", bookmarks_dir},
    "files": {"pyproject.toml", "package.json", "Cargo.toml", "build.sbt"},
}
bookmarks_dir_path = Path(bookmarks_dir)

obj = EmacsBookmarksManager(
    ux=ux,
    prefix_path=prefix_path,
    bookmarks_dir=bookmarks_dir,
    projects_markers=projects_markers,
    empty_bookmark=empty_bookmark,
)

@app.post("/api/v1/create-bookmarks")
async def create_bookmarks(request: CreateLoadRequest):
    if not request.current_file:
        return {"result": "error: current_file is required"}

    print(request)
    return obj.create_bookmarks(request.current_file, request.client)
    ux = RofiUX()
    prefix_path = "/home/z/"
    bookmarks_dir = ".bookmarks"
    projects_markers = {
        "dirs": {".git", bookmarks_dir},
        "files": {"pyproject.toml", "package.json", "Cargo.toml", "build.sbt"},
    }
    bookmarks_dir_path = Path(bookmarks_dir)
    path = "/home/z/src/Python/pocs/general-demos/domain/__init__.py"
    path = path.removeprefix(prefix_path)
    path = Path(path)
    parts = path.parts[:-1]
    fls = dict()
    locations_options = []
    for p in get_paths(parts):
        current_path = Path(prefix_path, *p)
        if path_is_project(current_path, projects_markers):
            l = get_all_bookmark_files(bookmarks_dir_path, current_path)
            if len(l) > 0:
                fls[(current_path / bookmarks_dir_path).as_posix()] = set(l)
            locations_options.append(current_path.as_posix())
    options = []
    for vls in fls.values():
        options.extend(list(vls))

    # print(f"before place: len(locations_options)={len(locations_options)}, locations_options={locations_options}")
    place = ux.choose(options=locations_options)
    # print("before name")
    if len(options) == 1:
        options.append("----")
    name = ux.choose(options=options)
    for k, v in fls.items():
        if name in v:
            return {"result": f"there is already one bookmark file with that name"}
    print(f"place: {place}, name: {name}")
    (place / bookmarks_dir_path).mkdir(parents=True, exist_ok=True)
    open(place / bookmarks_dir_path / name, "w").write(empty_bookmark)
    return {"result": f"logged at: {request.current_file}"}


@app.post("/api/v1/load-bookmarks")
async def load_bookmarks(request: CreateLoadRequest):
    if not request.current_file:
        return {"result": "error: current_file is required"}
    return obj.load_bookmarks(request.current_file, request.client)
    ux = RofiUX()
    prefix_path = "/home/z/"
    bookmarks_dir = ".bookmarks"
    projects_markers = {
        "dirs": {".git", bookmarks_dir},
        "files": {"pyproject.toml", "package.json", "Cargo.toml", "build.sbt"},
    }
    bookmarks_dir_path = Path(bookmarks_dir)

    path = "/home/z/src/Python/pocs/general-demos/domain/__init__.py"

    path = path.removeprefix(prefix_path)
    path = Path(path)
    parts = path.parts[:-1]
    fls = dict()
    for p in get_paths(parts):
        current_path = Path(prefix_path, *p)
        if path_is_project(current_path, projects_markers):
            l = get_all_bookmark_files(bookmarks_dir_path, current_path)
            if len(l) > 0:
                fls[(current_path / bookmarks_dir_path).as_posix()] = set(l)
    options = []
    for vls in fls.values():
        options.extend(list(vls))

    case = ux.choose(options=options)
    for k, v in fls.items():
        if case in v:
            print(Path(k) / case)

    return {"result": f"logged at: {request.current_file}"}



def main():
    uvicorn.run("dev_utilities.bookmarks:app", host="127.0.0.1",
                port=8099, reload=True,
                reload_dirs=[
                    Path("~/src/infra/tools/dev-utilities/src/dev_utilities/bookmarks").expanduser().as_posix()],
                )


def main2():
    ux = RofiUX()
    prefix_path = "/home/z/"
    path = "/home/z/src/infra/tools/dev-utilities/justfile"
    path = path.removeprefix(prefix_path)
    path = Path(path)
    bookmarks_dir = ".bookmarks"
    projects_markers = {
        "dirs": {".git", bookmarks_dir},
        "files": {"pyproject.toml", "package.json", "Cargo.toml", "build.sbt"},
    }
    bookmarks_dir_path = Path(bookmarks_dir)
    parts = path.parts[:-1]
    fls = dict()
    locations_options = []
    for p in get_paths(parts):
        current_path = Path(prefix_path, *p)
        if path_is_project(current_path, projects_markers):
            l = get_all_bookmark_files(bookmarks_dir_path, current_path)
            if len(l) > 0:
                fls[(current_path / bookmarks_dir_path).as_posix()] = set(l)
            locations_options.append(current_path)
    options = []
    for vls in fls.values():
        options.extend(list(vls))

    place = ux.choose(options=locations_options)
    name = ux.choose(options=options)
    for k, v in fls.items():
        if name in v:
            sys.exit(1)  # there is already one with that name
    print(f"place: {place}, name: {name}")


def main_load():
    ux = RofiUX()
    prefix_path = "/home/z/"
    path = "/home/z/src/infra/tools/dev-utilities/justfile"
    path = path.removeprefix(prefix_path)
    path = Path(path)
    bookmarks_dir = ".bookmarks"
    projects_markers = {
        "dirs": {".git", bookmarks_dir},
        "files": {"pyproject.toml", "package.json", "Cargo.toml", "build.sbt"},
    }
    bookmarks_dir_path = Path(bookmarks_dir)
    parts = path.parts[:-1]
    fls = dict()
    for p in get_paths(parts):
        current_path = Path(prefix_path, *p)
        if path_is_project(current_path, projects_markers):
            l = get_all_bookmark_files(bookmarks_dir_path, current_path)
            if len(l) > 0:
                fls[(current_path / bookmarks_dir_path).as_posix()] = set(l)
    options = []
    for vls in fls.values():
        options.extend(list(vls))

    case = ux.choose(options=options)
    for k, v in fls.items():
        if case in v:
            print(Path(k) / case)

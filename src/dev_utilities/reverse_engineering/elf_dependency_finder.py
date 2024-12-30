import os
import subprocess
import shutil
import tarfile

def list_dependencies(elf_file):
    try:
        result = subprocess.run(['ldd', elf_file], capture_output=True, text=True, check=True)
        dependencies = []
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 3 and parts[2].startswith('/'):
                dependencies.append(parts[2])
        return dependencies
    except subprocess.CalledProcessError as e:
        print(f"Error running ldd: {e}")
        return []

def get_all_dependencies(elf_file, seen=None):
    if seen is None:
        seen = set()
    if elf_file in seen:
        return []
    seen.add(elf_file)
    dependencies = list_dependencies(elf_file)
    all_dependencies = set(dependencies)
    for dep in dependencies:
        all_dependencies.update(get_all_dependencies(dep, seen))
    return all_dependencies

def copy_dependencies(dependencies, dest_folder):
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)
    for dep in dependencies:
        shutil.copy(dep, dest_folder)

def create_tar_file(source_folder, tar_file_path):
    with tarfile.open(tar_file_path, "w:gz") as tar:
        tar.add(source_folder, arcname=os.path.basename(source_folder))

import typer


def main(elf_file : str,
         dest_folder : str = './elfs-deps',
         tar_file_path : str = './packed-elf-deps.tar.gz',
         ):

    all_dependencies = get_all_dependencies(elf_file)
    copy_dependencies(all_dependencies, dest_folder)
    # create_tar_file(dest_folder, tar_file_path)

    print(f"All dependencies have been copied to {dest_folder} and archived in {tar_file_path}")

def run():
    typer.run(main)

if __name__ == "__main__":
    typer.run(main)

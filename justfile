set shell := ["sh", "-c"]
set allow-duplicate-recipes
set positional-arguments
set dotenv-load
set export

shfmt:
	shfmt -i 2 -l -w bin/*

pyfmt:
	black src/

build:
    #!/usr/bin/env python

    import zipfile
    import shutil
    import os
    import subprocess
    import glob

    def delete_files_and_subdirectories(directory_path):
       try:
         with os.scandir(directory_path) as entries:
           for entry in entries:
             if entry.is_file():
                os.unlink(entry.path)
             else:
                shutil.rmtree(entry.path)
       except OSError:
         pass

    def build():
        delete_files_and_subdirectories("dist")
        subprocess.run(["python", "-m", "build"])

    build()
    files = glob.glob('dist/*.whl')
    whl_file = files[0]
    whl_file_as_zip_file = whl_file[:-4] + ".zip"
    whl_file_name = whl_file[:-4]
    shutil.move(whl_file, whl_file_as_zip_file)
    os.mkdir("dist/out")
    shutil.unpack_archive(whl_file_as_zip_file, "dist/out")
    files = glob.glob('dist/*.gz')
    gz_file_name = files[0][5:-7]
    destination_folder = f"dist/out/{gz_file_name}.data/scripts/"
    os.makedirs(destination_folder)
    source_folder = "bin/"
    for file_name in os.listdir(source_folder):
        source = source_folder + file_name
        destination = destination_folder + file_name
        if os.path.isfile(source):
            shutil.copy(source, destination)

    shutil.make_archive(whl_file_name, format='zip', root_dir='dist/out')
    shutil.move(f"{whl_file_name}.zip", f"{whl_file_name}.whl")

    shutil.rmtree("dist/out")

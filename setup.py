import setuptools
import pathlib

from setuptools import find_packages

here = pathlib.Path(__file__).parent.resolve()

install_requires = (
    (here / "requirements/common.txt").read_text(encoding="utf-8").splitlines()
)


setuptools.setup(
    name="dev-utilities",
    version="0.0.1",
    author="J. Albert Cruz",
    author_email="jalbertcruz@gmail.com",
    license="MIT",
    package_dir={
        "": "lib",
    },
    packages=find_packages("lib"),
    install_requires=install_requires,
    include_package_data=True,
    scripts=[
        "bin/set-hooks",
    ],
    entry_points={
        "console_scripts": [
            "dot2d2=dev_conversors.main:dot_to_d2",
            "_pre-push=git_policy.pre_push:put_as_githook",
            "_pre-commit=git_policy.pre_commit:put_as_githook",
            "_prepare-commit-msg=git_policy.prepare_commit_msg:put_as_githook",
            "branch-setup=git_policy.branch_setup:main",
        ],
    },
)

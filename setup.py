import os
import subprocess
import sys

from setuptools import Command, find_packages, setup


class DevSetupCommand(Command):
    description = "Setup ambiente di sviluppo: requirements + alembic upgrade head"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        print("\n[Setup] Installazione requirements...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
        )
        print("\n[Setup] Migrazione database Alembic...")
        subprocess.check_call(["alembic", "upgrade", "head"])
        print("\n[Setup] Ambiente pronto!")


setup(
    name="volleyball_scout",
    version="0.1",
    packages=find_packages(),
    install_requires=[],  # usa requirements.txt
    cmdclass={
        "dev_setup": DevSetupCommand,
    },
)

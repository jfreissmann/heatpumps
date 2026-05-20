import os
import subprocess
from importlib import resources


def main():
    dashboard_path = resources.files('heatpumps').joinpath('hp_dashboard.py')

    subprocess.run(['streamlit', 'run', dashboard_path])

if __name__ == '__main__':
    main()

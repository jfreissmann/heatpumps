import os
import subprocess


def main():
    dashboard_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), 'hp_dashboard.py'
        )
    )
    subprocess.run(['streamlit', 'run', dashboard_path])

if __name__ == '__main__':
    main()

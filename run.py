import subprocess
import sys

def run_script(script_name):
    try:
        print(f"Running {script_name}...")
        subprocess.check_call([sys.executable, script_name])
    except subprocess.CalledProcessError:
        print(f"Error while running {script_name}")
        sys.exit(1)

if __name__ == "__main__":
    print("\nGenerating Dashboard..\n")

    run_script("balance_cashflow_analysis.py")

    run_script("report_generator.py")

    print("\nDashboard generated !")
    print("Open: index.html\n")
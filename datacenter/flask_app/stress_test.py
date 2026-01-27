import time
import multiprocessing
import os

def cpu_stress():
    """Calculates square roots in a loop to consume CPU."""
    print(f"Stress process started on PID: {os.getpid()}")
    while True:
        x = 100.0 * 100.0
        x = x ** 0.5

def run_stress_event(duration_sec):
    """Starts stress on all CPU cores for a specific duration."""
    processes = []
    # Start a process for every CPU core
    for _ in range(multiprocessing.cpu_count()):
        p = multiprocessing.Process(target=cpu_stress)
        p.start()
        processes.append(p)
    
    time.sleep(duration_sec)
    
    # Stop the stress
    for p in processes:
        p.terminate()
    print("--- Stress Event Finished. System Cooling Down. ---")

# --- MAIN EXPERIMENT LOOP ---
if __name__ == "__main__":
    stress_duration = 120  # 2 minutes of stress
    rest_duration = 600    # 10 minutes of rest (Normal baseline)

    for i in range(1, 3):
        print(f"[{time.strftime('%H:%M:%S')}] Waiting {rest_duration/60} mins before Event #{i}...")
        time.sleep(rest_duration)
        
        print(f"[{time.strftime('%H:%M:%S')}] STARTING STRESS EVENT #{i}!")
        run_stress_event(stress_duration)

    print("Experiment Complete. Both stress events finished.")
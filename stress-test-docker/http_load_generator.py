"""
HTTP Load Generator - Simulate Web Traffic to Flask Server
===========================================================
Simulates DoS attack or high traffic load by sending many HTTP requests
to the Flask server to stress its CPU, memory, and network.
"""

import requests
import threading
import time
import logging
from concurrent.futures import ThreadPoolExecutor
import random

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class HTTPLoadGenerator:
    """Generate HTTP traffic to stress a web server."""
    
    def __init__(self, target_url, requests_per_second=100, duration=120, num_threads=20):
        """
        Args:
            target_url: URL of the Flask server to attack (e.g., http://flask_prod_server:5000)
            requests_per_second: Target RPS (requests per second)
            duration: Duration in seconds
            num_threads: Number of concurrent threads
        """
        self.target_url = target_url
        self.requests_per_second = requests_per_second
        self.duration = duration
        self.num_threads = num_threads
        self.stop_event = threading.Event()
        self.request_count = 0
        self.error_count = 0
        self.lock = threading.Lock()
    
    def send_request(self):
        """Send a single HTTP request."""
        try:
            response = requests.get(self.target_url, timeout=5)
            with self.lock:
                self.request_count += 1
            
            if response.status_code != 200:
                with self.lock:
                    self.error_count += 1
                    
        except Exception as e:
            with self.lock:
                self.error_count += 1
    
    def worker(self, worker_id):
        """Worker thread that sends continuous requests."""
        logger.info(f"Worker {worker_id} started")
        
        while not self.stop_event.is_set():
            self.send_request()
            
            # Sleep to maintain target RPS per worker
            delay = self.num_threads / self.requests_per_second
            time.sleep(delay)
    
    def run(self):
        """Start the load test."""
        logger.info("=" * 60)
        logger.info("HTTP LOAD GENERATOR - DoS SIMULATION")
        logger.info("=" * 60)
        logger.info(f"Target URL: {self.target_url}")
        logger.info(f"Target RPS: {self.requests_per_second}")
        logger.info(f"Threads: {self.num_threads}")
        logger.info(f"Duration: {self.duration}s")
        logger.info("=" * 60)
        
        # Test connection first
        try:
            logger.info("Testing connection to Flask server...")
            response = requests.get(self.target_url, timeout=5)
            logger.info(f"✓ Connection successful! Status: {response.status_code}")
        except Exception as e:
            logger.error(f"✗ Cannot connect to Flask server: {e}")
            logger.error("Make sure Flask container is running and reachable!")
            return
        
        start_time = time.time()
        
        # Start worker threads
        logger.info(f"\n🔥 STARTING ATTACK in 3 seconds...")
        time.sleep(3)
        
        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            # Submit workers
            futures = [executor.submit(self.worker, i) for i in range(self.num_threads)]
            
            # Monitor progress
            while time.time() - start_time < self.duration:
                time.sleep(10)
                elapsed = time.time() - start_time
                
                with self.lock:
                    current_rps = self.request_count / elapsed
                    logger.info(
                        f"⚡ Progress: {elapsed:.0f}s | "
                        f"Requests: {self.request_count} | "
                        f"RPS: {current_rps:.1f} | "
                        f"Errors: {self.error_count}"
                    )
            
            # Stop workers
            self.stop_event.set()
            logger.info("\n🛑 Stopping attack...")
        
        # Final report
        elapsed = time.time() - start_time
        logger.info("=" * 60)
        logger.info("LOAD TEST COMPLETED")
        logger.info("=" * 60)
        logger.info(f"Total Duration: {elapsed:.1f}s")
        logger.info(f"Total Requests: {self.request_count}")
        logger.info(f"Average RPS: {self.request_count / elapsed:.1f}")
        logger.info(f"Success Rate: {(1 - self.error_count/max(self.request_count, 1))*100:.1f}%")
        logger.info(f"Errors: {self.error_count}")
        logger.info("=" * 60)

if __name__ == "__main__":
    # Configuration
    FLASK_URL = "http://host.docker.internal:5005"  # Flask server URL
    REQUESTS_PER_SECOND = 200  # Aggressive load
    DURATION = 120  # 2 minutes
    THREADS = 50  # High concurrency
    
    logger.info("Starting HTTP Load Generator...")
    logger.info("This will simulate high traffic/DoS attack on Flask server")
    logger.info("Watch Grafana to see Flask container CPU/Network spike!\n")
    
    generator = HTTPLoadGenerator(
        target_url=FLASK_URL,
        requests_per_second=REQUESTS_PER_SECOND,
        duration=DURATION,
        num_threads=THREADS
    )
    
    try:
        generator.run()
    except KeyboardInterrupt:
        logger.info("\n⚠️  Load test interrupted by user")
        generator.stop_event.set()

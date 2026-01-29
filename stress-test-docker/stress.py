import psutil
import time
import threading
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class StressTest:
    """Generate CPU, memory, and I/O stress on the system."""
    
    def __init__(self, cpu_percent=80, memory_mb=500, duration=None):
        """
        Args:
            cpu_percent: Target CPU usage (0-100)
            memory_mb: Memory to allocate (MB)
            duration: Duration in seconds (None = infinite)
        """
        self.cpu_percent = cpu_percent
        self.memory_mb = memory_mb
        self.duration = duration
        self.start_time = None
        self.stop_event = threading.Event()
        self.memory_buffer = []
    
    def cpu_stress(self):
        """Generate CPU stress via computation."""
        logger.info(f"Starting CPU stress ({self.cpu_percent}% target)...")
        self.start_time = time.time()
        
        while not self.stop_event.is_set():
            # Intensive computation without sleep - max CPU usage
            # Multiple nested loops for aggressive stress
            for _ in range(100):
                _ = sum(i*i*i for i in range(100000))
                _ = [x**2 for x in range(50000)]
                _ = sum(x*x for x in range(50000))
            
            if self.duration and (time.time() - self.start_time) > self.duration:
                break
    
    def memory_stress(self):
        """Generate memory stress via allocation."""
        logger.info(f"Starting memory stress ({self.memory_mb}MB)...")
        
        try:
            # Allocate and hold memory
            chunk_size = 1024 * 1024  # 1MB chunks
            chunks = self.memory_mb
            
            for i in range(chunks):
                self.memory_buffer.append(bytearray(chunk_size))
                
                if self.duration and (time.time() - self.start_time) > self.duration:
                    break
            
            logger.info(f"Memory allocated: {len(self.memory_buffer)}MB")
            
            # Keep memory allocated
            while not self.stop_event.is_set():
                time.sleep(1)
                
                if self.duration and (time.time() - self.start_time) > self.duration:
                    break
        
        except MemoryError:
            logger.warning("Could not allocate all requested memory")
    
    def run(self, cpu_threads=4):
        """Run stress test with multiple threads."""
        logger.info(f"=== STRESS TEST STARTING ===")
        logger.info(f"CPU threads: {cpu_threads}")
        logger.info(f"Memory allocation: {self.memory_mb}MB")
        logger.info(f"Duration: {self.duration}s (infinite if None)")
        logger.info("Press Ctrl+C to stop\n")
        
        # Start memory stress in separate thread
        mem_thread = threading.Thread(target=self.memory_stress, daemon=True)
        mem_thread.start()
        
        # Start CPU stress threads
        cpu_threads_list = []
        for i in range(cpu_threads):
            t = threading.Thread(target=self.cpu_stress, daemon=True)
            t.start()
            cpu_threads_list.append(t)
        
        try:
            # Monitor and log system stats
            while True:
                cpu_usage = psutil.cpu_percent(interval=1)
                mem = psutil.virtual_memory()
                
                logger.info(
                    f"CPU: {cpu_usage}% | Memory: {mem.percent}% ({mem.used // (1024**2)}MB / {mem.total // (1024**2)}MB)"
                )
                
                if self.duration and (time.time() - self.start_time) > self.duration:
                    logger.info("Duration reached, stopping...")
                    break
                
                time.sleep(2)
        
        except KeyboardInterrupt:
            logger.info("\nStress test stopped by user")
        
        finally:
            self.stop_event.set()
            mem_thread.join(timeout=2)
            for t in cpu_threads_list:
                t.join(timeout=2)
            logger.info("=== STRESS TEST STOPPED ===")

if __name__ == "__main__":
    # Aggressive stress: 80% CPU, 1000MB memory, infinite duration
    stress = StressTest(
        cpu_percent=80,
        memory_mb=1000,
        duration=None  # Infinite until stopped
    )
    stress.run(cpu_threads=8)

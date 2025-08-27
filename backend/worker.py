import time
import sys

def main():
    print("Worker started... Standing by for tasks.")

    sys.stdout.flush()
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("Worker shutting down.")

if __name__ == "__main__":
    main()
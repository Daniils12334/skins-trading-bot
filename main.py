from core.engine import run_engine
import time
if __name__ =='__main__':
    try:
        run_engine()
    except Exception:
        time.sleep(400)
        run_engine()

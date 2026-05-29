import sys
import json
import argparse
import random

def main():
    parser = argparse.ArgumentParser(description="Logi-Hex TimesFM Forecasting Stub")
    parser.add_argument("--history", type=str, required=True, help="JSON string of historical data points")
    parser.add_argument("--horizon", type=int, default=30, help="Number of future points to predict")
    
    args = parser.parse_args()
    
    try:
        # 1. Parse historical data (e.g. daily item usage)
        history_data = json.loads(args.history)
        
        # 2. In production, this is where we invoke TimesFM:
        # import timesfm
        # tfm = timesfm.TimesFm(...)
        # tfm.load_from_checkpoint(...)
        # forecast = tfm.forecast(history_data, horizon=args.horizon)
        
        # For now, we mock the forecast by returning a simple trend based on the last value
        if len(history_data) == 0:
            last_val = 0
        else:
            last_val = history_data[-1]
            
        forecast = [max(0, last_val + random.uniform(-2, 2)) for _ in range(args.horizon)]
        
        # 3. Return JSON to stdout for Rust to capture
        result = {
            "status": "success",
            "forecast": forecast
        }
        
        print(json.dumps(result))
        sys.exit(0)
        
    except Exception as e:
        error_result = {
            "status": "error",
            "message": str(e)
        }
        print(json.dumps(error_result), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

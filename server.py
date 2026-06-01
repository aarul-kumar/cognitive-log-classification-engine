import os
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import json
from typing import AsyncGenerator

app = FastAPI(title="Log Classification API")

# Get the directory of this script
script_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(script_dir, "static")

# Mount static files
try:
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
except:
    pass

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main HTML page"""
    html_file = os.path.join(static_dir, "index.html")
    try:
        if os.path.exists(html_file):
            with open(html_file, 'r', encoding='utf-8') as f:
                return f.read()
    except Exception as e:
        pass
    return """<!DOCTYPE html>
<html>
<head><title>Log Classification API</title></head>
<body>
<h1>Log Classification API</h1>
<p><a href="/docs">API Documentation</a></p>
</body>
</html>"""

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/classify/")
async def classify_logs(file: UploadFile):
    """Classify logs from a CSV file"""
    try:
        # Import classify only when needed
        from classify import classify
        
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV.")
        
        df = pd.read_csv(file.file)
        if "source" not in df.columns or "log_message" not in df.columns:
            raise HTTPException(status_code=400, detail="CSV must contain 'source' and 'log_message' columns.")

        # --- THE FIX: Unpack the dictionaries safely ---
        raw_results = classify(list(zip(df["source"], df["log_message"])))
        
        # Split the dicts into pure string columns to prevent hashing errors
        df["target_label"] = [r["target_label"] for r in raw_results]
        df["layer"] = [r["layer"] for r in raw_results]
        df["confidence"] = [r["confidence"] for r in raw_results]

        # Save output
        os.makedirs("resources", exist_ok=True)
        output_file = "resources/output.csv"
        df.to_csv(output_file, index=False)
        
        # Prepare response (value_counts now works because the column is pure strings)
        stats = df["target_label"].value_counts().to_dict()
        logs = []
        for _, row in df.iterrows():
            logs.append({
                "source": str(row["source"]),
                "log_message": str(row["log_message"]),
                "target_label": str(row["target_label"]),
                "layer": str(row.get("layer", "Pipeline Core")),
                "confidence": str(row.get("confidence", "Automated"))
            })
        
        return {
            "logs": logs,
            "stats": {
                **stats,
                "total": len(df)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        try:
            file.file.close()
        except:
            pass

@app.post("/classify-stream/")
async def classify_logs_stream(file: UploadFile):
    """Classify logs with real-time progress streaming"""
    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            from classify import classify_single_log
            
            if not file.filename.endswith('.csv'):
                yield f"data: {json.dumps({'type': 'error', 'message': 'File must be a CSV'})}\n\n"
                return
            
            df = pd.read_csv(file.file)
            if "source" not in df.columns or "log_message" not in df.columns:
                yield f"data: {json.dumps({'type': 'error', 'message': 'CSV must contain source and log_message columns'})}\n\n"
                return
            
            # Send start event
            yield f"data: {json.dumps({'type': 'start', 'total_logs': len(df)})}\n\n"
            
            results = []
            for idx, (_, row) in enumerate(df.iterrows()):
                source = str(row["source"])
                log_message = str(row["log_message"])
                
                # Send processing event
                yield f"data: {json.dumps({'type': 'processing', 'log_index': idx, 'source': source, 'message': log_message[:60]})}\n\n"
                
                # --- THE FIX: Unpack the dict for single logs too ---
                res_dict = classify_single_log(source, log_message)
                label = res_dict["target_label"]
                layer = res_dict["layer"]
                confidence = res_dict["confidence"]
                
                # Send completion event
                yield f"data: {json.dumps({'type': 'completed', 'log_index': idx, 'label': label})}\n\n"
                
                results.append({
                    "source": source,
                    "log_message": log_message,
                    "target_label": label,
                    "layer": layer,
                    "confidence": confidence
                })
            
            # Calculate stats safely
            labels = [r["target_label"] for r in results]
            from collections import Counter
            stats = dict(Counter(labels))
            
            # Save output
            os.makedirs("resources", exist_ok=True)
            output_df = pd.DataFrame(results)
            output_df.to_csv("resources/output.csv", index=False)
            
            # Send final event
            yield f"data: {json.dumps({'type': 'complete', 'logs': results, 'stats': {**stats, 'total': len(results)}})}\n\n"
        
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        finally:
            try:
                file.file.close()
            except:
                pass
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")
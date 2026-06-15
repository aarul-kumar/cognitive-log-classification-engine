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
        from classify import classify, aggregate_results
        
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV.")
        
        df = pd.read_csv(file.file)
        if "source" not in df.columns or "log_message" not in df.columns:
            raise HTTPException(status_code=400, detail="CSV must contain 'source' and 'log_message' columns.")

        # Execute classification (now returns XAI metadata)
        raw_results = classify(list(zip(df["source"], df["log_message"])))
        
        # Apply Log Clustering and Statistical Analysis
        clustered_logs, stats = aggregate_results(raw_results)

        # Save raw output to CSV for records
        os.makedirs("resources", exist_ok=True)
        output_file = "resources/output.csv"
        df["target_label"] = [r.get("target_label", "Unclassified") for r in raw_results]
        df["layer"] = [r.get("layer", "Pipeline Core") for r in raw_results]
        df["confidence"] = [r.get("confidence", "Automated") for r in raw_results]
        df["reasoning_tokens"] = [json.dumps(r.get("reasoning_tokens", [])) for r in raw_results]
        df.to_csv(output_file, index=False)
        
        # Return the expanded Enterprise Payload
        return {
            "logs": clustered_logs,
            "stats": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
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
            from classify import classify_single_log, aggregate_results
            
            if not file.filename.endswith('.csv'):
                yield f"data: {json.dumps({'type': 'error', 'message': 'File must be a CSV'})}\n\n"
                return
            
            df = pd.read_csv(file.file)
            if "source" not in df.columns or "log_message" not in df.columns:
                yield f"data: {json.dumps({'type': 'error', 'message': 'CSV must contain source and log_message columns'})}\n\n"
                return
            
            yield f"data: {json.dumps({'type': 'start', 'total_logs': len(df)})}\n\n"
            
            results = []
            for idx, (_, row) in enumerate(df.iterrows()):
                source = str(row["source"])
                log_message = str(row["log_message"])
                
                yield f"data: {json.dumps({'type': 'processing', 'log_index': idx, 'source': source, 'message': log_message[:60]})}\n\n"
                
                res_dict = classify_single_log(source, log_message)
                results.append(res_dict)
                
                yield f"data: {json.dumps({'type': 'completed', 'log_index': idx, 'label': res_dict['target_label']})}\n\n"
            
            # Perform final clustering and analysis
            clustered_logs, stats = aggregate_results(results)
            
            os.makedirs("resources", exist_ok=True)
            output_df = pd.DataFrame(results)
            # Serialize tokens for CSV storage
            if 'reasoning_tokens' in output_df.columns:
                output_df['reasoning_tokens'] = output_df['reasoning_tokens'].apply(json.dumps)
            output_df.to_csv("resources/output.csv", index=False)
            
            yield f"data: {json.dumps({'type': 'complete', 'logs': clustered_logs, 'stats': stats})}\n\n"
        
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        finally:
            try:
                file.file.close()
            except:
                pass
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")
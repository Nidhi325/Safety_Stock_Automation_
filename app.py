import os
import sys
import queue
import threading
from pathlib import Path
from flask import Flask, render_template, jsonify, request, Response, send_file

# Resolve project root
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "python_script"))

# Import database and pipeline modules
import db
from run_pipeline import run_pipeline, PIPELINE_STAGES

app = Flask(__name__)
app.config['SECRET_KEY'] = 'safety_stock_secret_key'

# Global queue for capturing pipeline logs
pipeline_log_queue = queue.Queue()
pipeline_running = False

def import_pipeline_outputs():
    """
    Import newly generated CSVs from the pipeline into the database.
    """
    print("[SERVER] Importing pipeline outputs into database...")
    prediction_path = PROJECT_ROOT / "Client_deliverable" / "Prediction.csv"
    historical_path = PROJECT_ROOT / "Data_SES" / "updated_historical_dataset.csv"
    
    predictions_imported = False
    historical_imported = False
    
    if prediction_path.exists():
        predictions_imported = db.import_predictions_csv(str(prediction_path))
        print(f"[SERVER] Predictions import status: {predictions_imported}")
        
    if historical_path.exists():
        historical_imported = db.import_historical_csv(str(historical_path))
        print(f"[SERVER] Historical dataset import status: {historical_imported}")
        
    return predictions_imported and historical_imported

def initialize_database():
    """
    Initializes the database tables and pre-populates them if they are empty.
    """
    print("[SERVER] Initializing database...")
    db.db_init()
    
    # Check if database is empty
    summary = db.get_analytics_summary()
    if not summary or summary.get("total_materials", 0) == 0:
        print("[SERVER] Database is empty. Pre-populating from existing files...")
        import_pipeline_outputs()
        print("[SERVER] Database pre-population complete.")
    else:
        print(f"[SERVER] Database active. Currently storing {summary['total_materials']} materials.")

# Run database initialization within app context
with app.app_context():
    initialize_database()

@app.route('/')
def index():
    """Serve the single page dashboard."""
    return render_template('index.html')

@app.route('/api/db-status')
def db_status():
    """Get the status and type of the database (MySQL vs SQLite)."""
    return jsonify({
        "db_type": db.get_db_type(),
        "db_status": db.get_db_status()
    })

@app.route('/api/search')
def search():
    """Search for a material by ID."""
    material_id = request.args.get('material_id', '').strip()
    if not material_id:
        return jsonify({"error": "Material ID is required"}), 400
        
    data = db.get_material_details(material_id)
    if not data:
        return jsonify({"error": f"Material ID '{material_id}' not found"}), 404
        
    return jsonify(data)

@app.route('/api/analytics')
def analytics():
    """Get aggregated analytics summary."""
    data = db.get_analytics_summary()
    if not data:
        return jsonify({"error": "No data available in the database. Run the pipeline first."}), 404
    return jsonify(data)

@app.route('/api/inventory')
def inventory():
    """Get a paginated, filterable list of materials."""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 15))
    search_query = request.args.get('search', '').strip()
    action_filter = request.args.get('action', None)
    status_filter = request.args.get('status', None)
    abc_filter = request.args.get('abc', None)
    xyz_filter = request.args.get('xyz', None)
    
    # Normalize empty filters to None
    action_filter = None if action_filter == 'all' or not action_filter else action_filter
    status_filter = None if status_filter == 'all' or not status_filter else status_filter
    abc_filter = None if abc_filter == 'all' or not abc_filter else abc_filter
    xyz_filter = None if xyz_filter == 'all' or not xyz_filter else xyz_filter
    
    data = db.get_inventory_list(
        page=page,
        per_page=per_page,
        search_query=search_query,
        action_filter=action_filter,
        status_filter=status_filter,
        abc_filter=abc_filter,
        xyz_filter=xyz_filter
    )
    return jsonify(data)

@app.route('/api/download')
def download():
    """Download the final Prediction.csv file."""
    prediction_path = PROJECT_ROOT / "Client_deliverable" / "Prediction.csv"
    if not prediction_path.exists():
        return jsonify({"error": "Prediction file not found. Run the pipeline first."}), 404
    return send_file(str(prediction_path), as_attachment=True, attachment_filename="Prediction.csv")

def run_pipeline_thread(consumption_path, leadtime_path):
    """Target function for background pipeline execution."""
    global pipeline_running
    pipeline_running = True
    try:
        success, message = run_pipeline(
            str(consumption_path),
            str(leadtime_path),
            pipeline_log_queue
        )
        if success:
            pipeline_log_queue.put(("DONE", message))
        else:
            pipeline_log_queue.put(("FAIL", message))
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        pipeline_log_queue.put(("LOG", f"[UNEXPECTED ERROR]\n{tb}\n"))
        pipeline_log_queue.put(("FAIL", str(e)))
    finally:
        pipeline_running = False

@app.route('/api/run-pipeline', methods=['POST'])
def trigger_pipeline():
    """Trigger the safety stock pipeline with uploaded Excel files."""
    global pipeline_running
    if pipeline_running:
        return jsonify({"error": "Pipeline is already running"}), 400
        
    if 'consumption' not in request.files or 'leadtime' not in request.files:
        return jsonify({"error": "Both Consumption and LeadTime files are required"}), 400
        
    consumption_file = request.files['consumption']
    leadtime_file = request.files['leadtime']
    
    if not consumption_file.filename or not leadtime_file.filename:
        return jsonify({"error": "Invalid file upload"}), 400
        
    # Ensure Monthly_upload folder exists
    upload_dir = PROJECT_ROOT / "Monthly_upload"
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Save files to standard paths
    consumption_path = upload_dir / "Consumption.xlsx"
    leadtime_path = upload_dir / "LeadTime.xlsx"
    
    consumption_file.save(str(consumption_path))
    leadtime_file.save(str(leadtime_path))
    
    # Empty the queue before starting
    while not pipeline_log_queue.empty():
        try:
            pipeline_log_queue.get_nowait()
        except queue.Empty:
            break
            
    # Start pipeline in background thread
    thread = threading.Thread(
        target=run_pipeline_thread,
        args=(consumption_path, leadtime_path),
        daemon=True
    )
    thread.start()
    
    return jsonify({"status": "started", "message": "Pipeline started successfully"})

@app.route('/api/pipeline-status')
def pipeline_status():
    """Get current pipeline running status."""
    return jsonify({"running": pipeline_running})

@app.route('/api/pipeline-logs')
def stream_pipeline_logs():
    """Stream pipeline execution logs via Server-Sent Events (SSE)."""
    def generate():
        while True:
            try:
                # Retrieve logs from the queue with a timeout to allow checking if thread is alive
                kind, payload = pipeline_log_queue.get(timeout=10)
                
                if kind == "LOG":
                    # Format log lines nicely for SSE
                    yield f"data: LOG|{payload}\n\n"
                elif kind == "STAGE_START":
                    yield f"data: STAGE_START|{payload}\n\n"
                elif kind == "STAGE_DONE":
                    yield f"data: STAGE_DONE|{payload}\n\n"
                elif kind == "STAGE_FAIL":
                    yield f"data: STAGE_FAIL|{payload}\n\n"
                elif kind == "DONE":
                    # Import the new results in the database
                    db_success = import_pipeline_outputs()
                    db_msg = "Database updated successfully." if db_success else "Database update failed."
                    yield f"data: DONE|{payload} \\n\\n [SERVER] {db_msg}\n\n"
                    break
                elif kind == "FAIL":
                    yield f"data: FAIL|{payload}\n\n"
                    break
            except queue.Empty:
                # Connection keep-alive
                yield "data: PING|keepalive\n\n"
                if not pipeline_running and pipeline_log_queue.empty():
                    break
                    
    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    # Initialize app manually if running from command line
    db.db_init()
    import_pipeline_outputs()
    
    # Run the server on port 5000
    print("[SERVER] Starting Flask development server on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)

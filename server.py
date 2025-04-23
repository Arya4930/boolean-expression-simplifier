from flask import Flask, request, jsonify
from flask_cors import CORS
from quincy_mcClusky import simplify_sop

app = Flask(__name__)
CORS(app)

@app.route('/runSimulation', methods=['POST'])
def run_simulation():
    try:
        data = request.get_json()
        sop_expression = data.get('sop', '').strip()

        if not sop_expression:
            return jsonify({"success": False, "error": "No SOP expression provided"}), 400

        result = simplify_sop(sop_expression)
        print(result)

        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": f"Server error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
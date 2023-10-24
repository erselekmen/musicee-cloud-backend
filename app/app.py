from flask import Flask, jsonify, request
from flask_pymongo import PyMongo

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://mongodb:27017/myDatabase"
mongo = PyMongo(app)

@app.route('/add_note', methods=['POST'])
def add_note():
    note = request.json
    notes = mongo.db.notes
    note_id = notes.insert_one(note).inserted_id
    return jsonify({'result': str(note_id)})

@app.route('/get_notes', methods=['GET'])
def get_notes():
    notes = mongo.db.notes
    result = list(notes.find({}, {'_id': 0}))
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)

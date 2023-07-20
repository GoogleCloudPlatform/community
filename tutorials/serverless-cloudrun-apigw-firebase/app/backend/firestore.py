import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from google.cloud import firestore
from google.oauth2 import service_account

app = Flask(__name__)
CORS(app)

client = firestore.Client(project="gcp-three-tier-ref-app")
employees_app_ref = client.collection('employees_app').document('employees')
employees_ref = employees_app_ref.collection('info')


@app.route('/employees', methods=['GET'])
def get_employees():
    """
            get_employees() : Fetches documents from Firestore collection as JSON
            employee : Return document that matches query ID
            all_employees : Return all documents
        """
    try:
        # Check if ID was passed to URL query
        employee_id = request.args.get('id')
        if employee_id:
            employee = employees_ref.document(employee_id).get()
            return jsonify(employee.to_dict()), 200
        else:
            all_employees = [doc.to_dict() for doc in employees_ref.stream()]
            return jsonify(all_employees), 200
    except Exception as e:
        return f"An Error Occurred: {e}"


@app.route('/employee', methods=['POST', 'PUT'])
def add_update_employee():
    json_ = request.get_json()
    if 'id' not in json_:
        return 'Precondition Failed', 412

    doc_ref = employees_ref.document(u'{}'.format(json_.get('id')))
    try:
        doc_ref.set(json_)
        response = 'Employee Added or Updated'
        return jsonify(response), 201
    except (RuntimeError, TypeError, NameError):
        print(RuntimeError);
        return 500


@app.route('/employeesecure', methods=['POST', 'PUT'])
def add_update_employee_secure():
    json_ = request.get_json()
    if 'id' not in json_:
        return 'Precondition Failed', 412

    doc_ref = employees_ref.document(u'{}'.format(json_.get('id')))
    doc_ref.set(json_)
    response = 'Employee Added or Updated'
    return jsonify(response), 201


@app.route('/employee', methods=['DELETE'])
def delete_employee():
    employee_id = request.args.get('id')
    if employee_id:
        try:
            employee = employees_ref.document(employee_id).delete()
            response = 'Employee Deleted!'
            return jsonify(response), 201
        except (RuntimeError, TypeError, NameError):
            print(RuntimeError);
            return 500
    else:
        return 'Precondition Failed', 412


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 80)))

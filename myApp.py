from flask import Flask, request
import csv

app = Flask(__name__)

data_dict = {}
    
with open("./Results_File.csv", mode='r') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    for row in csv_reader:
        key = row['Image']
        data_dict[key] = row['Results']

@app.route('/', methods=['POST'])
def image_classification():
    if request.method == 'POST':
        print(request)
        input_file = request.files['inputFile'].filename
        responseStr =  input_file[:8] + ':' + data_dict[input_file[:8]]
        return responseStr, 200, {'Content-Type': 'text/plain'}

if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=8000)

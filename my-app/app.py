from flask import Flask, render_template, jsonify
import datetime
app = Flask(__name__)

@app.route('/')
def sample_page():
    year = datetime.datetime.now().year
    return render_template('index.html', year=year)

@app.route('/healthcheck')
def health_check():
    return jsonify({'health_status': 'OK'})

if __name__ =='__main__':
    app.run(host='0.0.0.0', port=8081)
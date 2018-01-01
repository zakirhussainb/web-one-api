from flask import Flask, request, jsonify
import extractor as ext

app = Flask(__name__)


@app.route("/")
def is_alive():
    return "WebOne API Services is Ready"


@app.route("/extract")
def extract():
    page_url = request.args.get("pageURL")
    print(page_url)
    response = ext.get_extracted_content(page_url)
    return jsonify(response)


if __name__ == "__main__":
    app.run(threaded=True)

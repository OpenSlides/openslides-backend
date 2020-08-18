from flask import Flask, request

app = Flask(__name__)

app.logger.info("Started Dummy-Presenter")


# for testing
@app.route("/system/presenter", methods=["POST"])
def dummy_presenter():
    app.logger.debug(f"dummy_presenter gets: {request.json}")
    meeting_id = request.json[0]["data"]["meeting_id"]
    if meeting_id == 12:
        return "[null]"
    if meeting_id == 13:
        return "XXX", 500
    return f"[{meeting_id}]"

from flask import Flask, jsonify, request

app = Flask(__name__)

app.logger.info("Started Dummy-Presenter")


# for testing
@app.route("/system/presenter/handle_request", methods=["POST"])
def dummy_presenter():
    app.logger.debug(f"dummy_presenter gets: {request.json}")
    file_id = request.json[0]["data"]["mediafile_id"]

    # Valid response from presenter, but not found in DB
    if file_id == 1:
        return jsonify([{"ok": True, "filename": "Does not exist"}])

    # OK-cases for dummy data
    if file_id == 2:
        return jsonify([{"ok": True, "filename": "A.txt"}])
    if file_id == 3:
        return jsonify([{"ok": True, "filename": "in.jpg"}])

    # OK-cases for uploaded data
    if file_id in (4, 5, 6, 7):
        return jsonify([{"ok": True, "filename": str(file_id)}])

    # invalid responses
    if file_id == 10:
        return jsonify([None])
    if file_id == 11:
        return "some text"
    if file_id == 12:
        return "An error", 500
    if file_id == 13:
        return {"ok": False}
    if file_id == 14:
        return jsonify([{"ok": True}])

    # not found or no perms
    if file_id == 20:
        return jsonify([{"ok": False}])

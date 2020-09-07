from flask import Flask, jsonify, request

app = Flask(__name__)

app.logger.info("Started Dummy-Presenter")


# for testing
@app.route("/system/presenter", methods=["POST"])
def dummy_presenter():
    app.logger.debug(f"dummy_presenter gets: {request.json}")
    mediafile_id = request.json[0]["data"]["mediafile_id"]

    # Valid response from presenter, but not found in DB
    if mediafile_id == 1:
        return jsonify([{"ok": True, "filename": "Does not exist"}])

    # OK-cases for dummy data
    if mediafile_id == 2:
        return jsonify([{"ok": True, "filename": "A.txt"}])
    if mediafile_id == 3:
        return jsonify([{"ok": True, "filename": "in.jpg"}])

    # OK-cases for uploaded data
    if mediafile_id in (4, 5, 6, 7):
        return jsonify([{"ok": True, "filename": str(mediafile_id)}])

    # invalid responses
    if mediafile_id == 10:
        return jsonify([None])
    if mediafile_id == 11:
        return "some text"
    if mediafile_id == 12:
        return "An error", 500
    if mediafile_id == 13:
        return {"ok": False}
    if mediafile_id == 14:
        return jsonify([{"ok": True}])

    # not found or no perms
    if mediafile_id == 20:
        return jsonify([{"ok": False}])

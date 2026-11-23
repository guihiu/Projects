from pathlib import Path
from uuid import uuid4


from flask import Flask
from flask import render_template, request, send_file
from Generator import create, save

app = Flask(__name__)

UPLOAD_FOLDER = Path(app.root_path) / "uploads"
OUTPUT_FOLDER = Path(app.root_path) / "generated"


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        uploaded_file = request.files.get("file_xlsx")
        number_text = request.form.get("number", "").strip()

        if uploaded_file is None or not uploaded_file.filename:
            return render_template("index.html", error="Please choose an .xlsx file."), 400
        if Path(uploaded_file.filename).suffix.lower() != ".xlsx":
            return render_template("index.html", error="The uploaded file must be an .xlsx file."), 400
        try:
            number = int(number_text)
            if number < 1:
                raise ValueError
        except ValueError:
            return render_template("index.html", error="Enter a positive whole number."), 400

        file_id = uuid4().hex
        UPLOAD_FOLDER.mkdir(exist_ok=True)
        OUTPUT_FOLDER.mkdir(exist_ok=True)
        file_xlsx = str(UPLOAD_FOLDER / f"{file_id}.xlsx")
        new_file = str(OUTPUT_FOLDER / f"{file_id}.xlsx")
        save(file_xlsx, uploaded_file)

        try:
            generated_file = create(file_xlsx, number)
            save(new_file, generated_file)

        except ValueError as error:
            return render_template("index.html", error=str(error)), 400

        return send_file(new_file, as_attachment=True, download_name="gerados.xlsx")

    return render_template("index.html")


if __name__ == "__main__":
    app.run()
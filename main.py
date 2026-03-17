import os, re, shutil, time
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

BASE_DIR = "tmp_files"
os.makedirs(BASE_DIR, exist_ok=True)


def split_by_month(input_file, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    files = {}
    last_valid_date = None
    date_pattern = r"^\[?\s*(\d{1,2}/\d{1,2}/\d{2})"

    with open(input_file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            match = re.match(date_pattern, line)
            if match:
                try:
                    date = datetime.strptime(match.group(1), "%m/%d/%y")
                    last_valid_date = date
                except:
                    continue
            else:
                if last_valid_date is None:
                    continue
                date = last_valid_date

            month_key = date.strftime("%B-%Y")
            if month_key not in files:
                file_path = os.path.join(output_dir, f"{month_key}.txt")
                files[month_key] = open(file_path, "a", encoding="utf-8")
            files[month_key].write(line)

    for f in files.values():
        f.close()


@app.get("/", response_class=HTMLResponse)
def home():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.post("/upload/")
async def upload(file: UploadFile = File(...)):
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only TXT files are supported.")

    timestamp = int(time.time())
    input_path = os.path.join(BASE_DIR, f"{timestamp}_input.txt")
    output_dir = os.path.join(BASE_DIR, f"{timestamp}_output")

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    split_by_month(input_path, output_dir)

    zip_path = f"{output_dir}.zip"
    shutil.make_archive(output_dir, 'zip', output_dir)

    return FileResponse(zip_path, filename="month_wise_output.zip", media_type="application/zip")
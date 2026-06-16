import fitz
import os

PDF_FOLDER = "syllabus"
OUTPUT_FOLDER = "output"

for root, dirs, files in os.walk(PDF_FOLDER):

    for file in files:

        if not file.lower().endswith(".pdf"):
            continue

        pdf_path = os.path.join(root, file)

        relative_dir = os.path.relpath(
            root,
            PDF_FOLDER
        )

        pdf_name = os.path.splitext(file)[0]

        output_dir = os.path.join(
            OUTPUT_FOLDER,
            relative_dir,
            pdf_name
        )

        os.makedirs(output_dir, exist_ok=True)

        try:
            pdf = fitz.open(pdf_path)

            text = ""

            for page in pdf:
                text += page.get_text()
                text += "\n"

            pdf.close()

            with open(
                os.path.join(output_dir, "raw.txt"),
                "w",
                encoding="utf-8"
            ) as f:
                f.write(text)

            print(f"✅ {pdf_path}")

        except Exception as e:
            print(f"❌ {pdf_path}")
            print(e)

print("🎉 Finished")
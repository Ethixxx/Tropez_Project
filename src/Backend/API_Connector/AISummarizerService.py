import openai
import requests
import os
import fitz  # PyMuPDF
from docx import Document
import pathlib

class AISummarizerService:        
    def summarize_from_external_service(filename: pathlib.Path) -> str:
        """
        Fetch a document from an external service and summarize it in exactly 2 sentences.
        
        :param service_name: The name of the service (e.g., 'direct_url', 'github', 'dropbox').
        :param link: The direct link to the file.
        :return: A 2-sentence summary.
        """

        content = AISummarizerService.read_file_contents(filename)
        os.remove(filename)  # Cleanup the temp file after reading

        if "Error reading" in content or content == "Unsupported file format.":
            return content

        return AISummarizerService.summarize_content(content)

    def extract_text_from_pdf(path):
        text = ""
        with fitz.open(path) as doc:
            for page in doc:
                text += page.get_text()
        return text

    def extract_text_from_docx(path):
        doc = Document(path)
        return "\n".join([para.text for para in doc.paragraphs])

    def summarize_content(content):
        prompt = (
            "Summarize the following file content in exactly 2 sentences. "
            "Be concise and informative, and do not exceed 2 sentences total.\n\n"
            f"{content[:4000]}"
        )

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes uploaded documents."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5
            )
            return response['choices'][0]['message']['content'].strip()
        
        except Exception as e:
            print(f"\nFULL OpenAI ERROR:\n{e}\n")
            return f"Error calling OpenAI API: {e}"

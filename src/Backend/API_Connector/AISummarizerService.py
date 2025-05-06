from openai import OpenAI
import requests
import os
import fitz  # PyMuPDF
from docx import Document
import pathlib

class AISummarizerService: 
    @staticmethod       
    def summarize_from_external_service(filename: pathlib.Path) -> str:
        """
        Fetch a document from an external service and summarize it in exactly 2 sentences.
        
        :param service_name: The name of the service (e.g., 'direct_url', 'github', 'dropbox').
        :param link: The direct link to the file.
        :return: A 2-sentence summary.
        """

        try:
            content = AISummarizerService.read_file_contents(filename)
            if content:
                print(f"Successfully read content from {filename}")
                content = AISummarizerService.summarize_content(content)
            os.remove(filename)  # Cleanup the temp file after reading
            return content
        except Exception as e:
            print(f"could not read downloaded file: {e}")

        return AISummarizerService.summarize_content(content)

    @staticmethod
    def read_file_contents(filepath):
        ext = os.path.splitext(filepath)[-1].lower()

        try:
            if ext == ".txt":
                with open(filepath, 'r', encoding='utf-8') as file:
                    return file.read()

            elif ext == ".pdf":
                return AISummarizerService.extract_text_from_pdf(filepath)

            elif ext == ".docx":
                return AISummarizerService.extract_text_from_docx(filepath)

            else:
                raise ValueError("Unsupported file type. Supported types are: .txt, .pdf, .docx")

        except Exception as e:
            raise ValueError(f"Error reading file {filepath}: {e}")
    
    @staticmethod
    def extract_text_from_pdf(path):
        text = ""
        with fitz.open(path) as doc:
            for page in doc:
                text += page.get_text()
        return text

    @staticmethod
    def extract_text_from_docx(path):
        doc = Document(path)
        return "\n".join([para.text for para in doc.paragraphs])

    @staticmethod
    def summarize_content(content):
        prompt = (
            f"{content[:4000]}"
        )

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an assistant that generates searchable captions for documents. The filename will be stored and searched seperately. The response must be consice because it must fit on a small screen do not exceed 2 sentences total. Do not include headers or descriptors \n\n"},
                    {"role": "user", "content": prompt}],
                temperature=0.5
            )
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"\nFULL OpenAI ERROR:\n{e}\n")
            return f"Error calling OpenAI API: {e}"

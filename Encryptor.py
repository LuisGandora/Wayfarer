#Main Scripts used for managing encrytion types
#Will use tradition hash and then add the path at the end so SHA256(message+derived_path_data)
#Serves to make it hard to duplicate between documents

import hashlib
import math
import numpy as np
import PyPDF2
import io

#Generate 3D path
def generate_3d_path(seed: float, points: int = 100):
    np.random.seed(int(seed * 1000))
    path = []
    t_values = np.linspace(0, 2 * math.pi, points)
    for t in t_values:
        x = math.cos(t) + np.random.normal(0, 0.01)
        y = math.sin(t) + np.random.normal(0, 0.01)
        z = t / (2 * math.pi) + np.random.normal(0, 0.01)
        path.append((x, y, z))
    return path

#Helper method to join all values in the path array
def path_to_string(path):
    return ''.join(f'{x:.5f},{y:.5f},{z:.5f};' for x, y, z in path)

#Procedural path-based hash 
def procedural_path_hash(data: bytes, seed: float):
    path = generate_3d_path(seed)
    path_str = path_to_string(path)
    combined = data + path_str.encode()
    return hashlib.sha256(combined).hexdigest()

#Read PDF 
def read_pdf_bytes(pdf_path):
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        text = ''
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
        return text.encode()

#Sign the Document
def sign_pdf_embed(pdf_path: str, seed: float, output_path: str):
    # Read PDF content for hashing
    data = read_pdf_bytes(pdf_path)
    signature = procedural_path_hash(data, seed)
    
    # Open original PDF
    reader = PyPDF2.PdfReader(pdf_path)
    writer = PyPDF2.PdfWriter()

    # Copy pages
    for page in reader.pages:
        writer.add_page(page)
    
    # Add the signature to the metadata
    metadata = reader.metadata or {}
    metadata.update({"/Signature": signature})
    writer.add_metadata(metadata)

    # Write signed PDF
    output_bytes = io.BytesIO()
    writer.write(output_bytes)
    output_bytes.seek(0)
    return output_bytes, signature

#Verify the document
def verify_pdf_embedded(pdf_path: str, signature: str):
    reader = PyPDF2.PdfReader(pdf_path)
    metadata = reader.metadata or {}
    embedded_signature = str(metadata.get("/Signature"))

    if not embedded_signature:
        return "No embedded signature found in PDF metadata."

    
    if signature == embedded_signature:
        return "Embedded signature matches. PDF is authentic."
    else:
        return "Signature mismatch! PDF may have been altered."
    
if __name__ == "__main__":
    pdf_original = "example.pdf"
    pdf_signed = "example_signed.pdf"
    seed = 42.3313

    # Embed signature into PDF metadata (Remember only in streamlit)
    output, signature = sign_pdf_embed(pdf_original, seed, pdf_signed)
    print(signature)
    print(output)
    
    #Test verify in streamlit

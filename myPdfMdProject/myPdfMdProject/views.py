

#home page view
import io
import re
from .utils.converter import convert_pdf_to_md

from django.http import FileResponse
from django.shortcuts import render 

def home(request):
    return render(request, "home.html")

def upload_file(request):
    if request.method == 'POST':
        
        if 'myfile' not in request.FILES or not request.FILES['myfile']:
            return render(request, 'home.html', {'error': 'No file selected. Please choose a PDF.'})

        uploaded_file = request.FILES['myfile']

        if not uploaded_file.name.lower().endswith('.pdf'):
            return render(request, 'home.html', {'error': 'Only PDF files allowed'})
        

        # আপনার কনভার্টার ফাংশন কল করুন
        md_text = convert_pdf_to_md(uploaded_file)

        # সেশনে সেভ করুন
        request.session['md_content'] = md_text
        return render(request, 'result.html', {'md_content': md_text})


    return render(request, "home.html")


def download_md(request):
    md_content = request.session.get('md_content', '')
    
    # Create an in-memory file to avoid saving to disk
    buffer = io.BytesIO(md_content.encode('utf-8'))
    response = FileResponse(buffer, as_attachment=True, filename='generated.md')
    return response


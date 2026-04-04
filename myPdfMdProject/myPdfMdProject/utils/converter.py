import os
import pdfplumber
import re

def convert_pdf_to_md(input_pdf_file):
    

    try:
        # ১. ফাইলটি সাময়িকভাবে সেভ করা (অনেক লাইব্রেরি সরাসরি অবজেক্ট নিতে পারে না)
        temp_path = f"temp_{input_pdf_file.name}"
        with open(temp_path, 'wb+') as destination:
            for chunk in input_pdf_file.chunks():
                destination.write(chunk)

        # ২. আপনার আসল কনভার্টার ফাংশন কল করা
        
        md_content = get_markdown_representation(temp_path)

        # ৩. কাজ শেষ হলে টেম্পোরারি ফাইলটি ডিলিট করে দিন
        if os.path.exists(temp_path):
            os.remove(temp_path)

        return md_content
    except Exception as e:
        return f"Error: {str(e)}"

def is_inside_table(word, table_bboxes):
    """চেক করে শব্দটি কোনো টেবিলের বাউন্ডারির ভেতরে কি না"""
    for bbox in table_bboxes:
        # bbox = (x0, top, x1, bottom)
        if (word['x0'] >= bbox[0] and word['top'] >= bbox[1] and 
            word['x1'] <= bbox[2] and word['bottom'] <= bbox[3]):
            return True
    return False

def get_markdown_representation(pdf_path):
    md_content = ""
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            #  table detection and find bounding boxes of tables
            tables = page.find_tables()
            table_bboxes = [t.bbox for t in tables]
            
            # extract all words with their attributes (size, fontname) to determine formatting
            all_words = page.extract_words(extra_attrs=["size", "fontname"])
            print(type (all_words))  # এটা দেখার জন্য যে all_words আসলে কি ধরনের ডাটা
            if not all_words: continue
            
            #  non table words 
            non_table_words = [w for w in all_words if not is_inside_table(w, table_bboxes)]

            # ordering of line words based on 'top' position 
            lines = {}
            for word in non_table_words:
                top = round(word['top'], 1)
                if top not in lines:
                    lines[top] = []
                lines[top].append(word)

            # element for final ordering (text and tables together)
            elements = []
            for top, line_words in lines.items():
                elements.append({'top': top, 'type': 'text', 'data': line_words})
            
            for t in tables:
                elements.append({'top': t.bbox[1], 'type': 'table', 'data': t.extract()})

            # sorting elements by their vertical position on the page
            elements.sort(key=lambda x: x['top'])

            #  formatting text according to md rules
            for el in elements:
                if el['type'] == 'text':
                    line_words = el['data']
                    formatted_words = []
                    max_size = 0
                    
                    for w in line_words:
                        text = w['text']
                        font = w['fontname'].lower()
                        size = w['size']
                        if size > max_size: max_size = size
                        
                        is_bold = "bold" in font
                        is_italic = "italic" in font or "oblique" in font
                        
                        if is_bold and is_italic:
                            text = f"***{text}***"
                        elif is_bold:
                            text = f"**{text}**"
                        elif is_italic:
                            text = f"*{text}*"
                        formatted_words.append(text)

                    line_text = " ".join(formatted_words)
                    
                    if max_size > 18:
                        md_content += f"# {line_text}\n\n"
                    elif max_size > 14:
                        md_content += f"## {line_text}\n\n"
                    elif re.match(r'^(\d+\.\s+|[\u2022\u00b7\u002d]\s+)', line_text.strip()):
                        md_content += f"{line_text}\n"
                    else:
                        md_content += f"{line_text}  \n"

                elif el['type'] == 'table':
                    table_data = el['data']
                    md_content += "\n"
                    for i, row in enumerate(table_data):
                        clean_row = [str(c).replace('\n', ' ') if c else "" for c in row]
                        md_content += "| " + " | ".join(clean_row) + " |\n"
                        if i == 0:
                            md_content += "| " + " | ".join(["---"] * len(row)) + " |\n"
                    md_content += "\n"

    return md_content

if __name__ == "__main__":
    convert_pdf_to_md()

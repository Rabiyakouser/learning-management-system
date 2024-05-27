from pypdf import PdfReader

path = 'static\pdf\python (1).pdf'
print(path)

reader = PdfReader(path) 

print(len(reader.pages)) 

i = 0
while i < len(reader.pages):
    page = reader.pages[0] 

    text = page.extract_text()
    print(text)
    if text:
        break
    i += 1

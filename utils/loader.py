import os
from langchain_community.document_loaders import TextLoader, PyPDFLoader
# A nova forma de importar o splitter:
from langchain_text_splitters import CharacterTextSplitter 

def carregar_documentos(pasta="data/leis/"):
    documentos_totais = []
    
    for ficheiro in os.listdir(pasta):
        caminho_completo = os.path.join(pasta, ficheiro)
        
        if ficheiro.endswith(".txt"):
            loader = TextLoader(caminho_completo, encoding='utf-8')
            documentos_totais.extend(loader.load())
            
        elif ficheiro.endswith(".pdf"):
            loader = PyPDFLoader(caminho_completo)
            documentos_totais.extend(loader.load())
            
    # Dividir o texto em partes pequenas para a IA não se perder
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    docs_divididos = text_splitter.split_documents(documentos_totais)
    
    return docs_divididos

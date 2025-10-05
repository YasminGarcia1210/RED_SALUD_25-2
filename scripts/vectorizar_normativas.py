#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import openai
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from pathlib import Path
from PyPDF2 import PdfReader

# === CONFIGURACIÓN ===
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

DB_PARAMS = {
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT"),
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
}

DIRECTORIO = Path("data")

# === FUNCIONES ===

def extraer_texto_pdf(ruta):
    reader = PdfReader(ruta)
    texto = ""
    for page in reader.pages:
        texto += page.extract_text() or ""
    return texto.strip()

def obtener_embeddings(texto):
    response = openai.embeddings.create(
        model="text-embedding-3-small",
        input=texto
    )
    return response.data[0].embedding

def guardar_embeddings(docs):
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS normativas_embeddings (
            id SERIAL PRIMARY KEY,
            filename TEXT,
            chunk TEXT,
            embedding vector(1536)
        );
    """)
    execute_values(cur,
        "INSERT INTO normativas_embeddings (filename, chunk, embedding) VALUES %s",
        [(d['filename'], d['chunk'], d['embedding']) for d in docs]
    )
    conn.commit()
    conn.close()

def dividir_texto(texto, n=800):
    palabras = texto.split()
    for i in range(0, len(palabras), n):
        yield " ".join(palabras[i:i+n])

# === PROCESO ===
docs = []
for archivo in DIRECTORIO.glob("*.pdf"):
    texto = extraer_texto_pdf(archivo)
    for chunk in dividir_texto(texto):
        embedding = obtener_embeddings(chunk)
        docs.append({
            "filename": archivo.name,
            "chunk": chunk,
            "embedding": embedding
        })

guardar_embeddings(docs)
print(f"✅ Vectorización completa. Se guardaron {len(docs)} fragmentos en la BD.")

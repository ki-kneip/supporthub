#!/usr/bin/env python
"""Falha se backend/openapi.yml estiver desatualizado em relacao ao schema atual da API."""
import os
import subprocess
import sys
import tempfile

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
COMMITTED_SCHEMA = os.path.join(BACKEND_DIR, "openapi.yml")


def main():
    fd, tmp_path = tempfile.mkstemp(suffix=".yml")
    os.close(fd)

    try:
        result = subprocess.run(
            [sys.executable, "manage.py", "spectacular", "--file", tmp_path],
            cwd=BACKEND_DIR,
        )
        if result.returncode != 0:
            print("Falha ao gerar o schema OpenAPI.")
            return 1

        with open(tmp_path, encoding="utf-8") as f:
            generated = f.read()
        with open(COMMITTED_SCHEMA, encoding="utf-8") as f:
            committed = f.read()
    finally:
        os.remove(tmp_path)

    if generated != committed:
        print("backend/openapi.yml esta desatualizado em relacao a API atual.")
        print("Rode (dentro de backend/): python manage.py spectacular --file openapi.yml")
        print("e inclua o arquivo atualizado no commit.")
        return 1

    print("backend/openapi.yml esta atualizado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

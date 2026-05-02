@echo off
REM Tribunal IA Portugal — Iniciar Interface Web (Windows)
setlocal EnableDelayedExpansion

echo ========================================
echo  🏛️  Tribunal IA Portugal
echo  Iniciando interface web...
echo ========================================
echo.

REM Verificar se estamos na pasta certa
if not exist "app.py" (
    echo ❌ ERRO: Nao encontrei app.py
    echo    Certifica-te que executas este .bat na pasta do projeto.
    echo    Pasta atual: %CD%
    pause
    exit /b 1
)

REM Verificar .env
if not exist ".env" (
    echo ⚠️  .env nao encontrado.
    if exist ".env.example" (
        echo    A copiar .env.example para .env...
        copy .env.example .env
        echo ✅ Copiado! Agora edita o ficheiro .env e coloca a tua chave API.
        notepad .env
        echo.
        echo ⚠️  Reinicia este .bat depois de configurares o .env
        pause
        exit /b 1
    ) else (
        echo ❌ .env.example tambem nao existe!
        echo    Cria um ficheiro .env com: OPENROUTER_API_KEY=sua_chave
        pause
        exit /b 1
    )
)

echo ✅ .env encontrado

REM --- TENTATIVA 1: streamlit ja esta no PATH? ---
streamlit --version >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ Streamlit encontrado no PATH do sistema
    goto :RUN
)

REM --- TENTATIVA 2: venv padrao Windows (.venv\Scripts) ---
if exist ".venv\Scripts\activate.bat" (
    echo ✅ Ambiente virtual encontrado (.venv\Scripts)
    echo ✅ A ativar...
    call .venv\Scripts\activate.bat
    goto :RUN
)

REM --- TENTATIVA 3: venv com outro nome (venv\Scripts) ---
if exist "venv\Scripts\activate.bat" (
    echo ✅ Ambiente virtual encontrado (venv\Scripts)
    echo ✅ A ativar...
    call venv\Scripts\activate.bat
    goto :RUN
)

REM --- TENTATIVA 4: venv criado no WSL (pasta bin) ---
if exist ".venv\bin\activate" (
    echo ⚠️  Detectado ambiente WSL/Linux (.venv\bin)
    echo    Tenta executar: source .venv/bin/activate ^&^& streamlit run app.py
    pause
    exit /b 1
)

REM --- TENTATIVA 5: tentar python -m streamlit diretamente ---
python -c "import streamlit" >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ Streamlit instalado globalmente
    goto :RUN_PYTHON
)

REM --- FALHOU TUDO ---
echo ❌ Nao consegui encontrar o Streamlit.
echo.
echo Possiveis solucoes:
echo  1. Cria o ambiente virtual:
echo        python -m venv .venv
echo        .venv\Scripts\activate
echo        pip install -r requirements.txt
echo.
echo  2. Ou instala globalmente:
echo        pip install streamlit
echo.
pause
exit /b 1

REM --- EXECUTAR ---
:RUN
echo 🚀 A iniciar Streamlit...
echo.
echo    O browser vai abrir automaticamente em http://localhost:8501
echo    Se nao abrir, copia esse link para o teu navegador.
echo    Para parar, fecha esta janela ou pressiona CTRL+C
echo ========================================
echo.
streamlit run app.py
goto :END

:RUN_PYTHON
echo 🚀 A iniciar Streamlit (via python -m)...
echo.
echo    O browser vai abrir automaticamente em http://localhost:8501
echo    Se nao abrir, copia esse link para o teu navegador.
echo    Para parar, fecha esta janela ou pressiona CTRL+C
echo ========================================
echo.
python -m streamlit run app.py
goto :END

:END
echo.
echo ========================================
echo Streamlit terminou.
pause

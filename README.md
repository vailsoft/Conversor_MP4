# Conversor MP4

Aplicativo gráfico em Python/Tkinter para converter um ou vários vídeos para MP4 (vídeo H.264 + áudio AAC).

## Requisitos
- Windows 10/11 (também pode funcionar em Linux com Tkinter instalado)
- Python 3.10 ou superior
- FFmpeg: no Windows o programa baixa sozinho (~30 MB) na primeira execução (precisa de internet); no Linux instale pelo gerenciador de pacotes
- tkinterdnd2 (para arrastar e soltar; o `iniciar.bat` instala automaticamente)

## FFmpeg automático (Windows)
Na primeira vez que o programa abre sem encontrar o FFmpeg, ele baixa uma versão leve (cerca de 30 MB, vinda do PyPI, com verificação de integridade; se falhar, tenta um build maior) para `%LOCALAPPDATA%\ConversorMP4\ffmpeg` e passa a usá-lo nas próximas execuções. Não é preciso mexer no PATH do Windows. Se você já tiver o FFmpeg no PATH, ele é usado e nada é baixado.
Para remover, apague a pasta `%LOCALAPPDATA%\ConversorMP4`.

## Executar
1. Extraia a pasta do projeto.
2. Clique duas vezes em `iniciar.bat` ou execute:
   `python conversor_mp4.py`

## Criar um EXE
Com Python instalado, execute `criar_exe.bat`. O script instalará PyInstaller e tentará gerar `dist\ConversorMP4.exe`, já com o ícone `icone.ico` (também usado na janela do programa).
Para trocar o ícone, substitua o arquivo `icone.ico` por outro (formato .ico, de preferência com vários tamanhos) antes de gerar o EXE.
O executável também baixa o FFmpeg sozinho na primeira execução.

## Arrastar e soltar
Arraste arquivos de vídeo (ou pastas inteiras) para a janela. Arquivos que não são vídeo são ignorados.
Se o `tkinterdnd2` não estiver instalado, o programa continua funcionando com o botão "Adicionar vídeos…".

## Progresso
Cada vídeo tem sua própria barra de progresso com a porcentagem da conversão, além do status (Aguardando, Convertendo, Concluído, Falhou ou Cancelado). Use o ✕ de cada linha para removê-lo da lista.

## Qualidade
- Alta qualidade: CRF 18
- Padrão: CRF 23
- Arquivo menor: CRF 28

Os arquivos originais não são apagados. Se já existir um arquivo com o mesmo nome no destino, o programa cria outro nome em vez de sobrescrever.

# 🎬 Conversor de Vídeos para MP4

Aplicativo desktop para Windows desenvolvido em Python, com interface gráfica, que permite converter vários vídeos para o formato MP4 de maneira simples e organizada.

O programa utiliza o **FFmpeg** como mecanismo de conversão e oferece acompanhamento individual do progresso de cada arquivo, além de uma barra de progresso geral da fila.

---

## 📌 Sobre o projeto

O Conversor de Vídeos para MP4 foi desenvolvido para facilitar a conversão de arquivos de vídeo sem a necessidade de utilizar comandos no terminal.

Com uma interface intuitiva, o usuário pode adicionar diversos vídeos, selecionar uma pasta de destino, escolher a qualidade desejada e acompanhar cada conversão em tempo real.

O projeto foi desenvolvido em Python e é compatível com Windows 10 e Windows 11.

## ✨ Funcionalidades

- [x] Interface gráfica intuitiva.
- [x] Adicionar vários vídeos simultaneamente.
- [x] Adicionar uma pasta inteira com vídeos.
- [x] Arrastar e soltar arquivos na janela.
- [x] Conversão em lote para MP4.
- [x] Progresso individual de cada vídeo.
- [x] Barra de progresso geral da fila.
- [x] Escolha de qualidade de conversão.
- [x] Seleção da pasta de destino.
- [x] Cancelamento da conversão.
- [x] Proteção contra sobrescrita de arquivos existentes.
- [x] Possibilidade de gerar um executável `.exe`.

## 🎞️ Formatos suportados

O programa aceita arquivos com as seguintes extensões:

| Formato | Extensão |
|---|---|
| MPEG-4 | `.mp4` |
| Matroska | `.mkv` |
| AVI | `.avi` |
| QuickTime | `.mov` |
| Windows Media Video | `.wmv` |
| Flash Video | `.flv` |
| WebM | `.webm` |
| MPEG-4 Video | `.m4v` |
| MPEG | `.mpeg`, `.mpg` |
| 3GPP | `.3gp` |
| MPEG Transport Stream | `.ts`, `.mts`, `.m2ts` |

**Formato de saída:** MP4 com vídeo H.264 e áudio AAC.

## 🎚️ Opções de qualidade

O aplicativo oferece três configurações de qualidade:

| Opção | CRF | Característica |
|---|---:|---|
| Alta | 18 | Maior qualidade e arquivos geralmente maiores |
| Equilibrada | 23 | Equilíbrio entre qualidade e tamanho |
| Compacta | 28 | Arquivos geralmente menores |

O CRF controla a qualidade da codificação: quanto menor o valor, maior tende a ser a qualidade e o tamanho do arquivo.

## 🛠️ Tecnologias utilizadas

- **Python:** linguagem principal do projeto.
- **Tkinter:** criação da interface gráfica.
- **tkinterdnd2:** suporte a arrastar e soltar arquivos.
- **FFmpeg:** processamento e conversão dos vídeos.
- **FFprobe:** identificação da duração dos vídeos.
- **PyInstaller:** geração do executável para Windows.
- **Threading:** execução das conversões sem bloquear a interface.
- **Queue:** comunicação entre a conversão e a interface gráfica.

## 💻 Requisitos

Para executar o projeto a partir do código-fonte, você precisará de:

- Windows 10 ou Windows 11.
- Python 3.10 ou superior.
- FFmpeg e FFprobe instalados.
- Pip (gerenciador de pacotes do Python).

## 📥 Instalação

### 1. Baixar o projeto

Clone o repositório:

```bash
git clone https://github.com/SEU-USUARIO/Conversor-MP4.git
```

Entre na pasta:

```bash
cd Conversor-MP4
```

Ou baixe o projeto diretamente pelo botão **Code → Download ZIP** do GitHub.

### 2. Instalar o Python

Baixe o Python pelo site oficial:

https://www.python.org/downloads/windows/

Durante a instalação, marque a opção:

**Add Python to PATH**

### 3. Instalar o FFmpeg

O FFmpeg é responsável pela conversão dos vídeos.

Uma opção para Windows é:

https://www.gyan.dev/ffmpeg/builds/

Baixe uma compilação adequada, extraia os arquivos e adicione a pasta `bin` do FFmpeg às variáveis de ambiente do Windows (PATH).

A instalação deve disponibilizar os comandos:

```bash
ffmpeg -version
ffprobe -version
```

Se os dois comandos apresentarem informações de versão, a configuração está funcionando.

### 4. Instalar as dependências

Execute o arquivo:

```text
instalar_dependencias.bat
```

Ele instala as bibliotecas necessárias para o funcionamento do aplicativo e para a criação do executável.

### 5. Executar o programa

Execute:

```text
iniciar.bat
```

A interface gráfica será aberta.

## 🚀 Como utilizar

1. Abra o Conversor de Vídeos para MP4.
2. Clique em **Adicionar vídeos** ou **Adicionar pasta**.
3. Se preferir, arraste os vídeos para a janela.
4. Escolha a pasta onde os arquivos convertidos serão salvos.
5. Selecione a qualidade desejada.
6. Clique em **Iniciar conversão**.
7. Acompanhe o progresso individual e geral.

Ao terminar, os arquivos estarão disponíveis na pasta de destino.

## 📦 Criar um executável (.exe)

O projeto permite gerar um executável para facilitar a distribuição.

Execute:

```text
criar_exe.bat
```

O PyInstaller irá empacotar o aplicativo.

Após a conclusão, procure o arquivo:

```text
dist/ConversorMP4.exe
```

**Importante:** o executável gerado não inclui o FFmpeg. O computador que executar o programa ainda precisará ter o FFmpeg e o FFprobe instalados e disponíveis no PATH.

## 📁 Estrutura do projeto

```text
Conversor_MP4_Windows/
│
├── conversor_mp4.py
│
├── instalar_dependencias.bat
│
├── iniciar.bat
│
├── criar_exe.bat
│
└── README.md
```

| Arquivo | Descrição |
|---|---|
| `conversor_mp4.py` | Código-fonte principal |
| `instalar_dependencias.bat` | Instala as dependências |
| `iniciar.bat` | Inicia o aplicativo |
| `criar_exe.bat` | Gera o executável |
| `README.md` | Documentação do projeto |

## 🔒 Segurança e integridade dos arquivos

- Os vídeos originais não são modificados.
- Os arquivos convertidos são salvos na pasta de destino.
- O programa evita substituir arquivos existentes.
- Em caso de cancelamento, o arquivo de saída incompleto é removido.

Recomenda-se manter uma cópia de segurança dos arquivos importantes.

## ❓ Solução de problemas

### FFmpeg não encontrado

Verifique se a pasta `bin` do FFmpeg está adicionada ao PATH do Windows.

Feche e abra novamente o aplicativo após alterar as variáveis de ambiente.

### Arrastar e soltar não funciona

Execute novamente:

```text
instalar_dependencias.bat
```

Confira se a biblioteca `tkinterdnd2` foi instalada corretamente.

### A conversão apresenta erro

Verifique se:

- O arquivo de origem não está corrompido.
- Existe espaço disponível no disco.
- O FFmpeg está instalado corretamente.
- O arquivo não está sendo utilizado por outro programa.

### O executável não abre

Verifique se o FFmpeg está instalado e disponível no PATH. O `.exe` não contém o mecanismo de conversão.

## 🗺️ Melhorias futuras

Possíveis evoluções para as próximas versões:

- [ ] Tema escuro.
- [ ] Pré-visualização dos vídeos.
- [ ] Exibição do tamanho estimado e final dos arquivos.
- [ ] Estimativa do tempo restante.
- [ ] Configurações avançadas de vídeo e áudio.
- [ ] Escolha de resolução.
- [ ] Conversão de áudio para MP3 e outros formatos.
- [ ] Histórico de conversões.
- [ ] Empacotamento do FFmpeg junto ao instalador, respeitando sua licença.
- [ ] Instalador profissional para Windows.

## 🤝 Contribuição

Contribuições são bem-vindas!

Se você encontrou um problema, tem uma sugestão ou deseja melhorar o projeto:

1. Faça um Fork do repositório.
2. Crie uma branch para sua alteração.
3. Faça as modificações.
4. Envie um Pull Request.

Você também pode abrir uma Issue para relatar problemas ou sugerir funcionalidades.

## 📄 Licença

Este projeto ainda não possui uma licença definida.

Antes de publicar uma licença, escolha os termos de distribuição e verifique as condições aplicáveis às dependências utilizadas, especialmente FFmpeg e tkinterdnd2.

---

**Desenvolvido com Python e FFmpeg.** 🎬

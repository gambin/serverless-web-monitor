# pt-br

# λ serverless-web-monitor

Essa solução foi inspirada em https://github.com/vittorio-nardone/selenium-chromium-lambda

Que foi inspirada em https://github.com/jairovadillo/pychromeless

Que por sua vez é uma implementação de https://github.com/adieuadieu/serverless-chrome/ 

Ou seja - ninguém inventou a roda por aqui.


Acontece que qualquer implementação de testes com selenium é um pouco chata na definição de versão de drivers (chromedriver que o diga), browser (chrome que o diga), selenium driver, plataforma, timeouts/ timewaits/ timesleeps, e todo aquilo universo que a gente já sabe. E para quem usa muito esporadicamente (não tem ninguém de QA e afins por aqui), criar um teste do 0 ou ficar reciclando testes existentes é um pouco chato.

Para acabar (ou minimizar) essa dor de cabeça com uma possibilidade de automação + redução de custos top (serverless, my friend), criei esse carinha aqui.

Ele nasceu como um projeto console dotnet core que iria rodar em docker, mas ao ver a possibilidade de rodar em uma ambiente serverless com o uso de navegadores ja buildados compativeis com lambda (serverless chrome), e alguns modelos já prontos resolvi me aventurar em Python.

Sim, este é a primeira coisa que faço em Python e as implementações e desenvolvimento envolveram muitas vozes da minha cabeça e umas consultas no stackoverflow.

Criei um teste específico para um ambiente que deveria rodar nos próximos meses, mas aproveitei para deixar este código o mais genérico possível. Espero que aproveitem (ou reclamem, critiquem, e COMITEM melhorias se aplicáveis - que são várias rs)!


### Mas afinal, o que faz?

A solução basicamente compreende o seguinte cenário:

    - Implementar um lambda na AWS que execute testes agendados ou por demanda (crontab/ api gateway request/ manual/ whatever);
    - Fazer com que este lambda leia um roteiro (arquivo texto mesmo) como se fosse um roteiro de teste. Ex.:
        Acessar "www.meusite.com.br"
        Preencher "#seletor-input" com "valor do campo"
        Clicar ".seletor-botao"
    - Se ele chegar até a última etapa sem qualquer tipo de exception, sucesso!
    - Se der qualquer exception, registra num log file formato JSON no S3, assim como print que evidencia o erro;
    - Em caso de sucesso, loga resultado, html output e print de tela no S3
    - É um pseudo Cucumber/ Pingdom alike



### Requisitos

Esse cara roda em docker, mas foi feito pra AWS Lambda. Choose your path, padawan.
Para rodar em docker e buildar o pacote para Lambda voce irá precisar de:

* [Python 3.6] (https://wiki.python.org/moin/BeginnersGuide/Download)
* [Docker](https://docs.docker.com/engine/installation/#get-started)
* [Docker compose](https://docs.docker.com/compose/install/#install-compose)


Eventualmente teremos outros itens que serão instalados automaticamente, como:
* Boto3
* Logger
* [Chrome driver](https://sites.google.com/a/chromium.org/chromedriver/)
* [Chromium binary](https://github.com/adieuadieu/serverless-chrome/releases)


Obs.: todos os testes realizados em ambiente Linux. Consigo fazer o setup e build no Windows/ WSL? Provável, mas o tio aqui não teve saco pra testar ainda.


### Primeiros passos

Preparando a AWS:
    - Ainda não tem terraform, mas vai ter =)
    - Por hora crie um bucket e batize-o como desejar
    - Neste bucket crie a seguinte estrutura de pastas:
        - /tests
        - /results
        - /screenshots
    - Crie um novo lambda, contemplando:
        - Policy de leitura e escrita no S3
        - Runtime python 3.6
        - RAM 500Mb (isso pode variar com seu uso, é só uma sugestão)
        - Tempo de execução de 2 min (isso pode variar com seu uso, é só uma sugestão)
    - Faça o upload do arquivo "template.w3swm" para a pasta "/tests" que foi criada previamente no novo bucket

Preparando o pacote:
    - Clone o repositório localmente
    - Defina o nome do bucket no arquivo "docker-compose.yml"
    - Execute os comandos nessa ordem:
        `make clean fetch-dependencies` limpa qualquer possível sujeira e baixa as dependencias
        `sudo make docker-build` ja prepara sua imagem docker, quase lá

Trabalhando local (docker)
    - É preciso antes definir as chaves do docker-compose, via arquivo aws credentials e etc. Se voce estiver sem muita paciencia, dá pra mudar o makefile (linha 35) de modo que ele fica igual o modelo abaixo (meio go-horse, mas funciona), mandando variável de ambiente pro docker-compose:
        `docker-compose run -e AWS_ACCESS_KEY_ID=<AQUI-VAI-MINHA-KEY> -e AWS_SECRET_ACCESS_KEY=<AQUI-VAI-MEU-SECRET> lambda src.lambda_function.lambda_handler`
    - Obviamente que voce não precisa disso no contexto do lambda.
    - Para executar no seu docker
        `sudo make docker-run` executa seu docker com um teste pré-definido, o "template.w3swm"
    -Se estiver tudo bem, verifique em seu bucket na pasta "/results" e "/screenshots" se foi carregada a página abaixo com sucesso!

Gerando o pacote AWS Lambda:
    - `make build-lambda-package` gera o arquivo "build.zip", que voce deverá subir para um bucket de sua preferencia e referenciar como código fonte em seu lambda

Executando o lambda:
    - Defina as variáveis de ambiente para o lambda conforme já definidas previamente no "docket-compose.yml"
    - Crie um novo evento de teste, e informe o argumento conforme modelo abaixo:

    {
        "test_to_run": "meu-teste.w3swm"
    }
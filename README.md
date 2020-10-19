# λ Serverless Web Monitor (Lambda Edition)

## pt-br

Essa solução foi inspirada em https://github.com/vittorio-nardone/selenium-chromium-lambda

Que foi inspirada em https://github.com/jairovadillo/pychromeless

Que por sua vez é uma implementação de https://github.com/adieuadieu/serverless-chrome/ 

Ou seja - ninguém inventou a roda por aqui.


Acontece que qualquer implementação de testes com selenium é um pouco chata na definição de versão de drivers (chromedriver que o diga), browser (chrome que o diga), selenium driver, plataforma, timeouts/ timewaits/ timesleeps, e todo aquele universo que a gente já sabe. E para quem usa muito esporadicamente (não tem ninguém de QA e afins por aqui), criar um teste do 0 ou ficar reciclando testes existentes é um pouco chato.

Para acabar (ou minimizar) essa dor de cabeça com uma possibilidade de automação + redução de custos top (serverless, my friend), criei esse carinha aqui.

Ele nasceu como um projeto console dotnet core que iria rodar em docker, mas ao ver a possibilidade de rodar em uma ambiente serverless com o uso de navegadores ja buildados compativeis com lambda (serverless chrome), e alguns modelos já prontos resolvi me aventurar em Python.

Sim, este é a primeira coisa que faço em Python e as implementações e desenvolvimento envolveram muitas vozes da minha cabeça e umas consultas no stackoverflow. Não necessariamente nesta ordem ou intensidade.

Neste contexto criei um código específico para um ambiente que deveria rodar nos próximos meses, mas aproveitei para deixá-lo o mais genérico possível. Espero que aproveitem (ou reclamem, critiquem, e COMITEM melhorias se aplicáveis - que são várias rs)!


### Mas afinal, o que faz?

A solução basicamente compreende o seguinte cenário:

- Implementar um lambda na AWS que execute testes agendados ou por demanda (crontab/ api gateway request/ manual/ whatever);
- Fazer com que este lambda leia um roteiro (arquivo texto mesmo) como se fosse um roteiro de teste. Ex.:
    - Acessar **"https://www.meusite.com.br"**
    - Preencher **"#seletor-input"** com **"valor do campo"**
    - Clicar **".seletor-botao"**
- Se ele chegar até a última etapa sem qualquer tipo de exception, sucesso!
- Se der qualquer exception, registra num log file formato JSON no S3, assim como print que evidencia o erro;
- Em caso de sucesso, loga resultado, html output e print de tela no S3
> **Resumo:** É um pseudo Cucumber/ Pingdom (transaction test) alike


### Vantagens

- Fácil implementação;
- Reutilização de código para diferentes roteiros, através de um único lamda/ docker;
- Captura de screenshot, html output, gravação de resultado do roteiro em formato JSON (sim, já foi pensado para a criação de uma API de consulta!);
- Criação de roteiros baseados em arquivos texto (com extensão exótica), não necessitando de novos deployments;
- Não há necessidade de conhecimento técnico para criação de novos testes (apenas de seletor CSS, seu browser ajuda vai);
- Se você não pretende usar um cenário on-premises, é um forte candidato a solução com menor custo possível para o que se propõe;


### Requisitos

Esse cara roda em docker, mas foi feito pra AWS Lambda. Choose your path, padawan.
Para rodar em docker e buildar o pacote para Lambda você irá precisar de:

* [Python 3.6](https://wiki.python.org/moin/BeginnersGuide/Download)
* [Docker](https://docs.docker.com/engine/installation/#get-started)
* [Docker compose](https://docs.docker.com/compose/install/#install-compose)


Eventualmente teremos outros itens que serão instalados automaticamente, como:
* Boto3
* Logger
* [Chrome driver](https://sites.google.com/a/chromium.org/chromedriver/)
* [Chromium binary](https://github.com/adieuadieu/serverless-chrome/releases)


> **Obs.:** todos os testes realizados em ambiente Linux. Consigo fazer o setup e build no Windows/ WSL? Provável, mas o tio aqui não teve saco pra testar ainda.


### Primeiros passos


**Preparando a AWS**
- Ainda não tem terraform, mas vai ter =)
- Por hora crie um bucket e batize-o como desejar
- Neste bucket crie a seguinte estrutura de pastas:
    - **/tests**
    - **/results**
    - **/screenshots**
- Crie um novo lambda, contemplando:
    - Policy de leitura e escrita no S3
    - Runtime Python 3.6
    - RAM 1024Mb (isso pode variar com seu uso, é só uma sugestão)
    - Tempo de execução de 2 min (isso pode variar com seu uso, é só uma sugestão)
- Faça o upload do arquivo **"template.w3swm"** para a pasta **"/tests"** que foi criada previamente no novo bucket


**Preparando o pacote**
- Clone o repositório localmente
- Defina o nome do bucket no arquivo **"docker-compose.yml"**
- Execute os comandos nessa ordem:
```sh
$ make clean fetch-dependencies
$ sudo make docker-build
```


**Trabalhando local (docker)**
- É preciso antes definir as chaves do docker-compose, via arquivo aws credentials e etc. Se você estiver sem muita paciência, dá pra mudar o makefile (linha 35) de modo que ele fica igual o modelo abaixo (meio go-horse, mas funciona), mandando variável de ambiente pro docker-compose:
```sh
docker-compose run -e AWS_ACCESS_KEY_ID=<AQUI-VAI-MINHA-KEY> -e AWS_SECRET_ACCESS_KEY=<AQUI-VAI-MEU-SECRET> lambda src.lambda_function.lambda_handler
```
- Obviamente que você não precisa disso no contexto do lambda.
- Para executar no seu docker
```sh
$ sudo make docker-run
```
> **Se estiver tudo bem** verifique em seu bucket na pasta **"/results"** e **"/screenshots"** se foi carregada a página abaixo com sucesso!

Gerando o pacote AWS Lambda:
- O comando abaixo gera o arquivo **"build.zip"**, que você deverá subir para um bucket de sua preferencia e referenciar como código fonte em seu lambda
```sh
$ make build-lambda-package
```
  

**Executando o lambda**
- Defina as variáveis de ambiente para o lambda conforme já definidas previamente no **"docket-compose.yml"**
- Crie um novo evento de teste, e informe o argumento conforme modelo abaixo:
```sh
{
    "test_to_run": "template.w3swm"
}
```
> **Se estiver tudo bem**, verifique em seu bucket na pasta **"/results"** e **"/screenshots"** se foi carregada a página abaixo com sucesso!


### Criando novos roteiros

Os roteiros basicamente seguem uma estrutura baseada em verbos, como descrito no modelo **"template.w3swm"**, mas que podem ser listados como:

- Comandos de parâmetro unico:
    - **Esperar** (to wait): implementa um timesleep no valor informado em seguida. Tempo em segundos.
    - **Evitar** (to avoid): evitar à partir do momento em que foi declarado, qualquer **NOVO** elemento que possa surgir (temporariamente) sob o elemento desejado, por exemplo um modal de "loading". A intenção é que ele seja usado para requisições AJAX onde um pequeno delay possa impactar a pesquisa ou interação com o elemento desejado. Também é muito útil para postbacks e ações cliente side, como onclick, onchage, onblur, etc. O tempo de espera é definido pela variável de ambiente *"TIME_WAIT"*.
    - **Acessar** (to get): o clássico GET URL! Apenas informe a URL desejada e voilà. Um ponto interessante é que ele pode ser usado por exemplo para fazer processos de single sign on, por exemplo, voce acessa uma URL de autenticação e os cookies/ localstorage/ whatever são atualizados, portanto se voce quiser navegar em um outro site e reutilizar esse dados locais, tudo bem, uma vez que eles permanecem na sessão do navegador em execução.]
    - **Clicar** (to click): pode ser um button, um radio button, tanto faz;
    - **Ignorar** (to ignore): será implementado ainda rs
    - **Pressionar** (to press): pressionar alguma tecla no teclado considerando o foco no último elemento que teve interação. Por hora só suporta **"ENTER"** e **"TAB"**.
    
- Comandos de parâmetro duplo (nem sempre):
    - **Preencher** (to fill): use para preencher um input text. Se for informado o sufixo "com delay", será utilizad um time.sleep baseado na variável de ambiente *"TIME_SLEEP"*
    - **Selecionar** (to select): use para preencher dropdowns. O valor informado no preenchimento deve ser o valor exibido, e não o "value" do option.
    
- Exemplos
```sh
    Evitar ".classe-modal-loading"
    Acessar "https://www.meusite.com.br"
    Esperar 5
    Pressionar "TAB"
    Clicar "#button-submit"
    Preencher ".seletor-usuario" com "nome-do-usuario@dominio.com"
    Preencher ".seletor-senha" com "senha-secreta" com delay
    Selecionar ".dropdown-campo" com "Segunda opção"
```

### Configurações variáveis de ambiente

Basicamente as unicas variáveis de ambiente que você precisa se preocupar são:

- **BUCKET**: nome do bucket que armazenará resultados, screenshots e roteiros de teste
- **TIME_WAIT**: tempo implicito (em segundos) que um elemento poderá ser localizado na página
- **TIME_SLEEP**: tempo de espera (delay) para ser implementado quando desejado

# λ Serverless Web Monitor (Lambda Edition)

[![](https://icons.iconarchive.com/icons/designbolts/world-cup-2014-teams/48/Brazil-Flag-icon.png)](https://github.com/gambin/serverless-web-monitor/blob/main/README.md#pt-br)
[![](https://icons.iconarchive.com/icons/designbolts/world-cup-2014-teams/48/USA-Flag-icon.png)](https://github.com/gambin/serverless-web-monitor/blob/main/README.md#en-us)

Source: https://www.iconarchive.com/show/world-cup-2014-teams-icons-by-designbolts.html


## pt-br

Essa solução foi inspirada em https://github.com/vittorio-nardone/selenium-chromium-lambda

Que foi inspirada em https://github.com/jairovadillo/pychromeless

Que por sua vez é uma implementação de https://github.com/adieuadieu/serverless-chrome/ 

Ou seja - ninguém inventou a roda por aqui.


Acontece que qualquer implementação de roteiros de teste com selenium é um pouco chato na definição de versão de drivers (chromedriver que o diga), browser (chrome/ chromium que o diga), selenium driver, plataforma, timeouts/ timewaits/ timesleeps, e todo aquele universo que a gente já sabe. E para quem usa muito esporadicamente (não tem ninguém de QA e afins por aqui), criar um do zero ou ficar reciclando roteiros de testes existentes é um pouco chato.

Para acabar (ou minimizar) essa dor de cabeça com uma possibilidade de automação + redução de custos top (serverless, my friend), criei esse carinha aqui.

Ele nasceu como um projeto console dotnet core que iria rodar em docker, mas ao ver a possibilidade de rodar em uma ambiente serverless com o uso de navegadores ja buildados compativeis com lambda (serverless chrome), e alguns modelos já prontos resolvi me aventurar em Python.

Sim, este é a primeira coisa que faço em Python e as implementações e desenvolvimento envolveram muitas vozes da minha cabeça e umas consultas no stackoverflow. Não necessariamente nesta ordem ou intensidade.

Neste contexto criei um código específico para um ambiente que deveria rodar nos próximos meses, mas aproveitei para deixá-lo o mais genérico possível. Espero que aproveitem (ou reclamem, critiquem, e COMITEM melhorias se aplicáveis - que são várias rs)!


### Mas afinal, o que faz?

A solução basicamente compreende o seguinte cenário:

- Implementar um lambda na AWS que execute roteiros de testes agendados ou por demanda (crontab/ api gateway request/ manual/ whatever);
- Fazer com que este lambda leia um roteiro (arquivo texto mesmo) como se fosse um roteiro de teste. Ex.:
```sh
    Acessar "https://www.meusite.com.br"
    Preencher "#seletor-input" com "valor do campo"
    Clicar ".seletor-botao"
````
- Se ele chegar até a última etapa sem qualquer tipo de exception, sucesso! Grava resultado, html output e screenshot em um bucket no S3
- Se der qualquer exception, registra num log file formato JSON no S3, assim como screenshot que evidencia o erro;
> **Resumo:** É um pseudo Cucumber/ Pingdom (transaction test) alike


### Vantagens

- Fácil implementação;
- Reutilização de código para diferentes roteiros, através de um único lamda/ docker;
- Captura de screenshot, html output, gravação de resultado do roteiro em formato JSON (sim, já foi pensado para a criação de uma API de consulta!);
- Criação de roteiros baseados em arquivos texto (com extensão exótica), sem necessidade de novos deployments ou alteração de fonte;
- Não há necessidade de conhecimento técnico para criação de novos roteiros (apenas de seletor CSS, seu browser ajuda vai);
- Se você não pretende usar um cenário on-premises já disponível, é um forte candidato a solução com menor custo possível para o que se propõe;

### Screenshots

![](http://tarcisiogambin.net/wp-content/uploads/sites/2/2020/10/s3_folders.png)

![](http://tarcisiogambin.net/wp-content/uploads/sites/2/2020/10/code-roteiro.png)

![](http://tarcisiogambin.net/wp-content/uploads/sites/2/2020/10/screenshot_lambda.png)

![](http://tarcisiogambin.net/wp-content/uploads/sites/2/2020/10/screenshot_02.png)

![](http://tarcisiogambin.net/wp-content/uploads/sites/2/2020/10/template.w3swm.2020-10-16_22-36-55.png)


### Quero usar agora!

Baixe agora mesmo o pack com pacote pronto para subir no seu AWS Lambda na página de releases: https://github.com/gambin/serverless-web-monitor/releases



### Requisitos

Esse cara roda em docker, mas foi feito pra AWS Lambda. Choose your path, padawan.
Para rodar em docker e buildar o pacote para Lambda você irá precisar de:

* [Python 3.7](https://wiki.python.org/moin/BeginnersGuide/Download)
* [Docker](https://docs.docker.com/engine/installation/#get-started)
* [Docker compose](https://docs.docker.com/compose/install/#install-compose)


Eventualmente teremos outros itens que serão instalados automaticamente, como:
* Boto3
* Logger
* [Chrome driver](https://sites.google.com/a/chromium.org/chromedriver/)
* [Chromium binary](https://github.com/adieuadieu/serverless-chrome/releases)


> **Obs.:** toda a implementação foi realizada em ambiente Linux. Consigo fazer o setup e build no Windows/ WSL? Dá sim!! Agora o tio arrumou um tempo e fez alguns testes :)

![](http://tarcisiogambin.net/wp-content/uploads/sites/2/2020/11/WSL-01.png)

![](http://tarcisiogambin.net/wp-content/uploads/sites/2/2020/11/WSL-02.png)



A única diferença é que o setup no WSL é mais sacal. Eu fiz um teste usando o Ubuntu no WSL2, e nele voce precisa instalar alguns componentes no SO, pois a build/ imagem do Ubuntu na MS Store vem muito mais pelada que um Ubuntu "tradicional". Seguem alguns pacotes quase que nativos mas precisei instalar no braço:

```sh
$ sudo apt install python3-pip unzip make curl apt-transport-https ca-certificates software-properties-common python3.7 python3.6 virtualenvwrapper python3-virtualenv zip
```

E claro, não podia faltar os 'cat jumps' né? A instalação do Docker não é tão easy mode no WSL como uma build Ubuntu tradicional, mas bem..

Eu comecei neste step by step: https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-20-04

Mas terminei neste aqui (**recomendo fortemente**): https://docs.docker.com/docker-for-windows/wsl/



### Primeiros passos


**Preparando a AWS**
>**Ainda não tem terraform**, mas vai ter =)
- Por hora crie um bucket e batize-o como desejar
- Neste bucket crie a seguinte estrutura de pastas:
    - **/tests**
    - **/results**
    - **/screenshots**
- Crie um novo lambda, contemplando:
    - Policy de leitura e escrita no S3
    - Runtime Python 3.7
    - RAM 1500Mb (recomendado, lembre-se que estamos usando um Chrome)
    - Tempo de execução de 2 min (isso pode variar com seu uso, é só uma sugestão)
- Faça o upload do arquivo **"template.w3swm"** para a pasta **"/tests"** que foi criada previamente no novo bucket


**Preparando o pacote**
- Clone o repositório localmente
- Defina o nome do bucket no arquivo **"docker-compose.yml"**
- Execute os comandos nessa ordem:
```sh
$ make clean fetch-dependencies
$ make docker-build
```


**Trabalhando local (docker)**
- Faça o setup do (AWS credentials)[https://docs.aws.amazon.com/sdk-for-java/v1/developer-guide/setup-credentials.html], o docker-compose.yml já está preparado pra isso meu caro. Neste mesmo arquivo voce pode alterar region e profile do AWS Credentials. Obviamente que você não precisa disso executando no contexto do Lambda, lá voce deve se preocupar com as Policies.
- Para executar no seu docker
```sh
$ make docker-run
```
> **Se estiver tudo bem** verifique em seu bucket na pasta **"/results"** e **"/screenshots"** se foi carregada a página abaixo com sucesso!


**Gerando o pacote AWS Lambda:**
- Certifique-se de rodar uma versão do Python compatível com o build dos pacotes. Da última versão que testei, python3.7 rodou 100%, para isso recomendo que você utilize um virtual environment:

```sh
$ virtualenv -p /usr/bin/python3.7 venv
$ source ./venv/bin/activate
```

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
- **LOG_LEVEL**: pode ser INFO ou ERROR. Autoexplicativo.

---

## en-us

This solution was inspired by https://github.com/vittorio-nardone/selenium-chromium-lambda

That was inspired by https://github.com/jairovadillo/pychromeless

That's an implementaion of https://github.com/adieuadieu/serverless-chrome/ 

In other words - nobody invented the wheel here!


Some of you may notice that implementing test scripts with selenium isn't so simple when you start to code it from sratch, specifically if you aren't a tester or just need to code some automation to run twice a year. We must care about chromedriver version, chrome browser version, selenium driver versions, platform (OS, language, many variables here..), how to handle timeouts/ timewaits/ timesleeps. So boring.

I know, i know.. there's pytest, some browser extensions that may help you to prepare or create a base version of your test. But how can you automate that? Of if you want to run the same test every single minute to stress or check your web application health?

Even more - if you want to have a kind of 'engine' that you may only upload and schedule test scripts to run periodically, and upload the tests result with the screenshot to an AWS Bucket, and using the Cloudwatch to notify you when some of your test fail?

That would be great hm?

So this project was born following those guidelines, trying to be the most cost killer solution to run scheduled web tests - since it's going to be able to run on AWS Lambda, that costs CENTS by MILLIONS of executions.

I started to built it on .Net Core to run on Docker, but since I meet the projects mentioned earlier, it becames a good opportunity to learn something new (Python, in this case), and since I never wrote any single line in Python I started to follow some voices on my head and copy/ pasting some parts of Stackoverflow. Not in this order or intensity.

So it was tailored to run an specific test, then it was refactored to be the more generic as possible. Please enjoy, ask, find bugs (and report them!), and if you can, commit and help me evolve this! There's a bunch to do :)



### What EXACTLY it does?

This solution comprehends the following scenario:

- Implements a AWS Lambda that runs tests scripts to run scheduled or on-demand (AWS Cloudwatch Rules [crontab alike], manual, whatever);
- When invocated, this lambda reads a script (text file wroted in pt-br, I'm working to support en-us, please don't bite me) like a test script. Example:
```sh
    Acessar "https://www.mydomain.com"
    Preencher "#choose-your-css2-selector" com "heres my field value bro!"
    Clicar ".my-custom-submit-button"
````
- If there's no exception (timeout, element not available, any kind of) so it's done! If you want you may write the result output and the screenshot in a AWS Bucket;
- If there's any exception, it'll write the result and the screenshot in a AWS Bucket;
> **Summary:** It's a Cucumber/ Pingdom (transaction test) alike


### Advantages

- Easy deployment;
- Code/ solution/ infrastructure reuse for many test scripts you want to run, no need to touch any single of code;
- Screenshot save, html output save, writing results in a JSON format, you may want to implement a API to status check at the future :)
- Easy to create new test scripts, no coding needed;
- Also not required web developemnt skills to create the test script (I'm sure your browser can do the hard work for you);
- If you don't have servers or containters, it's probably the cheapest solution you may have to address this need running it on serverless infrastructure;


### Screenshots

![](http://tarcisiogambin.net/wp-content/uploads/sites/2/2020/10/s3_folders.png)

![](http://tarcisiogambin.net/wp-content/uploads/sites/2/2020/10/code-roteiro.png)

![](http://tarcisiogambin.net/wp-content/uploads/sites/2/2020/10/screenshot_lambda.png)

![](http://tarcisiogambin.net/wp-content/uploads/sites/2/2020/10/screenshot_02.png)

![](http://tarcisiogambin.net/wp-content/uploads/sites/2/2020/10/template.w3swm.2020-10-16_22-36-55.png)


### Want to use it now!

Please download one of our releases to run RIGHT NOW on your AWS Lambda: https://github.com/gambin/serverless-web-monitor/releases


### Requirements

It runs on docker, but it's made to run on AWS Lambda. Choose your path, padawan.
To run on docker and build it to run on Lambda you'll need:

* [Python 3.7](https://wiki.python.org/moin/BeginnersGuide/Download)
* [Docker](https://docs.docker.com/engine/installation/#get-started)
* [Docker compose](https://docs.docker.com/compose/install/#install-compose)


Eventually there are other stuff that'll be installed automatically, like:
* Boto3
* Logger
* [Chrome driver](https://sites.google.com/a/chromium.org/chromedriver/)
* [Chromium binary](https://github.com/adieuadieu/serverless-chrome/releases)


> **Notes:** all of this was built on Linux. Can I use Windows/ WSL? Absolutely!! 

![](http://tarcisiogambin.net/wp-content/uploads/sites/2/2020/11/WSL-01.png)

![](http://tarcisiogambin.net/wp-content/uploads/sites/2/2020/11/WSL-02.png)


The only difference is that setting the Linux image on WSL requires more steps. When doing that, you must install more components, libs, etc because the Ubuntu from MS Store comes lighter. Some of them I need to install before doing the next steps (only when on WSL):

```sh
$ sudo apt install python3-pip unzip make curl apt-transport-https ca-certificates software-properties-common python3.7 python3.6 virtualenvwrapper python3-virtualenv zip
```

Still want to run on WSL? Some workaround required!


So please read those before:

I've started on this: https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-20-04

And finished there (**strongly recommended**): https://docs.docker.com/docker-for-windows/wsl/


### First steps

**Preparing the AWS**
>**There's no terraform script**, yet =)
- Create a brand new bucket and put the name you want
- Under this bucket, create the following folders:
    - **/tests**
    - **/results**
    - **/screenshots**
- Create a brand new lambda, using the configuration as follows:
    - Read and write policy on S3
    - Python runtime 3.7
    - RAM 1500Mb (recommended, we are using Chromium, you know..)
    - Execution time 2 min (just a recommendation, you may adjust as you need to)
- Upload the file **"template.w3swm"** to the folder **"/tests"** you've created previously

**Preparing the package**
- Clone the repository locally
- Define the bucket on **"docker-compose.yml"** file
- Run this:
```sh
$ make clean fetch-dependencies
$ make docker-build
```

**Working local (docker)**
- Do your (AWS credentials)[https://docs.aws.amazon.com/sdk-for-java/v1/developer-guide/setup-credentials.html] setup, the docker-compose.yml file is already prepared for this. Obviously you don't need to care about it on lambda context.
- To run your docker
```sh
$ make docker-run
```
> **If everything runs smoothly AND you enable INFO logs on EV** check your **"/results"** and **"/screenshots"** folder on S3!


**Generate your AWS Lambda package**
- Make sure to run a Python version compatible. The last time I did it Python 3.7 were fully compatible, so I just recommend you to run it on a virtual environment.

```sh
$ virtualenv -p /usr/bin/python3.7 venv
$ source ./venv/bin/activate
```

- The following command generates the **"build.zip"** file that you must upload on an S3 you prefer and point to it on your AWS Lambda:
```sh
$ make build-lambda-package
```


**Running it on AWS Lambda**
- Define the EV to the lambda accordingly to the ones already defined on **"docket-compose.yml"**
- On your lambda create a new test event (AWS Console top right menu), and pass some arguments like:
```sh
{
    "test_to_run": "template.w3swm"
}
```
> **If everything runs smoothly AND you enable INFO logs on EV** check your **"/results"** and **"/screenshots"** folder on S3!


### Creating new test scripts

The script are based on verbs, as described on the model **"template.w3swm"**, but you may understand it like:

- Single parameters statements:
    - **Esperar** (to wait): implements a timesleep according to the value (int) informed next to it. Time in seconds.
    - **Evitar** (to avoid): since declared it must avoid any **NEW** element that may sunrise in front your screen temporaly, like a loading modal. It's intended to be used when you have some transition elements, or animation, or any AJAX or delay that may improperly break the interation with the next element on script. It's also a good option for client side events, like onclick, onchange, onblur, etc. The waitint time to avoid is defined by the *"TIME_WAIT"* EV.
    - **Acessar** (to get): the classic GET URL! Just type the URL you want and voilà. There's something interesting here that you may want to use it like a "fake SSO" - for example - you just want to access some protected page that you must send a auth cookie, session info, localstorage, anything that sits on client side. So if you goes to the login page, do login and then access the URL want it's going to work normally, because all the session runs at the same context, like a native browser interaction! You don't need to handle headers, cookies, any sort of that. Just browse, my friend!
    - **Clicar** (to click): may be a button, radio button, anything clickabled.
    - **Pressionar** (to press): simulates to press a key considering the last element you interacted with. For now just supports **"ENTER"** and **"TAB"**. I really need to improve this.

- Double parameters statements:
    - **Preencher** (to fill): use it to fill up an input text. If you add a "com delay" at the end of statement, you're adding a timesleep accordingly to the EV *"TIME_SLEEP"*
    - **Selecionar** (to select): must use to fill dropdowns. Important: you must set the display value, not the internal value.
    
- Examples
```sh
    Evitar ".classe-modal-loading"
    Acessar "https://www.meusite.com"
    Esperar 5
    Pressionar "TAB"
    Clicar "#button-submit"
    Preencher ".user-inpunt" com "username@domain.com"
    Preencher ".user-password" com "my-secret-pass_123" com delay
    Selecionar ".dropdown-field" com "I really liked this project!"
```


### Setting up EV

Basicaly those are the unique EV you must care about:

- **BUCKET**: name of the AWS bucket that will store test scripts, screenshots and results
- **TIME_WAIT**: implicit time wait (in seconds) that an element must be located at the current page
- **TIME_SLEEP**: delay time to be implemented anytime you want
- **LOG_LEVEL**: INFO or ERROR. Self explanatory.
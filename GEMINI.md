Projeto Python + Kivy para Android.

Objetivo:

- preservar comportamento atual
- reduzir acoplamento
- evitar duplicação

Compatibilidade obrigatória:

- Android
- Kivy
- Buildozer

Nunca:

- inventar APIs
- inventar arquivos inexistentes
- inventar atributos inexistentes
- assumir contexto não fornecido

Refatoração:

- preferir extração de métodos antes de criar classes
- preferir composição antes de herança
- preservar nomes públicos utilizados por outros módulos
- minimizar alterações em arquivos estáveis

Nomenclatura:

- utilizar português para novos métodos
- utilizar português para novas classes
- utilizar português para novas variáveis

Antes de alterar código:

- identificar dependências
- identificar riscos
- identificar efeitos colaterais

Antes de criar um novo arquivo:

- verificar se existe uma classe já responsável pelo domínio
- preferir mover lógica para arquivos existentes quando houver aderência de responsabilidade
- criar novos arquivos apenas quando não existir um local adequado no projeto

Exemplos:

- lógica de Spotify deve preferencialmente ficar em SpotifyManager
- lógica de voz deve preferencialmente ficar em módulos de voz
- lógica de animações deve preferencialmente ficar em módulos de animação
- lógica de cenário deve preferencialmente ficar em módulos de cenário